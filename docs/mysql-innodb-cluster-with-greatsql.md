# How to deploy MGR Cluster by MySQL InnoDB Cluster and GreatSQL

## 0. Outline

MySQL InnoDB Cluster (MIC for short) is a complete solution launched by MySQL, which consists of several parts:
- MySQL Server, the core is Group Replication (MGR).
- MySQL Shell, a programmable advanced client, supports standard SQL syntax, JavaScript syntax, Python syntax, and API interfaces, making it easier to manage and use the MySQL server.
- MySQL Router, lightweight middleware, supports transparent routing rules (read-write separation and read load balancing).

This article describes in detail how to use MIC and GreatSQL to build an MGR cluster, and combine MySQL Router to achieve read-write separation, read load balancing, and automatic failover architecture.

For the sake of simplicity, this MGR cluster uses a single-primary mode instead of a multi-primary mode.

The overall system architecture is shown in the figure below:
![Enter image description](https://images.gitee.com/uploads/images/2021/0623/172104_653e92d0_8779455.png "The architecture of MySQL InnoDB Cluster.png")

## 1. Deployment environment and initialization

It is recommended to use yum to install MySQL Shell, Router and MySQL Community server.

If you don’t have the yum source of MySQL, you need to download and install the repo package first. The download address is:
```
https://dev.mysql.com/downloads/repo/yum/
```

Choose the correct version of the corresponding OS to download and install, for example:
```
[root@greatsql]# yum -y install https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm
```

Then you can use yum to install MySQL-related software packages.
```
[root@greatsql]# yum install -y mysql-shell mysql-router mysql-community-server
```

In addition to the official MySQL community server, if you want to experience a more reliable, stable, and efficient MGR, the GreatSQL is recommended. This article uses GreatSQL version 8.0.25. For details on this version, please refer to [GreatSQL, Build a Better MGR Ecosystem](https://mp.weixin.qq.com/s/ByAjPOwHIwEPFtwC5jA28Q).

The GreatSQL binary package is placed under /usr/local/, ie basedir = /usr/local/GreatSQL-8.0.25.

The MGR cluster is composed of three instances, which are allocated according to the following plan:

| Examples | IP | Port | datadir
| --- |--- |--- |--- |
|GreatSQL-01|172.16.16.10|3306|/data/GreatSQL/
|GreatSQL-02|172.16.16.11|3306|/data/GreatSQL/
|GreatSQL-03|172.16.16.12|3306|/data/GreatSQL/

In addition, for the convenience of mysqld service management, I directly modify the 52nd line of the configuration file about mysqld service in systemd:
```
[root@greatsql]# vim /usr/lib/systemd/system/mysqld.service +52
...
ExecStart=/usr/local/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64/bin/mysqld $MYSQLD_OPTS
#ExecStart=/usr/sbin/mysqld $MYSQLD_OPTS
```

After modifying, save and exit, execute the following command to let systemd reload the configuration file:
```
[root@greatsql]# systemctl daemon-reload
```

In this way, systemd can be used to manage mysqld services.
```
[root@greatsql]# systemctl start/stop/status/restart mysqld.service
```

Since the `/usr/sbin/mysqld` binary file needs to be called in `/usr/bin/mysqld_pre_systemd`, this should also be replaced:
```
#yuminstalled make a backup
[root@greatsql]# mv /usr/sbin/mysqld /usr/sbin/mysqld-8.0.25

# Make a soft chain replacement
[root@greatsql]# ln -s /usr/local/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64/bin/mysqld /usr/sbin/mysqld
```

In order to make mysqld use jemalloc instead, edit the file at the same time:
```
[root@greatsql]# vim /etc/sysconfig/mysql
LD_PRELOAD=/usr/lib64/libjemalloc.so.1
```

This is a configuration reference (you can adjust it according to the actual situation):
```
[mysqld]
basedir=/usr/local/GreatSQL-8.0.22
datadir=/data/GreatSQL
socket=/data/GreatSQL/mysql.sock
log_timestamps=SYSTEM
user = mysql
log_error_verbosity = 3
log-error=/data/GreatSQL/error.log
port=3306
server_id=3310

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
loose-group_replication_group_name="fbc510f0-c5ba-11eb-bfaf-5254002eb6d6"

#Specify the IP+port of this node
loose-group_replication_local_address= "172.16.16.10:33061"

#Specify the IP+port of each node in the MGR cluster, this port is dedicated to MGR, not the usual mysqld instance port
#If you are deploying an MGR cluster on multiple nodes, pay attention to whether this port will be blocked by the firewall
loose-group_replication_group_seeds= "172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061"

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
```

Finally, you can directly start the mysqld service (the first startup will complete the initialization by itself):
```
[root@greatsql]# systemctl start mysqld.service
```

During initialization, a temporary password will be generated for the root account, such as this:
```
[Note] [MY-010454] [Server] A temporary password is generated for root@localhost: h<GL%Lr:v66W
```

After logging in with this password for the first time, you must modify it immediately, otherwise nothing else can be done:
```
[root@GreatSQL](none)> ALTER USER CURRENT_USER() IDENTIFIED BY'GreatSQL-##)^';
```

In the same way, complete the initialization of the MySQL instances of other nodes and check the GreatSQL that is running.
```
[root@GreatSQL](none)> \s
...
Server version: 8.0.22-13 Source distribution
```

## 2. Use MySQL Shell to build an MGR cluster
Using MySQL Shell to build an MGR cluster can be done with a few simple commands. It is indeed much more convenient than manual deployment.

It only takes three steps:
- Check whether the instance meets the conditions.
- Create and initialize a cluster.
- Add instances one by one.

To use MySQL Shell to build an MGR cluster, in addition to meeting the basic requirements of MGR (must have InnoDB tables, and must have primary keys, etc.), several other conditions must be met:
- Python version >= 2.7.
- Enable PFS (performance_schema).
- The server_id of each node must be unique.

Then you can start.

After the MySQL instance is started, use the MySQL Shell client tool `mysqlsh` to connect to the server:
```
# For the first time, use the root user with administrative privileges to connect
[root@greatsql]# mysqlsh --uri root@172.16.16.10:3306
Please provide the password for'root@172.16.16.10:3306': <-- Prompt for password
Save password for'mic@172.16.16.10:3306'? [Y]es/[N]o/Ne[v]er (default No): y <-- Prompt whether to save the password (depending on the company’s security rules, The storage password is selected here for convenience)
Fetching schema names for autocompletion... Press ^C to stop.
Closing old connection...
Your MySQL connection id is 14
Server version: 8.0.22-13 Source distribution
No default schema selected; type \use <schema> to set one. <--- successfully connected to the server

 MySQL 172.16.16.10:3306 ssl JS> \s <-- View the current status, which is equivalent to executing the \s command under the mysql client
MySQL Shell version 8.0.25 <-- mysql shell client version number

Connection Id: 20425
Current schema:
Current user: root@GreatSQL-01
SSL: Cipher in use: ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2
Using delimiter:;
Server version: 8.0.22-13 Source distribution <-- server version number
Protocol version: Classic 10
Client library: 8.0.25
Connection: 172.16.16.10 via TCP/IP
TCP port: 3306
Server characterset: utf8mb4
Schema characterset: utf8mb4
Client characterset: utf8mb4
Conn. characterset: utf8mb4
Result characterset: utf8mb4
Compression: Disabled
Uptime: 2 hours 56 min 50.0000 sec

Threads: 8 Questions: 216540 Slow queries: 10563 Opens: 264 Flush tables: 3 Open tables: 183 Queries per second avg: 20.409

#You can also switch to the sql command line mode and execute a command
 MySQL 172.16.16.10:3306 ssl JS> \sql select user();
+------------------------+
| user() |
+------------------------+
| root@GreatSQL-01 |
+------------------------+
```

**tips:**
`mysqlsh` can also be used like `mysql` client **pager**:
```
mysqlsh> shell.enablePager();
mysqlsh> shell.options["pager"]="less -i -n -S";
Pager has been set to'less -i -n -S'.
```

**1. Check whether the instance meets the conditions for installing the MGR cluster**
Next, execute the `dba.configureInstance()` command to check whether the current instance is ready and can be used as a node of the MGR cluster:
```
#Check the syntax and usage of the command
MySQL 172.16.16.10:3306 ssl JS> \help dba.configureInstance
NAME
      configureInstance-Validates and configures an instance for MySQL InnoDB
                          Cluster usage.

SYNTAX
      dba.configureInstance([instance][, options])

WHERE
      instance: An instance definition.
      options: Additional options for the operation.

RETURNS
      A descriptive text of the operation result.
      ...
      
# Start configuring MIC
MySQL 172.16.16.10:3306 ssl JS> dba.configureInstance();
Configuring local MySQL instance listening at port 3306 for use in an InnoDB cluster...

This instance reports its own address as GreatSQL-01:3306
Clients and other cluster members will communicate with it through this address by default. If this is not correct, the report_host MySQL system variable should be changed.

#root user cannot run MGR service, you need to create a new dedicated account
ERROR: User'root' can only connect from'localhost'. New account(s) with proper source address specification to allow remote connection from all instances must be created to manage the cluster.

1) Create remotely usable account for'root' with same grants and password
2) Create a new admin account for InnoDB cluster with minimal required grants
3) Ignore and continue
4) Cancel

Please select an option [1]: 2 #<-- Choose to create a least-privileged account
Please provide an account name (e.g: icroot@%) to have it created with the necessary
privileges or leave empty and press Enter to cancel.
Account Name: mic <-- account name
Password for new account: ******* <-- Password***
Confirm password: *******

#Node initialization is complete
The instance'GreatSQL-01:3306' is valid to be used in an InnoDB cluster.

#MGR Management user account created
Cluster admin user'mic'@'%' created.
The instance'GreatSQL-01:3306' is already ready to be used in an InnoDB cluster.
```

The above `dba.configureInstance()` command is also executed on other nodes.

**2. Create MGR cluster**
After the nodes are initialized, use the **mysqlsh** client to login to the PRIMARY node with the management user account of the newly created MGR, and prepare to create the MGR cluster:
```
[root@greatsql]# mysqlsh --uri mic@172.16.16.10:3306
Creating a session to'mic@172.16.16.10:3306'
Please provide the password for'mic@172.16.16.10:3306': *******
Save password for'mic@172.16.16.10:3306'? [Y]es/[N]o/Ne[v]er (default No): y
Fetching schema names for autocompletion... Press ^C to stop.
Closing old connection...
Your MySQL connection id is 14
Server version: 8.0.22-13 Source distribution
No default schema selected; type \use <schema> to set one.

#Start creating an MGR cluster on the PRIMARY node
# The cluster is named GreatSQLMGR, which will be used later when mysqlrouter reads metadata
MySQL 172.16.16.10:3306 ssl JS> var mic = dba.createCluster('GreatSQLMGR');
A new InnoDB cluster will be created on instance '172.16.16.10:3306'.

Validating instance configuration at 172.16.16.10:3306...

This instance reports its own address as GreatSQL-01:3306

Instance configuration is suitable.
NOTE: Group Replication will communicate with other members using'GreatSQL-01:33061'. Use the localAddress option to override.

Creating InnoDB cluster'GreatSQLMGR' on'GreatSQL-01:3306'...

Adding Seed Instance...
Cluster successfully created. Use Cluster.addInstance() to add MySQL instances.
At least 3 instances are needed for the cluster to be able to withstand up to
one server failure.
```

The cluster has been created and initialized, the next step is to continue adding other nodes.

**3. Add other nodes**
You can directly add other nodes on the PRIMARY node, or you can use the **mysqlsh** client to login to other nodes to perform the operation of adding nodes. The former is used here:
```
MySQL 172.16.16.10:3306 ssl JS> mic.addInstance('mic@172.16.16.11:3306'); <-- Add other MGR nodes
NOTE: The target instance'GreatSQL-02:3306' has not been pre-provisioned (GTID set is empty). The Shell is unable to decide whether incremental state recovery can correctly provision it.
The safest and most convenient way to provision a new instance is through automatic clone provisioning, which will completely overwrite the state of'GreatSQL-02:3306' with a physical snapshot from an existing cluster member. To use this method by default, set the 'recoveryMethod' option to'clone'.

The incremental state recovery may be safely used if you are sure all updates ever executed in the cluster were done with GTIDs enabled, there are no purged transactions and the new instance contains the same GTID set as the cluster or a subset of it. To use this method by default, set the'recoveryMethod' option to'incremental'.

#Select recovery mode: clone/incremental recovery/ignore, clone is selected by default
Please select a recovery method [C]lone/[I]ncremental recovery/[A]bort (default Clone):
Validating instance configuration at 172.16.16.11:3306...

This instance reports its own address as GreatSQL-02:3306

Instance configuration is suitable.
NOTE: Group Replication will communicate with other members using'GreatSQL-02:33061'. Use the localAddress option to override.

A new instance will be added to the InnoDB cluster. Depending on the amount of
data on the cluster this might take from a few seconds to several hours.

Adding instance to the cluster...

Monitoring recovery process of the new cluster member. Press ^C to stop monitoring and let it continue in background.
Clone based state recovery is now in progress.

# Prompt that the GreatSQL-02 node instance needs to be restarted during this process
# If you cannot restart automatically, you need to restart manually
NOTE: A server restart is expected to happen as part of the clone process. If the
server does not support the RESTART command or does not come back after a
while, you may need to manually start it back.

* Waiting for clone to finish...
#Clone data from GreatSQL-01 node
NOTE: GreatSQL-02:3306 is being cloned from GreatSQL-01:3306
** Stage DROP DATA: Completed
** Clone Transfer
    FILE COPY ############################################# ############ 100% Completed
    PAGE COPY ############################################## ############ 100% Completed
    REDO COPY ############################################# ############ 100% Completed
    NOTE: GreatSQL-02:3306 is shutting down...

* Waiting for server restart... \ <-- restarting
* Waiting for server restart... ready <-- After restarting, if you have not joined systemed, you need to manually start it yourself
* GreatSQL-02:3306 has restarted, waiting for clone to finish...
** Stage RESTART: Completed
* Clone process has finished: 59.62 MB transferred in about 1 second (~59.62 MB/s)

State recovery already finished for'GreatSQL-02:3306'

# New node GreatSQL-02: 3306 has joined the cluster
The instance'GreatSQL-02:3306' was successfully added to the cluster.
```

The same operation is also performed on the **GreatSQL-03:3306** node and added to the MGR cluster.

After all nodes have joined the MGR cluster, check the cluster status:
```
# check thread list 
MySQL  172.16.16.10:3306 ssl  JS > \sql show processlist;
+-------+----------------------------+-------------------+------+---------+-------+--------------------------------------------------------+----------------------------------+-----------+---------------+
| Id    | User                       | Host              | db   | Command | Time  | State                                                  | Info                             | Rows_sent | Rows_examined |
+-------+----------------------------+-------------------+------+---------+-------+--------------------------------------------------------+----------------------------------+-----------+---------------+
|     9 | system user                |                   | NULL | Connect | 19935 | waiting for handler commit                             | Group replication applier module |         0 |             0 |
|    12 | system user                |                   | NULL | Query   |     5 | Slave has read all relay log; waiting for more updates | NULL                             |         0 |             0 |
|    13 | system user                |                   | NULL | Query   |     5 | Waiting for an event from Coordinator                  | NULL                             |         0 |             0 |
|    14 | system user                |                   | NULL | Connect | 19934 | Waiting for an event from Coordinator                  | NULL                             |         0 |             0 |
| 20425 | mic                        | GreatSQL-01:42678 | NULL | Query   |     0 | init                                                   | show processlist                 |         0 |             0 |
| 38381 | mysql_router1_2ya0m3z4582s | GreatSQL-01:54034 | NULL | Sleep   |     1 |                                                        | NULL                             |         4 |             4 |
+-------+----------------------------+-------------------+------+---------+-------+--------------------------------------------------------+----------------------------------+-----------+---------------+

# check cluster status
MySQL  172.16.16.10:3306 ssl  JS > mic.describe();
{
    "clusterName": "GreatSQLMGR",
    "defaultReplicaSet": {
        "name": "default",
        "topology": [
            {
                "address": "GreatSQL-01:3306",
                "label": "GreatSQL-01:3306",
                "role": "HA"
            },
            {
                "address": "GreatSQL-02:3306",
                "label": "GreatSQL-02:3306",
                "role": "HA"
            },
            {
                "address": "GreatSQL-03:3306",
                "label": "GreatSQL-03:3306",
                "role": "HA"
            }
        ],
        "topologyMode": "Single-Primary"
    }
}

# check the detail status of cluster
MySQL  172.16.16.10:3306 ssl  JS > mic.status();
{
    "clusterName": "GreatSQLMGR",
    "defaultReplicaSet": {
        "name": "default",
        "primary": "GreatSQL-01:3306",
        "ssl": "REQUIRED",
        "status": "OK",
        "statusText": "Cluster is ONLINE and can tolerate up to ONE failure.",
        "topology": {
            "GreatSQL-01:3306": {
                "address": "GreatSQL-01:3306",
                "memberRole": "PRIMARY",
                "mode": "R/W",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
            "GreatSQL-02:3306": {
                "address": "GreatSQL-02:3306",
                "memberRole": "SECONDARY",
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
... 
        },
        "topologyMode": "Single-Primary"
    },
    "groupInformationSourceMember": "GreatSQL-02:3306"
}

# add {extended:1} extended attributes, more information will be printed
MySQL  172.16.16.10:3306 ssl  JS > mic.status({extended:1});
{
    "clusterName": "GreatSQLMGR",
    "defaultReplicaSet": {
        "GRProtocolVersion": "8.0.16",
        "groupName": "fbc510f0-c5ba-11eb-bfaf-5254002eb6d6",
        "groupViewId": "16228692455693206:28",
        "name": "default",
        "primary": "GreatSQL-01:3306",
        "ssl": "REQUIRED",
        "status": "OK",
        "statusText": "Cluster is ONLINE and can tolerate up to ONE failure.",
        "topology": {
            "GreatSQL-01:3306": {
                "address": "GreatSQL-01:3306",
                "applierWorkerThreads": 2,
                "fenceSysVars": [],
                "memberId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1",
                "memberRole": "PRIMARY",
                "memberState": "ONLINE",
                "mode": "R/W",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
            "GreatSQL-02:3306": {
                "address": "GreatSQL-02:3306",
                "applierWorkerThreads": 2,
                "fenceSysVars": [
                    "read_only",
                    "super_read_only"
                ],
                "memberId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2",
                "memberRole": "SECONDARY",
                "memberState": "ONLINE",
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
           ...  
        },
        "topologyMode": "Single-Primary"
    },
    "groupInformationSourceMember": "GreatSQL-01:3306",
    "metadataServer": "GreatSQL-01:3306",
    "metadataVersion": "2.0.0"
}

# use the SQL command
MySQL  172.16.16.10:3306 ssl  JS >  \sql select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1 | GreatSQL-01 |        3306 | ONLINE       | PRIMARY     | 8.0.22         |
| group_replication_applier | bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2 | GreatSQL-02 |        3306 | ONLINE       | SECONDARY   | 8.0.22         |
| group_replication_applier | bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb3 | GreatSQL-03 |        3306 | ONLINE       | SECONDARY   | 8.0.22         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
```

By now, a three-node MGR cluster has been created.

## 3. Add a new node to the online MGR cluster
The above MGR cluster is online, and now I want to add a new node **GreatSQL-04:3306**, the steps are basically the same as the above, three steps:
- Log in to the MySQL instance with an account with administrative privileges (use the **mysqlsh** client).
- Execute the preprocessing of the `dba.configureInstance()` function.
- Execute the `cluster.addInstance()` function to join the cluster.

I won’t repeat the detailed process and do it by yourself.

If you want to delete a node, you can change it to execute the `cluster.removeInstance()` function.

## 4. Deploy MySQL Router to achieve read-write separation and automatic failover
MySQL Router is a lightweight middleware that uses a multi-port solution to achieve read-write separation and read load balancing, and it supports both mysql and mysqlx protocols.

**1. mysqlrouter initialization**
The server-side program file corresponding to MySQL Router is `/usr/bin/mysqlrouter`, which must be initialized when it is started for the first time:
```
#
# --bootstrap means to start initialization
# mic@172.16.16.10:3306 is the MGR cluster administrator user account
# --user=mysqlrouter is the username of the system running the mysqlrouter process
#
[root@greatsql]# mysqlrouter --bootstrap mic@172.16.16.10:3306 --user=mysqlrouter
Please enter MySQL password for mic: <-- Enter password
# Then mysqlrouter starts to initialize automatically
# It will automatically read the metadata information of MGR and automatically generate configuration files
# Reconfiguring system MySQL Router instance...

- Fetching password for current account (mysql_router1_2ya0m3z4582s) from keyring
- Creating account(s) (only those that are needed, if any)
- Using existing certificates from the '/var/lib/mysqlrouter' directory
- Verifying account (using it to run SQL queries that would be run by Router)
- Storing account in keyring
- Adjusting permissions of generated files
- Creating configuration /etc/mysqlrouter/mysqlrouter.conf

Existing configuration backed up to '/etc/mysqlrouter/mysqlrouter.conf.bak'

# MySQL Router configured for the InnoDB Cluster 'GreatSQLMGR'

After this MySQL Router has been started with the generated configuration

    $ /etc/init.d/mysqlrouter restart
or
    $ systemctl start mysqlrouter
or
    $ mysqlrouter -c /etc/mysqlrouter/mysqlrouter.conf

the cluster 'GreatSQLMGR' can be reached by connecting to:

## MySQL Classic protocol

- Read/Write Connections: localhost:6446
- Read/Only Connections:  localhost:6447

## MySQL X protocol

- Read/Write Connections: localhost:6448
- Read/Only Connections:  localhost:6449
```

**2. start mysqlrouter service**
After initialization is complete, follow the above prompts to directly start the **mysqlrouter** service:
```
[root@greatsql]# systemctl start mysqlrouter

[root@greatsql]# ps -ef | grep -v grep | grep mysqlrouter
mysqlro+ 6026 1 5 09:28? 00:00:00 /usr/bin/mysqlrouter

[root@greatsql]# netstat -lntp | grep mysqlrouter
tcp 0 0 0.0.0.0:6446 0.0.0.0:* LISTEN 6026/mysqlrouter
tcp 0 0 0.0.0.0:6447 0.0.0.0:* LISTEN 6026/mysqlrouter
tcp 0 0 0.0.0.0:6448 0.0.0.0:* LISTEN 6026/mysqlrouter
tcp 0 0 0.0.0.0:6449 0.0.0.0:* LISTEN 6026/mysqlrouter
tcp 0 0 0.0.0.0:8443 0.0.0.0:* LISTEN 6026/mysqlrouter
```
You can see that the **mysqlrouter** service started normally.

**mysqlrouter** The configuration file automatically generated during initialization is `/etc/mysqlrouter/mysqlrouter.conf`, mainly about the configuration of different ports of R/W and RO, for example:
```
[routing:GreatSQLMGR_rw]
bind_address=0.0.0.0
bind_port=6446
destinations=metadata-cache://GreatSQLMGR/?role=PRIMARY
routing_strategy=first-available
protocol=classic
```
You can change the IP address and port according to your needs.

**3. Confirm the effect of reading and writing separation**
Now, use the client to connect to port 6446 (read and write) and confirm that the connection is the PRIMARY node:
```
[root@greatsql]# mysql -h172.16.16.10 -u mic -p -P6446
Enter password:
...
mic@GreatSQL [(none)]>select @@server_uuid;
+--------------------------------------+
| @@server_uuid                        |
+--------------------------------------+
| bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1 |
+--------------------------------------+
# It is indeed the connected PRIMARY node (GreatSQL-01)
```

Similarly, connect to port 6447 (read-only) and confirm that the SECONDARY node is connected:
```
[root@greatsql]# mysql -h172.16.16.10 -u mic -p -P6447
Enter password:
...
mic@GreatSQL [(none)]>select @@server_uuid;
+--------------------------------------+
| @@server_uuid                        |
+--------------------------------------+
| bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2 |
+--------------------------------------+
# It is indeed the connected SECONDARY node (GreatSQL-02)
```

**4. Check the read-only load balancing effect**
The connection is keeped without exiting, continue to create a new connection to port 6447, check **server_uuid**, you should find that the value read is the value of the `GreatSQL-03` node, because of the read load balancing mechanism of **mysqlrouter** It is automatically polled among several read-only nodes (read-only requests will not hit the PRIMARY node).

**5. How to switch failover automatic**
Next, when the PRIMARY node is shutdown or switched, **mysqlrouter** can also automatic failover.

Login to any node in the MGR cluster:
```
[root@greatsql]# mysqlsh --uri mic@172.16.16.10:3306
...
MySQL 172.16.16.10:3306 ssl JS> var mic=dba.getCluster();
MySQL 172.16.16.10:3306 ssl JS> mic.setPrimaryInstance('GreatSQL-02:3306'); <-- Switch GreatSQL-02:3306 to PRIMARY node
Setting instance'GreatSQL-02:3306' as the primary instance of cluster'GreatSQLMGR'...

Instance'GreatSQL-01:3306' was switched from PRIMARY to SECONDARY. <-- Switched, from PRIMARY to SECONDARY
Instance'GreatSQL-02:3306' was switched from SECONDARY to PRIMARY. <-- Switched, from SECONDARY to PRIMARY
Instance'GreatSQL-03:3306' remains SECONDARY. <-- remain unchanged
Instance'GreatSQL-04:3306' remains SECONDARY. <-- remain unchanged

WARNING: The cluster internal session is not the primary member anymore. For cluster management operations please obtain a fresh cluster handle using dba.getCluster().

The instance'GreatSQL-02:3306' was successfully elected as primary.
```

Go back to the previous session connected to port 6446, query **server_uuid** again, and you will find that the connection is automatically disconnected:
```
mic@GreatSQL [(none)]> select @@server_uuid;
ERROR 2013 (HY000): Lost connection to MySQL server during query
mic@GreatSQL [(none)]> select @@server_uuid;
ERROR 2006 (HY000): MySQL server has gone away
No connection. Trying to reconnect...
Connection id: 157990
Current database: *** NONE ***

+--------------------------------------+
| @@server_uuid |
+--------------------------------------+
| bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2 | <-- Confirm that server_uuid becomes the value of the GreatSQL-02 node
+--------------------------------------+
```

This enables automatic failover.

Check again the status of the MGR cluster after the switch:
```
MySQL 172.16.16.10:3306 ssl JS> mic.status();
...
        "topology": {
            "GreatSQL-01:3306": {
                "address": "GreatSQL-01:3306",
                "memberRole": "SECONDARY", <-- switch to SECONDARY node
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
            "GreatSQL-02:3306": {
                "address": "GreatSQL-02:3306",
                "memberRole": "PRIMARY", <--- new PRIMARY node
                "mode": "R/W",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
...
```

So far, using InnoDB Cluster and GreatSQL to build a set of MGR clusters that support read-write separation, read load balancing, and automatic failover is deployed.

Enjoy MGR & GreatSQL :)
