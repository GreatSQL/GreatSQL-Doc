# 一文掌握GreatSQL MGR集群的部署和运维

[toc]

本文详细介绍如何在单机环境下，利用GreatSQL构建一个3节点的MGR集群，并用mysqld_multi进行管理（ 也建议采用systemd来管理GreatSQL多实例服务，参考：[利用systemd管理MySQL单机多实例](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/build-multi-instance-with-systemd.md) ）。

为了简单起见，这个MGR集群采用单主（single-primary）模式，不采用多主（multi-primary）模式。

构建完MGR集群后，再添加一个新节点，以及模拟进行滚动升级和切主等其他操作。

除了MySQL官方社区版本外，如果想体验更可靠、稳定、高效的MGR，推荐使用GreatSQL版本。本文采用GreatSQL 8.0.22版本，关于这个版本的说明详见 [GreatSQL，打造更好的MGR生态](https://mp.weixin.qq.com/s/ByAjPOwHIwEPFtwC5jA28Q)。

P.S，单机模式下，如果要部署多实例并构建MGR集群，要注意避免TCP self-connect的问题，详见 [bug#98151](https://bugs.mysql.com/bug.php?id=98151)，如果采用GreatSQL版本就没这个问题了。

### 1. 运行环境

GreatSQL二进制包放在 /usr/local/ 下，即 `basedir = /usr/local/GreatSQL-8.0.22`。

三个实例按下面规划分配：

| 实例 | 端口 | datadir |
|--- | --- | ---
| GreatSQL-01 | 3306 | /data/GreatSQL/mgr01/
| GreatSQL-02 | 3307 | /data/GreatSQL/mgr02/
| GreatSQL-03 | 3308 | /data/GreatSQL/mgr03/

![输入图片说明](https://images.gitee.com/uploads/images/2021/0623/171734_e00636c7_8779455.png "屏幕截图.png")


### 2、准备my.cnf配置文件
```
[mysqld]
basedir=/usr/local/GreatSQL-8.0.22
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
slave_parallel_workers=128 #可以设置为逻辑CPU数量的2-4倍
sql_require_primary_key=1
slave_preserve_commit_order=1
slave_checkpoint_period=2

#mgr
loose-plugin_load_add='mysql_clone.so'
loose-plugin_load_add='group_replication.so'

#所有节点的group_replication_group_name值必须相同
#这是一个标准的UUID格式，可以手动指定，也可以用随机生成的UUID
loose-group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"

#指定MGR集群各节点的IP+端口，这个端口是专用于MGR的，不是平常所说的mysqld实例端口
#如果是在多节点上部署MGR集群时，要注意这个端口是否会被防火墙拦截
loose-group_replication_group_seeds= "127.0.0.1:33061,127.0.0.1:33071,127.0.0.1:33081"

#不建议启动mysqld的同时也启动MGR服务
loose-group_replication_start_on_boot=off

#默认不要作为MGR集群引导节点，有需要时再手动执行并立即改回OFF状态
loose-group_replication_bootstrap_group=off

#当退出MGR后，把该实例设置为read_only，避免误操作写入数据
loose-group_replication_exit_state_action=READ_ONLY

#一般没什么必要开启流控机制
loose-group_replication_flow_control_mode = "DISABLED"

#【强烈】建议只用单主模式，如果是实验目的，可以尝试玩玩多主模式
loose-group_replication_single_primary_mode=ON

[mysqld_multi]
mysqld = /usr/local/GreatSQL-8.0.22/bin/mysqld
log = /data/GreatSQL/mysqld_multi.log
mysqladmin = /usr/local/GreatSQL-8.0.22/bin/mysqladmin
user=root

[mysqld3306]
datadir=/data/GreatSQL/mgr01
socket=/data/GreatSQL/mgr01/mysql.sock
port=3306
server_id=3306
log-error=/data/GreatSQL/mgr01/error.log
#指定本节点的IP+端口
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

在这份配置文件中，`[mysqld]` 这部分内容是所有实例都会读取应用的，而在 `[mysqld3306]` 这部分配置，才是 3306 端口这个实例所独有的。

在构建MGR集群中，要保证集群各节点的 `group_replication_group_name` 选项值一样才行，否则就是不同的集群了。 

另外，如果有防火墙的话，注意要开放各端口间的访问规则，否则无法启动MGR。

### 3、初始化MySQL实例
先手动创建相应的datadir，并修改目录属主为mysql用户：
```
[root@greatsql]# mkdir -p /data/GreatSQL/{mgr01,mgr02,mgr03}
[root@greatsql]# chown -R mysql.mysql /data/GreatSQL
```

执行下面的命令进行MySQL实例初始化，会自动创建InnoDB系统表空间、redo log、undo log的文件：
```
[root@greatsql]# /usr/local/GreatSQL-8.0.22/bin/mysqld --no-defaults --datadir=/data/GreatSQL/mgr01 --initialize --user=mysql

[System] [MY-013169] [Server] /usr/local/GreatSQL-8.0.22/bin/mysqld (mysqld 8.0.22-13) initializing of server in progress as process 18688
[System] [MY-013576] [InnoDB] InnoDB initialization has started.
[System] [MY-013577] [InnoDB] InnoDB initialization has ended.
[Note] [MY-010454] [Server] A temporary password is generated for root@localhost: h<GL%Lr:v66W
```
可以看到，在输出的日志中打印了root账号的临时密码（最后一行），启动mysqld实例后，首次用这个密码登入，就要立即进行修改，否则其他什么也做不了：

用同样的方法，也分别完成mgr02、mgr03的初始化。

接下来，分别启动三个mysqld实例：
```
[root@greatsql]# /usr/local/GreatSQL-8.0.22/bin/mysqld_multi start 3306
[root@greatsql]# /usr/local/GreatSQL-8.0.22/bin/mysqld_multi start 3307
[root@greatsql]# /usr/local/GreatSQL-8.0.22/bin/mysqld_multi start 3308
```

能看到datadir下的文件目录大概像这样的：
```
-rw-r----- 1 mysql mysql       56 Jun  4 10:44 auto.cnf
-rw-r----- 1 mysql mysql      401 Jun  4 10:46 binlog.000001
-rw-r----- 1 mysql mysql       16 Jun  4 10:46 binlog.index
-rw------- 1 mysql mysql     1676 Jun  4 10:44 ca-key.pem
-rw-r--r-- 1 mysql mysql     1120 Jun  4 10:44 ca.pem
-rw-r--r-- 1 mysql mysql     1120 Jun  4 10:44 client-cert.pem
-rw------- 1 mysql mysql     1680 Jun  4 10:44 client-key.pem
-rw-r----- 1 mysql mysql     8800 Jun  4 10:46 error.log
-rw-r----- 1 mysql mysql   196608 Jun  4 10:48 #ib_16384_0.dblwr
-rw-r----- 1 mysql mysql  8585216 Jun  4 10:44 #ib_16384_1.dblwr
-rw-r----- 1 mysql mysql     6274 Jun  4 10:44 ib_buffer_pool
-rw-r----- 1 mysql mysql 12582912 Jun  4 10:46 ibdata1
-rw-r----- 1 mysql mysql 50331648 Jun  4 10:48 ib_logfile0
-rw-r----- 1 mysql mysql 50331648 Jun  4 10:44 ib_logfile1
-rw-r----- 1 mysql mysql 12582912 Jun  4 10:46 ibtmp1
drwxr-x--- 2 mysql mysql      168 Jun  4 10:46 #innodb_temp
drwxr-x--- 2 mysql mysql      143 Jun  4 10:44 mysql
-rw-r----- 1 mysql mysql 25165824 Jun  4 10:46 mysql.ibd
srwxrwxrwx 1 mysql mysql        0 Jun  4 10:46 mysql.sock
-rw------- 1 mysql mysql        6 Jun  4 10:46 mysql.sock.lock
drwxr-x--- 2 mysql mysql     8192 Jun  4 10:46 performance_schema
-rw------- 1 mysql mysql     1680 Jun  4 10:44 private_key.pem
-rw-r--r-- 1 mysql mysql      452 Jun  4 10:44 public_key.pem
-rw-r--r-- 1 mysql mysql     1120 Jun  4 10:44 server-cert.pem
-rw------- 1 mysql mysql     1676 Jun  4 10:44 server-key.pem
drwxr-x--- 2 mysql mysql       28 Jun  4 10:44 sys
-rw-r----- 1 mysql mysql 10485760 Jun  4 10:48 undo_001
-rw-r----- 1 mysql mysql 10485760 Jun  4 10:46 undo_002
-rw-r----- 1 mysql mysql        6 Jun  4 10:46 greatsql.pid
```

### 4、构建MGR集群
#### 4.1 构建MGR集群前的准备工作
因为在配置文件中已经指定了要加载 `group_replication` 和 `mysql_clone` 两个 plugin，如无意外，应该都已经加载成功：
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
看到确实已经加载了。

如果没有被正确加载，就需要查看日志文件确认什么原因无法加载。

也可以尝试手动加载这两个plugin：
```
[root@GreatSQL][(3306)]> INSTALL PLUGIN group_replication SONAME 'group_replication.so';
[root@GreatSQL][(3306)]> INSTALL PLUGIN clone SONAME 'mysql_clone.so';
```

`clone plugin` 的作用后面再介绍。

#### 4.2 配置MGR集群PRIMARY节点
接下来创建MGR所需要的账户，并授权：
```
[root@GreatSQL][(3306)]> CREATE USER repl@'%' IDENTIFIED WITH MYSQL_NATIVE_PASSWORD BY 'repl';
[root@GreatSQL][(3306)]> GRANT REPLICATION SLAVE, BACKUP_ADMIN ON *.* TO `repl`@`%`;
```

因为是一个刚初始化的干净系统，也为了简单起见，执行下面的命令再重置一下：
```
[root@GreatSQL][(3306)]> reset master; reset slave all;
```
【提醒】**生产环境中请勿这么做**。后面会有其他文章介绍如何对已上线的MGR集群再加入新的节点。

创建MGR复制通道：
```
[root@GreatSQL][(3306)]> CHANGE MASTER TO MASTER_USER='repl', MASTER_PASSWORD='repl' FOR CHANNEL 'group_replication_recovery';
```

上述所有操作，在其他几个节点上都重复执行一遍。

接着，【重要的一步】来了，登入被选中作为 **PRIMARY** 节点的mgr01实例，执行下面的命令：
```
[root@GreatSQL][(3306)]> set global group_replication_bootstrap_group=ON;
```
这个命令的作用是在MGR集群的PRIMARY节点第一次被启动时，用于引导MGR集群的。

在其他节点启动时，记住【不要】将选项 `group_replication_bootstrap_group` 设置为ON，否则会独立拉起一个新的MGR集群。

之后就可以在MGR集群的 **PRIMARY** 节点上启动组复制线程了：
```
[root@GreatSQL][(3306)]> start group_replication;
Query OK, 0 rows affected (2.14 sec)

[root@GreatSQL][(3306)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            |  MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 0fbb2cfd-c4d9-11eb-8747-525400e2078a | greatsql-mgr |        3306 | ONLINE       | PRIMARY     | 8.0.22         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
此时可以看到MGR集群已启动，且只有PRIMARY节点。

集群启动后，记得立即将该选项重置为 OFF。
```
[root@GreatSQL][(3306)]> set global group_replication_bootstrap_group=OFF;
```

接下来在mgr02、mgr03节点上也执行 `start group_replication` 启动MGR服务，【记得要设置 】`group_replication_bootstrap_group=OFF`。

#### 4.3 查看MGR集群状态
所有实例都启动MGR服务后，再次查看集群状态：
```
[root@GreatSQL][(3308)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            |  MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 0fbb2cfd-c4d9-11eb-8747-525400e2078a | greatsql-mgr |        3306 | ONLINE       | PRIMARY     | 8.0.22         |
| group_replication_applier | 1778e87a-c4d9-11eb-bf33-525400e2078a | greatsql-mgr |        3307 | ONLINE       | SECONDARY   | 8.0.22         |
| group_replication_applier | 1c8ebfa6-c4d9-11eb-80d1-525400e2078a | greatsql-mgr |        3308 | ONLINE       | SECONDARY   | 8.0.22         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
因为是在同一个主机上启动多实例构建的MGR，所以 **MEMBER_HOST** 的值是一样的。

一个在单机上由三个实例组成的MGR集群构建完毕。

#### 4.4 测试数据读写
在MGR集群运行过程中，**只有PRIMARY节点上允许同时读写数据，其他节点只能只读数据，不能写入**。

在PRIMARY节点上，创建新的库表并写入几行数据：
```
[root@GreatSQL][(3306)]> create database greatsql;
[root@GreatSQL][(3306)]> use greatsql;
[root@GreatSQL][(3306)][greatsql]> create table t1(id int primary key);
[root@GreatSQL][(3306)][greatsql]> insert into t1 values (rand()*1024), (rand()*1024), (rand()*1024);
Query OK, 3 rows affected (0.01 sec)
Records: 3  Duplicates: 0  Warnings: 0

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

在另外两个节点上查看数据：
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
可以读取到刚新写入的数据。

再次查看MGR的applier线程工作状态：
```
[root@GreatSQL][(3306)]> select * from performance_schema.replication_connection_status where channel_name = 'group_replication_applier'\G
*************************** 1. row ***************************
                                      CHANNEL_NAME: group_replication_applier
                                        GROUP_NAME: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1
                                       SOURCE_UUID: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1
                                         THREAD_ID: NULL
                                     SERVICE_STATE: ON   <---状态为ON，正常
                         COUNT_RECEIVED_HEARTBEATS: 0
                          LAST_HEARTBEAT_TIMESTAMP: 0000-00-00 00:00:00.000000
                          RECEIVED_TRANSACTION_SET: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1:1-19  <--- GTID在持续变化
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

以及查看复制组各成员的状态：
```
[root@GreatSQL][(3306)]> select * from performance_schema.replication_group_member_stats\G
*************************** 1. row ***************************
                              CHANNEL_NAME: group_replication_applier
                                   VIEW_ID: 16227931944218245:4
                                 MEMBER_ID: 0fbb2cfd-c4d9-11eb-8747-525400e2078a
               COUNT_TRANSACTIONS_IN_QUEUE: 0   <--- 等待冲突检测的事务队列大小
                COUNT_TRANSACTIONS_CHECKED: 0
                  COUNT_CONFLICTS_DETECTED: 0
        COUNT_TRANSACTIONS_ROWS_VALIDATING: 0
        TRANSACTIONS_COMMITTED_ALL_MEMBERS: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1:1-19
            LAST_CONFLICT_FREE_TRANSACTION:
COUNT_TRANSACTIONS_REMOTE_IN_APPLIER_QUEUE: 0   <--- 本地等待apply的事务队列大小
         COUNT_TRANSACTIONS_REMOTE_APPLIED: 3
         COUNT_TRANSACTIONS_LOCAL_PROPOSED: 0
         COUNT_TRANSACTIONS_LOCAL_ROLLBACK: 0
         ...
```

### 5、进一步，再增加一个新节点
如果想对MGR集群扩展读性能，可以增加新的SECONDARY节点。

按照前面的方法，先初始化一个新的实例 mgr04，它运行的端口是 3309。然后利用 **clone plugin**（主从节点都必须要启用clone plugin） 从现有其他节点复制数据过来，再加入MGR集群。

运行clone复制数据需要 `BACKUP_ADMIN` 权限（复制源、目标两个节点都需要），前面已经授予了。

首先，设置clone donor节点：
```
# 尽量从SECONDARY节点复制数据，不从PRIMARY节点复制
[root@GreatSQL][(3309)]> set global clone_valid_donor_list='127.0.0.1:3307';
```

开始复制数据：
```
[root@GreatSQL][(3309)]> clone instance from repl@127.0.0.1:3307 identified by 'repl';

#clone结束后，会自动重启mysqld实例
#但因为该实例没有用systemd服务管理起来，所以需要手动启动进程
ERROR 3707 (HY000): Restart server failed (mysqld is not managed by supervisor process).
```

再次启动3309端口实例，登入查询，就能看到从其他节点复制过来的数据了：
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

在mgr04实例上启动MGR服务：
```
[root@GreatSQL][(3309)]> start group_replication;
Query OK, 0 rows affected (2.85 sec)

[root@GreatSQL][(3309)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            |  MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 0fbb2cfd-c4d9-11eb-8747-525400e2078a | greatsql-mgr |        3306 | ONLINE       | PRIMARY     | 8.0.22         |
| group_replication_applier | 1778e87a-c4d9-11eb-bf33-525400e2078a | greatsql-mgr |        3307 | ONLINE       | SECONDARY   | 8.0.22         |
| group_replication_applier | 1c8ebfa6-c4d9-11eb-80d1-525400e2078a | greatsql-mgr |        3308 | ONLINE       | SECONDARY   | 8.0.22         |
| group_replication_applier | bc037d6c-c4de-11eb-a5b8-525400e2078a | greatsql-mgr |        3309 | ONLINE       | SECONDARY   | 8.0.22         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
可以看到，新节点加入成功了。

![输入图片说明](https://images.gitee.com/uploads/images/2021/0623/171805_392264ca_8779455.png "屏幕截图.png")


### 6、再进一步，切换主节点
如果需要升级MGR集群中各节点的MySQL版本，则可以进行**滚动升级**。

即**先升级完全部SECONDARY节点，再将PRIMARY节点停掉下线，最后升级**，MGR集群会自动选择其他已升级完的节点作为新的PRIMARY节点，等到原来的PRIMARY节点也升级完后再加入 回来即可，这就完成整个集群所有节点的升级工作了。

#### 6.1 先升级SECONDARY节点
现在要升级mgr4节点的MySQL版本，需要先停掉MGR服务：
```
[root@GreatSQL][(3309)]> stop group_replication;
```

再停掉mysqld进程后，在my.cnf中增加一行配置：
```
upgrade=AUTO
```

替换/指定新的MySQL二进制程序文件（相同大版本，只有相近几个小版本的差异时可以这么做），再次启动mysqld进程，即可实现自动升级。

这是MySQL 8.0.16之后的升级新方法，在8.0.16之前，需要手动执行 `mysql_upgrade` 二进制程序进行升级。

启动过程中，能看到类似下面的日志：
```
[System] [MY-013381] [Server] Server upgrade from '80022' to '80025' started.
[Note] [MY-013386] [Server] Running queries to upgrade MySQL server.
[Note] [MY-013387] [Server] Upgrading system table data.
[Note] [MY-013385] [Server] Upgrading the sys schema.
```

之后再启动MGR服务，就能看到各节点的MySQL版本不同了。
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
如上图所示，只剩下mgr01节点还没升级。

从MySQL 8.0.16开始，新增MGR协议要求，比如使用相同的通信协议版本才能组成MGR集群，而8.0.22和8.0.25是相同的，所以可以在同一个集群里。
```
#在mgr01上执行
[root@GreatSQL][(3306)]> select version(), group_replication_get_communication_protocol();
+-----------+------------------------------------------------+
| version() | group_replication_get_communication_protocol() |
+-----------+------------------------------------------------+
| 8.0.22-13 | 8.0.16                                         |
+-----------+------------------------------------------------+

#在mgr04上执行
[root@GreatSQL][(3309)]> select version(), group_replication_get_communication_protocol();
+-----------+------------------------------------------------+
| version() | group_replication_get_communication_protocol() |
+-----------+------------------------------------------------+
| 8.0.25    | 8.0.16                                         |
+-----------+------------------------------------------------+
```
#### 6.2 再升级PRIMARY节点
现在关闭mgr01节点后，剩下的三个节点会完成自动选主：
```
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            |  MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 1778e87a-c4d9-11eb-bf33-525400e2078a | greatsql-mgr |        3307 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | 1c8ebfa6-c4d9-11eb-80d1-525400e2078a | greatsql-mgr |        3308 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | bc037d6c-c4de-11eb-a5b8-525400e2078a | greatsql-mgr |        3309 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
自动选择了 mgr02 节点作为新的PRIMARY节点（未设定各节点权重值时，则按照 `MEMBER_ID` 的顺序依次选主）。

待到mgr01节点也完成升级，重新加回集群后：
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
![输入图片说明](https://images.gitee.com/uploads/images/2021/0623/171824_2bc1e254_8779455.png "屏幕截图.png")

#### 6.3 手动切换PRIMARY节点
此时，还是选择mgr02作为PRIMARY节点，不会发生变化，除非手动执行切主操作：
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
这就完成滚动升级以及再次切主的全部操作了。

至此，MGR集群的构建、添加新节点、滚动升级、切主等操作都已完成。

在单机多节点构建MGR集群，和在多机上的构建过程并无本质区别，大家可以自行操作一遍。
