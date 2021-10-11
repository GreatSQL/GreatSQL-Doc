# Use GreatSQL to deploy the MGR cluster, add new nodes, rolling upgrades, and switching to PRIMARY

This article describes in detail how to use GreatSQL to build a 3-node MGR cluster in same host and manage it with mysqld_multi.

For the sake of simplicity, this MGR cluster uses a single-primary mode instead of a multi-primary mode.

After constructing the MGR cluster, add a new node and simulate other operations such as rolling upgrades and switching masters.

In addition to the official MySQL community server, if you want to experience a more reliable, stable, and efficient MGR, the GreatSQL is recommended. This article uses GreatSQL version 8.0.25. For details on this version, please refer to [GreatSQL, Build a Better MGR Ecosystem](https://mp.weixin.qq.com/s/ByAjPOwHIwEPFtwC5jA28Q).

PS, if you want to deploy multiple instances and build an MGR cluster in same host, you must pay attention to avoid TCP self-connect problems, see [bug#98151](https://bugs.mysql.com/bug.php?id= 98151), if you use the GreatSQL version, there will be no such problem.

### 1. About the running environment

The GreatSQL binary package is placed under /usr/local/, that is, `basedir = /usr/local/GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64`.

The three instances are allocated according to the following plan:

| Example | Port | datadir |
|--- | --- | ---
| GreatSQL-01 | 3306 | /data/GreatSQL/mgr01/
| GreatSQL-02 | 3307 | /data/GreatSQL/mgr02/
| GreatSQL-03 | 3308 | /data/GreatSQL/mgr03/

![Enter picture description](https://images.gitee.com/uploads/images/2021/0623/171734_e00636c7_8779455.png "Screenshot.png")


### 2. Edit my.cnf 
```
[mysqld]
basedir=/usr/local/GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64
log_timestamps=SYSTEM
user = mysql
log_error_verbosity = 3

log-bin=binlog
binlog-format=row
log_slave_updates=ON
binlog_checksum=CRC32

master-info-repository=TABLE
relay-log-info-repository=TABLE
gtid-mode=on
enforce-gtid-consistency=true
binlog_transaction_dependency_tracking=writeset
transaction_write_set_extraction=XXHASH64
slave_parallel_type = LOGICAL_CLOCK
slave_parallel_workers=128 #Can be set to 2-4 times the number of logical CPUs
sql_require_primary_key=1
slave_preserve_commit_order=1
slave_checkpoint_period=2

#mgr
loose-plugin_load_add='mysql_clone.so'
loose-plugin_load_add='group_replication.so'

#The group_replication_group_name value of all nodes must be the same
#This is a standard UUID format, which can be specified manually or a randomly generated UUID
loose-group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"

#Specify the IP+port of each node in the MGR cluster, this port is dedicated to MGR, not the usual mysqld instance port
#If you are deploying an MGR cluster on multiple nodes, pay attention to whether this port will be blocked by the firewall
loose-group_replication_group_seeds= "127.0.0.1:33061,127.0.0.1:33071,127.0.0.1:33081"

#It is not recommended to start the MGR service at the same time as mysqld
loose-group_replication_start_on_boot=off

#By default, do not use as the MGR cluster boot node, manually execute it when necessary and immediately change it back to OFF state
loose-group_replication_bootstrap_group=off

#When exiting MGR, set the instance to read_only to avoid misoperation to write data
loose-group_replication_exit_state_action=READ_ONLY

#Generally there is no need to open the flow control mechanism
loose-group_replication_flow_control_mode = "DISABLED"

#【Strongly】Single-master mode is recommended, if it is for experimental purposes, you can try to play in multi-master mode
loose-group_replication_single_primary_mode=ON

[mysqld_multi]
mysqld = /usr/local/GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64/bin/mysqld
log = /data/GreatSQL/mysqld_multi.log
mysqladmin = /usr/local/GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64/bin/mysqladmin
user=root

[mysqld3306]
datadir=/data/GreatSQL/mgr01
socket=/data/GreatSQL/mgr01/mysql.sock
port=3306
server_id=3306
log-error=/data/GreatSQL/mgr01/error.log
#Specify the IP+port of this node
loose-group_replication_local_address= "127.0.0.1:33061"

[mysqld3307]
datadir=/data/GreatSQL/mgr02
socket=/data/GreatSQL/mgr02/mysql.sock
port=3307
server_id=3307
log-error=/data/GreatSQL/mgr02/error.log
loose-group_replication_local_address= "127.0.0.1:33071"

[mysqld3308]
datadir=/data/GreatSQL/mgr03
socket=/data/GreatSQL/mgr03/mysql.sock
port=3308
server_id=3308
log-error=/data/GreatSQL/mgr03/error.log
loose-group_replication_local_address= "127.0.0.1:33081"
```

In my.cnf, the content of `[mysqld]` is read by all instances, and the configuration of `[mysqld3306]` is unique to the instance of port 3306.

When building an MGR cluster, it is necessary to ensure that the value of the `group_replication_group_name` option of each node in the cluster is the same, otherwise it will be a different cluster.

In addition, if there is a firewall, pay attention to opening the access rules between the ports, otherwise MGR cannot be started.

### 3. Initialize the MySQL instance
First manually create the corresponding datadir, and modify the owner of the directory to the mysql user:
```
[root@greatsql]# mkdir -p /data/GreatSQL/{mgr01,mgr02,mgr03}
[root@greatsql]# chown -R mysql.mysql /data/GreatSQL
```

Execute the following command to initialize the MySQL instance, it will automatically create the InnoDB system tablespace, redo log, undo log files:
```
[root@greatsql]# /usr/local/GreatSQL-8.0.22/bin/mysqld --no-defaults --datadir=/data/GreatSQL/mgr01 --initialize --user=mysql

[System] [MY-013169] [Server] /usr/local/GreatSQL-8.0.22/bin/mysqld (mysqld 8.0.22-13) initializing of server in progress as process 18688
[System] [MY-013576] [InnoDB] InnoDB initialization has started.
[System] [MY-013577] [InnoDB] InnoDB initialization has ended.
[Note] [MY-010454] [Server] A temporary password is generated for root@localhost: h<GL%Lr:v66W
```

As you can see, the temporary password of the root account (the last line) is printed in the output log. After starting the mysqld instance, if you login with this password for the first time, you must modify it immediately, otherwise nothing else can be done:

In the same way, the initialization of mgr02 and mgr03 are also completed respectively.

Next, start three mysqld instances:
```
[root@greatsql]# /usr/local/GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64/bin/mysqld_multi start 3306
[root@greatsql]# /usr/local/GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64/bin/mysqld_multi start 3307
[root@greatsql]# /usr/local/GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64/bin/mysqld_multi start 3308
```

You can see that the file directory under datadir looks like this:
```
-rw-r----- 1 mysql mysql 56 Jun 4 10:44 auto.cnf
-rw-r----- 1 mysql mysql 401 Jun 4 10:46 binlog.000001
-rw-r----- 1 mysql mysql 16 Jun 4 10:46 binlog.index
-rw------- 1 mysql mysql 1676 Jun 4 10:44 ca-key.pem
-rw-r--r-- 1 mysql mysql 1120 Jun 4 10:44 ca.pem
-rw-r--r-- 1 mysql mysql 1120 Jun 4 10:44 client-cert.pem
-rw------- 1 mysql mysql 1680 Jun 4 10:44 client-key.pem
-rw-r----- 1 mysql mysql 8800 Jun 4 10:46 error.log
-rw-r----- 1 mysql mysql 196608 Jun 4 10:48 #ib_16384_0.dblwr
-rw-r----- 1 mysql mysql 8585216 Jun 4 10:44 #ib_16384_1.dblwr
-rw-r----- 1 mysql mysql 6274 Jun 4 10:44 ib_buffer_pool
-rw-r----- 1 mysql mysql 12582912 Jun 4 10:46 ibdata1
-rw-r----- 1 mysql mysql 50331648 Jun 4 10:48 ib_logfile0
-rw-r----- 1 mysql mysql 50331648 Jun 4 10:44 ib_logfile1
-rw-r----- 1 mysql mysql 12582912 Jun 4 10:46 ibtmp1
drwxr-x--- 2 mysql mysql 168 Jun 4 10:46 #innodb_temp
drwxr-x--- 2 mysql mysql 143 Jun 4 10:44 mysql
-rw-r----- 1 mysql mysql 25165824 Jun 4 10:46 mysql.ibd
srwxrwxrwx 1 mysql mysql 0 Jun 4 10:46 mysql.sock
-rw------- 1 mysql mysql 6 Jun 4 10:46 mysql.sock.lock
drwxr-x--- 2 mysql mysql 8192 Jun 4 10:46 performance_schema
-rw------- 1 mysql mysql 1680 Jun 4 10:44 private_key.pem
-rw-r--r-- 1 mysql mysql 452 Jun 4 10:44 public_key.pem
-rw-r--r-- 1 mysql mysql 1120 Jun 4 10:44 server-cert.pem
-rw------- 1 mysql mysql 1676 Jun 4 10:44 server-key.pem
drwxr-x--- 2 mysql mysql 28 Jun 4 10:44 sys
-rw-r----- 1 mysql mysql 10485760 Jun 4 10:48 undo_001
-rw-r----- 1 mysql mysql 10485760 Jun 4 10:46 undo_002
-rw-r----- 1 mysql mysql 6 Jun 4 10:46 greatsql.pid
```

### 4. Build an MGR cluster
#### 4.1 Preparations before building an MGR cluster
Because the two plugins `group_replication` and `mysql_clone` have been specified in the configuration file, if nothing happens, they should have been loaded successfully:
```
[root@GreatSQL][(3306)]> show plugins;
+---------------------------------+----------+--------------------+----------------------+---------+
| Name                            | Status   | Type               | Library              | License |
+---------------------------------+----------+--------------------+----------------------+---------+
| binlog                          | ACTIVE   | STORAGE ENGINE     | NULL                 | GPL     |
...
| clone                           | ACTIVE   | CLONE              | mysql_clone.so       | GPL     |
| group_replication               | ACTIVE   | GROUP REPLICATION  | group_replication.so | GPL     |
+---------------------------------+----------+--------------------+----------------------+---------+
```
See that it has indeed been loaded.

If it is not loaded correctly, you need to check the log file to confirm why it could not be loaded.

You can also try to load these two plugins manually:
```
[root@GreatSQL][(3306)]> INSTALL PLUGIN group_replication SONAME'group_replication.so';
[root@GreatSQL][(3306)]> INSTALL PLUGIN clone SONAME'mysql_clone.so';
```

The role of `clone plugin` will be introduced later.

#### 4.2 Configure MGR cluster PRIMARY node
Next, create the account required by MGR and grants:
```
[root@GreatSQL][(3306)]> CREATE USER repl@'%' IDENTIFIED WITH MYSQL_NATIVE_PASSWORD BY'repl';
[root@GreatSQL][(3306)]> GRANT REPLICATION SLAVE, BACKUP_ADMIN ON *.* TO `repl`@`%`;
```

Because it is a clean system that has just been initialized, for the sake of simplicity, execute the following command to reset it again:
```
[root@GreatSQL][(3306)]> reset master; reset slave all;
```
[Reminder] **Do not do this in a online production environment**. There will be other articles later on how to add new nodes to the online MGR cluster.

Create MGR replication channel:
```
[root@GreatSQL][(3306)]> CHANGE MASTER TO MASTER_USER='repl', MASTER_PASSWORD='repl' FOR CHANNEL'group_replication_recovery';
```

All the above operations are repeated on several other nodes.

Then, the **important step** is here, login to the mgr01 instance selected as the **PRIMARY** node, and execute the following command:
```
[root@GreatSQL][(3306)]> set global group_replication_bootstrap_group=ON;
```
The function of this command is to guide the MGR cluster when the PRIMARY node of the MGR cluster is started for the first time.

When other nodes start, remember to **don't** set the option `group_replication_bootstrap_group=OBN`, otherwise a new MGR cluster will be launched independently.

Then you can start the group replication thread on the **PRIMARY** node of the MGR cluster:
```
[root@GreatSQL][(3306)]> start group_replication;
Query OK, 0 rows affected (2.14 sec)

[root@GreatSQL][(3306)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            |  MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 0fbb2cfd-c4d9-11eb-8747-525400e2078a | greatsql-mgr |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
You can see that the MGR cluster has been started, and there are only PRIMARY nodes.

After the cluster starts, remember to reset option `group_replication_bootstrap_group` to OFF immediately.
```
[root@GreatSQL][(3306)]> set global group_replication_bootstrap_group=OFF;
```

Next, execute `start group_replication` on the mgr02 and mgr03 nodes to start the MGR service, remember to set `group_replication_bootstrap_group=OFF`.

#### 4.3 Check status of MGR cluster
After all instances have started the MGR service, check the cluster status again:
```
[root@GreatSQL][(3308)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            |  MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 0fbb2cfd-c4d9-11eb-8747-525400e2078a | greatsql-mgr |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | 1778e87a-c4d9-11eb-bf33-525400e2078a | greatsql-mgr |        3307 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | 1c8ebfa6-c4d9-11eb-80d1-525400e2078a | greatsql-mgr |        3308 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+

```
Because the MGR built with multiple instances is started on the same host, the value of **MEMBER_HOST** is the same.

An MGR cluster composed of three instances on same host has been constructed.

#### 4.4 Test data reading and writing
Note, **Only the PRIMARY node allows simultaneous reading and writing of data, and other nodes can only read data but cannot write**.

On the PRIMARY node, create a new table and write a few rows of data:
```
[root@GreatSQL][(3306)]> create database greatsql;
[root@GreatSQL][(3306)]> use greatsql;
[root@GreatSQL][(3306)][greatsql]> create table t1(id int primary key);
[root@GreatSQL][(3306)][greatsql]> insert into t1 values ​​(rand()*1024), (rand()*1024), (rand()*1024);
Query OK, 3 rows affected (0.01 sec)
Records: 3 Duplicates: 0 Warnings: 0

[root@GreatSQL][(3306)][greatsql]> select * from t1;
+-----+
| id  |
+-----+
| 105 |
| 423 |
| 557 |
+-----+
3 rows in set (0.00 sec)
```

Read the data on the other two nodes:
```
[root@GreatSQL][(3308)]> select * from greatsql.t1;
+-----+
| id  |
+-----+
| 105 |
| 423 |
| 557 |
+-----+
3 rows in set (0.00 sec)
```
The newly written data can be read.

Check the working status of the applier thread of MGR again:
```
[root@GreatSQL][(3306)]> select * from performance_schema.replication_connection_status where channel_name ='group_replication_applier'\G
*************************** 1. row ******************** *******
                                      CHANNEL_NAME: group_replication_applier
                                        GROUP_NAME: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1
                                       SOURCE_UUID: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1
                                         THREAD_ID: NULL
                                     SERVICE_STATE: ON <---The state is ON, normal
                         COUNT_RECEIVED_HEARTBEATS: 0
                          LAST_HEARTBEAT_TIMESTAMP: 0000-00-00 00:00:00.000000
                          RECEIVED_TRANSACTION_SET: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1:1-19 <--- GTID is constantly changing
                                 LAST_ERROR_NUMBER: 0
                                LAST_ERROR_MESSAGE:
                              LAST_ERROR_TIMESTAMP: 0000-00-00 00:00:00.000000
                           LAST_QUEUED_TRANSACTION: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1:19
 LAST_QUEUED_TRANSACTION_ORIGINAL_COMMIT_TIMESTAMP: 0000-00-00 00:00:00.000000
LAST_QUEUED_TRANSACTION_IMMEDIATE_COMMIT_TIMESTAMP: 0000-00-00 00:00:00.000000
     LAST_QUEUED_TRANSACTION_START_QUEUE_TIMESTAMP: 2021-06-04 15:53:55.395605
       LAST_QUEUED_TRANSACTION_END_QUEUE_TIMESTAMP: 2021-06-04 15:53:55.395630
                              QUEUEING_TRANSACTION:
    QUEUEING_TRANSACTION_ORIGINAL_COMMIT_TIMESTAMP: 0000-00-00 00:00:00.000000
   QUEUEING_TRANSACTION_IMMEDIATE_COMMIT_TIMESTAMP: 0000-00-00 00:00:00.000000
        QUEUEING_TRANSACTION_START_QUEUE_TIMESTAMP: 0000-00-00 00:00:00.000000
```

And checkthe status of each member of the replication group:
```
[root@GreatSQL][(3306)]> select * from performance_schema.replication_group_member_stats\G
*************************** 1. row ******************** *******
                              CHANNEL_NAME: group_replication_applier
                                   VIEW_ID: 16227931944218245:4
                                 MEMBER_ID: 0fbb2cfd-c4d9-11eb-8747-525400e2078a
               COUNT_TRANSACTIONS_IN_QUEUE: 0 <--- The size of the transaction queue waiting for conflict detection
                COUNT_TRANSACTIONS_CHECKED: 0
                  COUNT_CONFLICTS_DETECTED: 0
        COUNT_TRANSACTIONS_ROWS_VALIDATING: 0
        TRANSACTIONS_COMMITTED_ALL_MEMBERS: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1:1-19
            LAST_CONFLICT_FREE_TRANSACTION:
COUNT_TRANSACTIONS_REMOTE_IN_APPLIER_QUEUE: 0 <--- local transaction queue size waiting for apply
         COUNT_TRANSACTIONS_REMOTE_APPLIED: 3
         COUNT_TRANSACTIONS_LOCAL_PROPOSED: 0
         COUNT_TRANSACTIONS_LOCAL_ROLLBACK: 0
         ...
```

### 5. Add a new node
If you want to expand the read performance of the MGR cluster, you can add a new SECONDARY node.

According to the previous steps, first initialize a new instance mgr04, which runs on port 3309. Then use **clone plugin** (both source and target nodes must enable clone plugin) to copy data from other existing nodes, and then join the MGR cluster.

Running clone plugin requires `BACKUP_ADMIN` permission (required for both the source and target nodes), which has been granted previously.

First, set the donor node:
```
# Try to copy data from the SECONDARY node, not from the PRIMARY node
[root@GreatSQL][(3309)]> set global clone_valid_donor_list='127.0.0.1:3307';
```

Start copying data:
```
[root@GreatSQL][(3309)]> clone instance from repl@127.0.0.1:3307 identified by'repl';

After #clone is over, the mysqld instance will be restarted automatically
#But because the instance is not managed by the systemd service, you need to manually start the process
ERROR 3707 (HY000): Restart server failed (mysqld is not managed by supervisor process).
```

Start the 3309 port instance again, login and query, you can see the data copied from other nodes:
```
[root@GreatSQL][(3309)]> select * from greatsql.t1;
+-----+
| id  |
+-----+
| 105 |
| 423 |
| 557 |
+-----+
3 rows in set (0.00 sec)
```

Start the MGR service on the mgr04 instance:
```
[root@GreatSQL][(3309)]> start group_replication;
Query OK, 0 rows affected (2.85 sec)

[root@GreatSQL][(3309)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            |  MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 0fbb2cfd-c4d9-11eb-8747-525400e2078a | greatsql-mgr |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | 1778e87a-c4d9-11eb-bf33-525400e2078a | greatsql-mgr |        3307 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | 1c8ebfa6-c4d9-11eb-80d1-525400e2078a | greatsql-mgr |        3308 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | bc037d6c-c4de-11eb-a5b8-525400e2078a | greatsql-mgr |        3309 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
As you can see, the new node has been added successfully.

![Enter picture description](https://images.gitee.com/uploads/images/2021/0623/171805_392264ca_8779455.png "Screenshot.png")

### 6. Switch the PRTMARY node
If you need to upgrade the MySQL version of each node in the MGR cluster, you can perform a **rolling upgrade**.

That is, **first upgrade all SECONDARY nodes, then stop the PRIMARY node, and finally upgrade it**, the MGR cluster will automatically select other upgraded nodes as the new PRIMARY node. After the original PRIMARY node is also upgraded, join back, and this completes the upgrade of all nodes in the entire cluster.

#### 6.1 Upgrade SECONDARY node first
Now to upgrade the MySQL version of the mgr4 node, you need to stop the MGR service first:
```
[root@GreatSQL][(3309)]> stop group_replication;
```

After stopping the mysqld process, add a line of configuration to my.cnf:
```
upgrade=AUTO
```

Replace/specify a new MySQL binary program file, and restart the mysqld process, MySQL will upgrade automatically.

This is a new upgrade method as of MySQL 8.0.16. Before 8.0.16, you need to manually execute the `mysql_upgrade` binary program to upgrade.

During the startup process, you can see a log similar to the following:
```
[System] [MY-013381] [Server] Server upgrade from '80022' to '80025' started.
[Note] [MY-013386] [Server] Running queries to upgrade MySQL server.
[Note] [MY-013387] [Server] Upgrading system table data.
[Note] [MY-013385] [Server] Upgrading the sys schema.
```

After starting the MGR service, you can see that the MySQL version of each node is different.
```
[root@GreatSQL][(3309)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            |  MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 0fbb2cfd-c4d9-11eb-8747-525400e2078a | greatsql-mgr |        3306 | ONLINE       | PRIMARY     | 8.0.22         |
| group_replication_applier | 1778e87a-c4d9-11eb-bf33-525400e2078a | greatsql-mgr |        3307 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | 1c8ebfa6-c4d9-11eb-80d1-525400e2078a | greatsql-mgr |        3308 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | bc037d6c-c4de-11eb-a5b8-525400e2078a | greatsql-mgr |        3309 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
As shown in the figure above, only the mgr01 node has not been upgraded yet.

Starting from MySQL 8.0.16, new MGR protocol requirements have been added, such as using the same communication protocol version to form an MGR cluster, and 8.0.22 and 8.0.25 are the same, so they can be in the same cluster.
```
#Execute on mgr01
[root@GreatSQL][(3306)]> select version(), group_replication_get_communication_protocol();
+-----------+------------------------------------------------+
| version() | group_replication_get_communication_protocol() |
+-----------+------------------------------------------------+
| 8.0.22-13 | 8.0.16                                         |
+-----------+------------------------------------------------+

#Execute on mgr04
[root@GreatSQL][(3309)]> select version(), group_replication_get_communication_protocol();
+-----------+------------------------------------------------+
| version() | group_replication_get_communication_protocol() |
+-----------+------------------------------------------------+
| 8.0.25    | 8.0.16                                         |
+-----------+------------------------------------------------+
```

#### 6.2 Upgrade PRIMARY node 
Now after shutting down the mgr01 node, the remaining three nodes will election new PRIMARY node automatically:
```
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            |  MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 1778e87a-c4d9-11eb-bf33-525400e2078a | greatsql-mgr |        3307 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | 1c8ebfa6-c4d9-11eb-80d1-525400e2078a | greatsql-mgr |        3308 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | bc037d6c-c4de-11eb-a5b8-525400e2078a | greatsql-mgr |        3309 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
The mgr02 node is automatically selected as the new PRIMARY node (when the weight value of each node is not set, the primary is selected in the order of `MEMBER_ID`).

After the mgr01 node is also upgraded, rejoin to the cluster:
```
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            |  MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 0fbb2cfd-c4d9-11eb-8747-525400e2078a | greatsql-mgr |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | 1778e87a-c4d9-11eb-bf33-525400e2078a | greatsql-mgr |        3307 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | 1c8ebfa6-c4d9-11eb-80d1-525400e2078a | greatsql-mgr |        3308 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | bc037d6c-c4de-11eb-a5b8-525400e2078a | greatsql-mgr |        3309 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
![Enter picture description](https://images.gitee.com/uploads/images/2021/0623/171824_2bc1e254_8779455.png "Screenshot.png")

#### 6.3 Switch PRIMARY nodes manually
At this time, still choose mgr02 as the PRIMARY node, and there will be no change, unless switch it manually:
```
[root@GreatSQL][(3306)]> select group_replication_set_as_primary('0fbb2cfd-c4d9-11eb-8747-525400e2078a');
+--------------------------------------------------------------------------+
| group_replication_set_as_primary('0fbb2cfd-c4d9-11eb-8747-525400e2078a') |
+--------------------------------------------------------------------------+
| Primary server switched to: 0fbb2cfd-c4d9-11eb-8747-525400e2078a         |
+--------------------------------------------------------------------------+

[root@GreatSQL][(3306)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            |  MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 0fbb2cfd-c4d9-11eb-8747-525400e2078a | greatsql-mgr |        3306 | ONLINE      |  PRIMARY     | 8.0.25         |
| group_replication_applier | 1778e87a-c4d9-11eb-bf33-525400e2078a | greatsql-mgr |        3307 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | 1c8ebfa6-c4d9-11eb-80d1-525400e2078a | greatsql-mgr |        3308 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | bc037d6c-c4de-11eb-a5b8-525400e2078a | greatsql-mgr |        3309 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
This completes the rolling upgrade and all operations of switching primary again.

There is no essential difference between building an MGR cluster on a same host with multiple nodes and building it on multiple hosts. You can do it yourself.

Enjoy MGR & GreatSQL :)
