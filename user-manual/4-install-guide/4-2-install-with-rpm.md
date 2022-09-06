# RPM安装并构建MGR集群
---

本文档主要介绍如何用RPM包方式安装GreatSQL数据库，假定本次安装是在CentOS 8.x x86_64环境中安装，并且是以root用户身份执行安装操作。

在开始安装前，请根据文档 [安装准备](./4-1-install-prepare.md) 已经完成准备工作。

## 1. MGR集群规划

本次计划在3台服务器上安装GreatSQL数据库并部署MGR集群：

| node | ip | datadir | port |role|
| --- | --- | --- | --- | --- |
| GreatSQL-01 | 172.16.16.10 | /data/GreatSQL/ | 3306 | PRIMARY |
| GreatSQL-02 | 172.16.16.11 | /data/GreatSQL/ | 3306 | SECONDARY |
| GreatSQL-03 | 172.16.16.12 | /data/GreatSQL/ | 3306 | ARBITRATOR |

以下安装配置工作先在三个节点都同样操作一遍。

## 2. 下载安装包

[点击此处](https://gitee.com/GreatSQL/GreatSQL/releases/)下载最新的安装包，下载以下几个就可以：

- greatsql-client-8.0.25-16.1.el8.x86_64.rpm 
- greatsql-devel-8.0.25-16.1.el8.x86_64.rpm  
- greatsql-shared-8.0.25-16.1.el8.x86_64.rpm
- greatsql-server-8.0.25-16.1.el8.x86_64.rpm 

## 3. 安装GreatSQL RPM包

执行下面的命令安装PRM包，如果一切顺利的话，相应的过程如下所示：
```
$ rpm -ivh greatsql*rpm
Verifying...                          ################################# [100%]
Preparing...                          ################################# [100%]
Updating / installing...
   1:greatsql-shared-8.0.25-16.1.el8  ################################# [ 20%]
   2:greatsql-client-8.0.25-16.1.el8  ################################# [ 40%]
   3:greatsql-server-8.0.25-16.1.el8  ################################# [ 60%]
   4:greatsql-devel-8.0.25-16.1.el8   ################################# [ 80%]
```
这就安装成功了。

## 4. 启动前准备

### 4.1、修改 /etc/my.cnf 配置文件

[参考这份文件](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example-greatsql-8.0.25-16)，可根据实际情况修改，一般主要涉及数据库文件分区、目录，内存配置等少数几个选项。以下面这份为例：
```
#my.cnf
[client]
user = root
datadir	= /data/GreatSQL/mysql.sock

[mysqld]
user	= mysql
port	= 3306
#主从复制或MGR集群中，server_id记得要不同
#另外，实例启动时会生成 auto.cnf，里面的 server_uuid 值也要不同
#server_uuid的值还可以自己手动指定，只要符合uuid的格式标准就可以
server_id = 3306
basedir = /usr/
datadir	= /data/GreatSQL
socket	= mysql.sock
pid-file = mysql.pid
character-set-server = UTF8MB4
skip_name_resolve = 1
#若你的MySQL数据库主要运行在境外，请务必根据实际情况调整本参数
default_time_zone = "+8:00"

#performance setttings
lock_wait_timeout = 3600
open_files_limit    = 65535
back_log = 1024
max_connections = 512
max_connect_errors = 1000000
table_open_cache = 1024
table_definition_cache = 1024
thread_stack = 512K
sort_buffer_size = 4M
join_buffer_size = 4M
read_buffer_size = 8M
read_rnd_buffer_size = 4M
bulk_insert_buffer_size = 64M
thread_cache_size = 768
interactive_timeout = 600
wait_timeout = 600
tmp_table_size = 32M
max_heap_table_size = 32M

#log settings
log_timestamps = SYSTEM
log_error = error.log
log_error_verbosity = 3
slow_query_log = 1
log_slow_extra = 1
slow_query_log_file = slow.log
long_query_time = 0.1
log_queries_not_using_indexes = 1
log_throttle_queries_not_using_indexes = 60
min_examined_row_limit = 100
log_slow_admin_statements = 1
log_slow_slave_statements = 1
log_bin = binlog
binlog_format = ROW
sync_binlog = 1
binlog_cache_size = 4M
max_binlog_cache_size = 2G
max_binlog_size = 1G
binlog_rows_query_log_events = 1
binlog_expire_logs_seconds = 604800
#MySQL 8.0.22前，想启用MGR的话，需要设置binlog_checksum=NONE才行
binlog_checksum = CRC32
gtid_mode = ON
enforce_gtid_consistency = TRUE

#myisam settings
key_buffer_size = 32M
myisam_sort_buffer_size = 128M

#replication settings
relay_log_recovery = 1
slave_parallel_type = LOGICAL_CLOCK
#可以设置为逻辑CPU数量的2倍
slave_parallel_workers = 64
binlog_transaction_dependency_tracking = WRITESET
slave_preserve_commit_order = 1
slave_checkpoint_period = 2

#mgr settings
loose-plugin_load_add = 'mysql_clone.so'
loose-plugin_load_add = 'group_replication.so'
loose-group_replication_group_name = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"
#MGR本地节点IP:PORT，请自行替换
loose-group_replication_local_address = "172.16.16.10:33061"
#MGR集群所有节点IP:PORT，请自行替换
loose-group_replication_group_seeds = "172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061"
loose-group_replication_start_on_boot = OFF
loose-group_replication_bootstrap_group = OFF
loose-group_replication_exit_state_action = READ_ONLY
loose-group_replication_flow_control_mode = "DISABLED"
loose-group_replication_single_primary_mode = ON
loose-group_replication_majority_after_mode = ON
loose-group_replication_communication_max_message_size = 10M
loose-group_replication_arbitrator = 0
loose-group_replication_single_primary_fast_mode = 1
loose-group_replication_request_time_threshold = 100
loose-group_replication_primary_election_mode = GTID_FIRST
loose-group_replication_unreachable_majority_timeout = 30
loose-group_replication_member_expel_timeout = 5
loose-group_replication_autorejoin_tries = 288
report_host = "172.16.16.10"

#innodb settings
innodb_buffer_pool_size = 64G
innodb_buffer_pool_instances = 8
innodb_data_file_path = ibdata1:12M:autoextend
innodb_flush_log_at_trx_commit = 1
innodb_log_buffer_size = 32M
innodb_log_file_size = 2G
innodb_log_files_in_group = 3
innodb_max_undo_log_size = 4G
# 根据您的服务器IOPS能力适当调整
# 一般配普通SSD盘的话，可以调整到 10000 - 20000
# 配置高端PCIe SSD卡的话，则可以调整的更高，比如 50000 - 80000
innodb_io_capacity = 4000
innodb_io_capacity_max = 8000
innodb_open_files = 65535
innodb_flush_method = O_DIRECT
innodb_lru_scan_depth = 4000
innodb_lock_wait_timeout = 10
innodb_rollback_on_timeout = 1
innodb_print_all_deadlocks = 1
innodb_online_alter_log_max_size = 4G
innodb_print_ddl_logs = 1
innodb_status_file = 1
#注意: 开启 innodb_status_output & innodb_status_output_locks 后, 可能会导致log_error文件增长较快
innodb_status_output = 0
innodb_status_output_locks = 1
innodb_sort_buffer_size = 67108864

#innodb monitor settings
innodb_monitor_enable = "module_innodb"
innodb_monitor_enable = "module_server"
innodb_monitor_enable = "module_dml"
innodb_monitor_enable = "module_ddl"
innodb_monitor_enable = "module_trx"
innodb_monitor_enable = "module_os"
innodb_monitor_enable = "module_purge"
innodb_monitor_enable = "module_log"
innodb_monitor_enable = "module_lock"
innodb_monitor_enable = "module_buffer"
innodb_monitor_enable = "module_index"
innodb_monitor_enable = "module_ibuf_system"
innodb_monitor_enable = "module_buffer_page"
innodb_monitor_enable = "module_adaptive_hash"

#innodb parallel query
force_parallel_execute = OFF
parallel_default_dop = 8
parallel_max_threads = 96
temptable_max_ram = 8G

#pfs settings
performance_schema = 1
#performance_schema_instrument = '%memory%=on'
performance_schema_instrument = '%lock%=on'

```

### 4.2、新建数据库主目录，并修改权限模式及属主
```
$ mkdir -p /data/GreatSQL
$ chown -R mysql:mysql /data/GreatSQL
$ chmod -R 700 /data/GreatSQL
```

## 5. 启动GreatSQL

启动GreatSQL服务前，先修改systemd文件，调高一些limit上限，避免出现文件数、线程数不够用的告警。
```
# 在[Server]区间增加下面几行内容
$ vim /lib/systemd/system/mysqld.service
...
[Service]

# some limits
# file size
LimitFSIZE=infinity
# cpu time
LimitCPU=infinity
# virtual memory size
LimitAS=infinity
# open files
LimitNOFILE=65535
# processes/threads
LimitNPROC=65535
# locked memory
LimitMEMLOCK=infinity
# total threads (user+kernel)
TasksMax=infinity
TasksAccounting=false
...
```

保存退出，然后再执行命令重载systemd，如果没问题就不会报错：
```
$ systemctl daemon-reload
```

执行下面的命令启动GreatSQL服务
```
$ systemctl start mysqld
```

检查服务是否已启动，以及进程状态：
```
$ systemctl status mysqld
● mysqld.service - MySQL Server
   Loaded: loaded (/usr/lib/systemd/system/mysqld.service; enabled; vendor preset: disabled)
   Active: active (running) since Fri 2022-07-08 14:10:14 CST; 5min ago
     Docs: man:mysqld(8)
           http://dev.mysql.com/doc/refman/en/using-systemd.html
  Process: 51902 ExecStartPre=/usr/bin/mysqld_pre_systemd (code=exited, status=0/SUCCESS)
 Main PID: 52003 (mysqld)
   Status: "Server is operational"
    Tasks: 48 (limit: 149064)
   Memory: 5.5G
   CGroup: /system.slice/mysqld.service
           └─52003 /usr/sbin/mysqld

Jul 08 14:10:06 db170 systemd[1]: Starting MySQL Server...
Jul 08 14:10:14 db170 systemd[1]: Started MySQL Server.

$ ps -ef | grep mysqld
mysql      43653       1  3 10:35 ?        00:00:02 /usr/sbin/mysqld

$ ss -lntp | grep mysqld
LISTEN 0      70                 *:33060            *:*    users:(("mysqld",pid=43653,fd=23))
LISTEN 0      128                *:3306             *:*    users:(("mysqld",pid=43653,fd=26))

# 查看数据库文件
$ ls /data/GreatSQL
 auto.cnf          client-key.pem       '#ib_16384_14.dblwr'  '#ib_16384_6.dblwr'   ib_logfile1           mysql.pid            server-key.pem
 binlog.000001     error.log            '#ib_16384_15.dblwr'  '#ib_16384_7.dblwr'   ib_logfile2           mysql.sock           slow.log
 binlog.000002    '#ib_16384_0.dblwr'   '#ib_16384_1.dblwr'   '#ib_16384_8.dblwr'   ibtmp1                mysql.sock.lock      sys
 binlog.index     '#ib_16384_10.dblwr'  '#ib_16384_2.dblwr'   '#ib_16384_9.dblwr'   innodb_status.52003   performance_schema   undo_001
 ca-key.pem       '#ib_16384_11.dblwr'  '#ib_16384_3.dblwr'    ib_buffer_pool      '#innodb_temp'         private_key.pem      undo_002
 ca.pem           '#ib_16384_12.dblwr'  '#ib_16384_4.dblwr'    ibdata1              mysql                 public_key.pem
 client-cert.pem  '#ib_16384_13.dblwr'  '#ib_16384_5.dblwr'    ib_logfile0          mysql.ibd             server-cert.pem
```
可以看到，GreatSQL服务已经正常启动了。

顺便确认动态库 `jemalloc` 成功加载：
```
$ lsof -p 43653 | grep -i jema
mysqld  52003 mysql  mem       REG              253,0     608096   68994440 /usr/lib64/libjemalloc.so.2
```

## 6. 连接登入GreatSQL

RPM方式安装GreatSQL后，会随机生成管理员root的密码，通过搜索日志文件获取：
```
$ grep -i root /var/log/mysqld.log
2022-07-08T14:10:09.670473+08:00 6 [Note] [MY-010454] [Server] A temporary password is generated for root@localhost: ahaA(ACmw8wy
```
可以看到，root账户的密码是："ahaA(ACmw8wy" (不包含双引号)，复制到粘贴板里。

首次登入GreatSQL后，要立即修改root密码，否则无法执行其他操作，并且新密码要符合一定安全规则：
```
$ mysql -uroot -p
Enter password:     #<--这个地方粘贴上面复制的随机密码
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 8
Server version: 8.0.25-16

Copyright (c) 2021-2021 GreatDB Software Co., Ltd
Copyright (c) 2009-2021 Percona LLC and/or its affiliates
Copyright (c) 2000, 2021, Oracle and/or its affiliates.
...
Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> \s   #<--想执行一个命令，提示要先修改密码
ERROR 1820 (HY000): You must reset your password using ALTER USER statement before executing this statement.

mysql> alter user user() identified by 'GreatSQL@2022';  #<--修改密码
Query OK, 0 rows affected (0.02 sec)

mysql> \s   #<--就可以正常执行其他命令了
--------------
mysql  Ver 8.0.25-16 for Linux on x86_64 (GreatSQL (GPL), Release 16, Revision 8bb0e5af297)

Connection id:        8
Current database:
Current user:        root@localhost
SSL:            Not in use
Current pager:        stdout
Using outfile:        ''
Using delimiter:    ;
Server version:        8.0.25-16
Protocol version:    10
Connection:        Localhost via UNIX socket
Server characterset:    utf8mb4
Db     characterset:    utf8mb4
Client characterset:    utf8mb4
Conn.  characterset:    utf8mb4
UNIX socket:        /data/GreatSQL/mysql.sock
Binary data as:        Hexadecimal
Uptime:            20 min 8 sec

Threads: 2  Questions: 7  Slow queries: 0  Opens: 130  Flush tables: 3  Open tables: 46  Queries per second avg: 0.005
--------------

mysql> show databases;  #<--查看数据库列表
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
4 rows in set (0.01 sec)

mysql>
```

## 7. 关闭/重启GreatSQL

执行下面的命令关闭GreatSQL数据库。
```
$ systemctl stop mysqld
```

执行下面的命令重启GreatSQL数据库。
```
$ systemctl restart mysqld
```

GreatSQL数据库安装并初始化完毕。

## 8. 安装MySQL Shell

为了支持仲裁节点特性，需要安装GreatSQL提供的MySQL Shell发行包。打开[GreatSQL下载页面](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-16)，找到 **5. GreateSQL MySQL Shell**，下载相应的MySQL Shell安装包（目前只提供二进制安装包）。

P.S，如果暂时不想使用仲裁节点特性的话，则可以继续使用相同版本的官方MySQL Shell安装包，可以直接用YUM方式安装，此处略过。

本文场景中，选择下面的二进制包：

- greatsql-shell-8.0.25-16-Linux-glibc2.28-x86_64.tar.xz

将二进制文件包放在 `/usr/local` 目录下，解压缩：
```
$ cd /usr/local/
$ tar xf greatsql-shell-8.0.25-16-Linux-glibc2.28-x86_64.tar.xz
```

修改家目录下的profile文件，加入PATH：
```
$ vim ~/.bash_profile

...
PATH=$PATH:$HOME/bin:/usr/local/greatsql-shell-8.0.25-16-Linux-glibc2.28-x86_64/bin

export PATH
```

加载一下
```
$ source ~/.bash_profile
```

这样就可以直接执行 `mysqlsh`，而无需每次都加上全路径了。

第一次启动mysqlsh时，可能会有类似下面的提示：
```
WARNING: Found errors loading plugins, for more details look at the log at: /root/.mysqlsh/mysqlsh.log
```

执行下面的指令安装certifi这个Python模块即可：
```
$ pip3.6 install --user certifi
```

## 9. 准备构建MGR集群

在这里建议用MySQL Shell来构建MGR集群，相对于手工构建方便快捷很多，如果想要体验手工构建的同学可以参考这篇文档：[3. 安装部署MGR集群 | 深入浅出MGR](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-03.md)。

利用MySQL Shell构建MGR集群比较简单，主要有几个步骤：

1. 检查实例是否满足条件。
2. 创建并初始化一个集群。
3. 逐个添加实例。

接下来一步步执行。

### 9.1、MGR节点预检查

用管理员账号 root 连接到第一个节点：
```
#在本地通过socket方式登入
$ mysqlsh -S/data/GreatSQL/mysql.sock root@localhost
Please provide the password for 'root@.%2Fmysql.sock': ********  <-- 输入root密码
Save password for 'root@.%2Fmysql.sock'? [Y]es/[N]o/Ne[v]er (default No): yes  <-- 提示是否存储密码（视各公司安全规则而定，这里为了方便选择了存储密码）
MySQL Shell 8.0.25
...
Server version: 8.0.25-16 GreatSQL (GPL), Release 16, Revision 8bb0e5af297
No default schema selected; type \use <schema> to set one.
WARNING: Found errors loading plugins, for more details look at the log at: /root/.mysqlsh/mysqlsh.log
 MySQL  localhost  Py >
```

接下来，执行 `dba.configure_instance`命令开始检查当前实例是否准备好了，可以作为MGR集群的一个节点：
```
# 开始配置MGR节点
MySQL  172.16.16.10:3306 ssl  Py > dba.configure_instance();
Configuring local MySQL instance listening at port 3306 for use in an InnoDB cluster...

This instance reports its own address as GreatSQL-01:3306
Clients and other cluster members will communicate with it through this address by default. If this is not correct, the report_host MySQL system variable should be changed.

# 提示root账号不能运行MGR服务，需要创建新的专用账号
ERROR: User 'root' can only connect from 'localhost'. New account(s) with proper source address specification to allow remote connection from all instances must be created to manage the cluster.

1) Create remotely usable account for 'root' with same grants and password
2) Create a new admin account for InnoDB cluster with minimal required grants
3) Ignore and continue
4) Cancel

Please select an option [1]: 2  #<-- 选择创建最小权限账号
Please provide an account name (e.g: icroot@%) to have it created with the necessary
privileges or leave empty and press Enter to cancel.
Account Name: GreatSQL  <-- 输入账号名
Password for new account: *******  <-- 输入密码***
Confirm password: *******  <-- 再次确认密码

#节点初始化完毕
The instance 'GreatSQL-01:3306' is valid to be used in an InnoDB cluster.

#MGR管理账号创建完毕
Cluster admin user 'GreatSQL'@'%' created.
The instance 'GreatSQL-01:3306' is already ready to be used in an InnoDB cluster.      
```
这里切换到MySQL Shell的Python风格下了，如果是Javascript风格的话，则函数名是dba.configureInstance()。

GreatSQL提供的MySQL Shell二进制包不支持Javascript语法，因为编译时没有libv8库，所以只能支持Python/SQL语法。

**截止到这里，以上所有步骤在另外两个节点 GreatSQL-02、GreatSQL-03 也同样执行一遍。**

### 9.2、创建并初始化一个集群

在正式初始化MGR集群前，再次提醒要先再其他节点完成上述初始化工作。

上述另外两个节点也初始化完毕后，利用mysqlsh客户端，指定新建MGR的管理账号**GreatSQL**登入PRIMARY节点，准备创建MGR集群：
```
$ mysqlsh --uri GreatSQL@172.16.16.10:3306
Please provide the password for 'GreatSQL@127.0.0.1:3306': *************
Save password for 'GreatSQL@127.0.0.1:3306'? [Y]es/[N]o/Ne[v]er (default No): yes
MySQL Shell 8.0.25
...
Server version: 8.0.25-16 GreatSQL (GPL), Release 16, Revision 8bb0e5af297
No default schema selected; type \use <schema> to set one.

# 选定GreatSQL-01节点作为PRIMARY，开始创建MGR集群
# 集群命名为 GreatSQLMGR，后面mysqlrouter读取元数据时用得上
MySQL  172.16.16.10:3306 ssl  Py > c = dba.create_cluster('GreatSQLMGR');
A new InnoDB cluster will be created on instance '172.16.16.10:3306'.

Validating instance configuration at 172.16.16.10:3306...

This instance reports its own address as GreatSQL-01:3306

Instance configuration is suitable.
NOTE: Group Replication will communicate with other members using 'GreatSQL-01:33061'. Use the localAddress option to override.

Creating InnoDB cluster 'GreatSQLMGR' on 'GreatSQL-01:3306'...

Adding Seed Instance...
Cluster successfully created. Use Cluster.add_instance() to add MySQL instances.
At least 3 instances are needed for the cluster to be able to withstand up to
one server failure.
MySQL  172.16.16.10:3306 ssl  Py > 
```
集群已经创建并初始化完毕，接下来就是继续添加其他节点了。

### 9.3、逐个添加实例

可以在GreatSQL-01（PRIMARY）节点上直接添加其他节点，也可以用mysqlsh客户端登入其他节点执行添加节点操作。这里采用前者：
```
# 此时mysqlsh客户端还保持连接到GreatSQL-01节点
# 可以直接添加GreatSQL-02节点
MySQL  172.16.16.10:3306 ssl  Py > c.add_instance('GreatSQL@172.16.16.11:3306');  <-- 添加GreatSQL-02节点
NOTE: The target instance 'GreatSQL-02:3306' has not been pre-provisioned (GTID set is empty). The Shell is unable to decide whether incremental state recovery can correctly provision it.
The safest and most convenient way to provision a new instance is through automatic clone provisioning, which will completely overwrite the state of 'GreatSQL-02:3306' with a physical snapshot from an existing cluster member. To use this method by default, set the 'recoveryMethod' option to 'clone'.

The incremental state recovery may be safely used if you are sure all updates ever executed in the cluster were done with GTIDs enabled, there are no purged transactions and the new instance contains the same GTID set as the cluster or a subset of it. To use this method by default, set the 'recoveryMethod' option to 'incremental'.

# 选择恢复模式：克隆/增量恢复/忽略，默认选择克隆
Please select a recovery method [C]lone/[I]ncremental recovery/[A]bort (default Clone):
Validating instance configuration at 172.16.16.11:3306...

This instance reports its own address as GreatSQL-02:3306

Instance configuration is suitable.
NOTE: Group Replication will communicate with other members using 'GreatSQL-02:33061'. Use the localAddress option to override.

A new instance will be added to the InnoDB cluster. Depending on the amount of
data on the cluster this might take from a few seconds to several hours.

Adding instance to the cluster...

Monitoring recovery process of the new cluster member. Press ^C to stop monitoring and let it continue in background.
Clone based state recovery is now in progress.

# 提示在这个过程中需要重启GreatSQL-02节点实例
# 如果无法自动重启，需要手动重启
NOTE: A server restart is expected to happen as part of the clone process. If the
server does not support the RESTART command or does not come back after a
while, you may need to manually start it back.

* Waiting for clone to finish...
# 从GreatSQL-01节点克隆数据
NOTE: GreatSQL-02:3306 is being cloned from GreatSQL-01:3306
** Stage DROP DATA: Completed
** Clone Transfer
    FILE COPY  ############################################################  100%  Completed
    PAGE COPY  ############################################################  100%  Completed
    REDO COPY  ############################################################  100%  Completed
    NOTE: GreatSQL-02:3306 is shutting down...

* Waiting for server restart... \   <-- 重启中
* Waiting for server restart... ready   <-- 重启完毕，如果没有加入systemed，则需要自己手工启动
* GreatSQL-02:3306 has restarted, waiting for clone to finish...
** Stage RESTART: Completed
* Clone process has finished: 59.62 MB transferred in about 1 second (~59.62 MB/s)

State recovery already finished for 'GreatSQL-02:3306'

# 新节点 GreatSQL-02:3306 已加入集群
The instance 'GreatSQL-02:3306' was successfully added to the cluster.
```
这就将 GreatSQL-02 节点加入MGRT集群中了，此时可以先查看下集群状态。

```
MySQL  172.16.16.10:3306 ssl  Py > c.status()
{
    "clusterName": "GreatSQLMGR",
    "defaultReplicaSet": {
        "name": "default",
        "primary": "172.16.16.10:3306",
        "ssl": "REQUIRED",
        "status": "OK_NO_TOLERANCE",
        "statusText": "Cluster is NOT tolerant to any failures.",
        "topology": {
            "172.16.16.10:3306": {
                "address": "172.16.16.10:3306",
                "memberRole": "PRIMARY",
                "mode": "R/W",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.25"
            },
            "172.16.16.11:3306": {
                "address": "172.16.16.11:3306",
                "memberRole": "SECONDARY",
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.25"
            }
        },
        "topologyMode": "Single-Primary"
    },
    "groupInformationSourceMember": "172.16.16.10:3306"
}
```
可以看到，一个包含两节点的MGR集群已经构建好了，Primary节点是 *172.16.16.10:3306*，接下来还要加入另一个节点：**仲裁节点**。

如果不想体验仲裁节点特性的话，可以照着上面操作再次正常加入 GreatSQL-03 节点作为 Secondary 节点即可，到这里就可以结束MGR集群构建工作了。

### 9.4、添加仲裁节点

编辑 GreatSQL-03 节点上的 `/etc/my.cnf` 配置文件，加入/修改下面这行内容：
```
loose-group_replication_arbitrator = 1
```
其作用就是指定该节点作为**仲裁节点**，保存退出，重启该节点GreatSQL数据库。

然后照着第三步的操作，调用 `dba.add_instance()` 添加新节点，就可以直接将仲裁节点加入MGR集群了，再次查看集群状态：
```
MySQL  172.16.16.10:3306 ssl  Py > c.status()
{
    "clusterName": "GreatSQLMGR",
    "defaultReplicaSet": {
        "name": "default",
        "primary": "172.16.16.10:3306",
        "ssl": "REQUIRED",
        "status": "OK",
        "statusText": "Cluster is ONLINE and can tolerate up to ONE failure.",
        "topology": {
            "172.16.16.10:3306": {
                "address": "172.16.16.10:3306",
                "memberRole": "PRIMARY",
                "mode": "R/W",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.25"
            },
            "172.16.16.11:3306": {
                "address": "172.16.16.11:3306",
                "memberRole": "SECONDARY",
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.25"
            },
            "172.16.16.12:3306": {
                "address": "172.16.16.12:3306",
                "memberRole": "ARBITRATOR",
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.25"
            }
        },
        "topologyMode": "Single-Primary"
    },
    "groupInformationSourceMember": "172.16.16.10:3306"
}
```
可以看到一个包含仲裁节点的三节点MGR集群已经构建完毕。

在后面的内容中，我们再介绍如何手工方式部署MGR集群，以及利用MySQL Router实现读写分离及读可扩展。

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
