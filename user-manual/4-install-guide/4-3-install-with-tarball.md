# 二进制包安装并构建MGR集群
---

本文档主要介绍如何用二进制包方式安装GreatSQL数据库，假定本次安装是在CentOS 8.x x86_64环境中安装，并且是以root用户身份执行安装操作。

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

- GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64.tar.xz

将下载的二进制包放到安装目录下，并解压缩：
```
$ cd /usr/local
$ curl -o GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64.tar.xz https://product.greatdb.com/GreatSQL-8.0.25-16/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64.tar.xz
$ tar xf GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64.tar.xz
```

## 3. 启动前准备

### 3.1 修改 /etc/my.cnf 配置文件

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
basedir = /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64
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

### 3.2 新建mysql用户
```
$ /sbin/groupadd mysql
$ /sbin/useradd -g mysql mysql -d /dev/null -s /sbin/nologin
```

### 3.3 新建数据库主目录，并修改权限模式及属主
```
$ mkdir -p /data/GreatSQL
$ chown -R mysql:mysql /data/GreatSQL
$ chmod -R 700 /data/GreatSQL
```

### 3.4 增加GreatSQL系统服务
```
$ vim /lib/systemd/system/greatsql.service

[Unit]
Description=GreatSQL Server
Documentation=man:mysqld(8)
Documentation=http://dev.mysql.com/doc/refman/en/using-systemd.html
After=network.target
After=syslog.target
[Install]
WantedBy=multi-user.target
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

User=mysql
Group=mysql
Type=simple
TimeoutSec=0
PermissionsStartOnly=true
ExecStartPre=/usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld_pre_systemd
ExecStart=/usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld $MYSQLD_OPTS
EnvironmentFile=-/etc/sysconfig/mysql
LimitNOFILE = 10000
Restart=on-failure
RestartPreventExitStatus=1
Environment=MYSQLD_PARENT_PID=1
PrivateTmp=false
```
务必确认文件中目录及文件名是否正确。

执行命令重载systemd，加入 `greatsql` 服务，如果没问题就不会报错：
```
$ systemctl daemon-reload
```

这就安装成功并将GreatSQL添加到系统服务中，后面可以用 `systemctl` 来管理GreatSQL服务。

### 3.5 下载mysqld_pre_systemd文件

GreatSQL二进制包中没有自带 `mysqld_pre_systemd` 脚本文件，需要自行下载。

点击[本链接](https://gitee.com/GreatSQL/GreatSQL-Ansible/blob/master/mysql-support-files/mysqld_pre_systemd) 复制脚本内容，并保存成文件 `/usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld_pre_systemd`，确认第25行附近 `MYSQL_BASEDIR` 所指的路径是否正确：
```
MYSQL_BASEDIR = /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64
```

之后修改文件属性，加上可执行权限：
```
$ chmod ug+x /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld_pre_systemd
```

## 4. 启动GreatSQL

执行下面的命令启动GreatSQL服务
```
$ systemctl start greatsql
```

检查服务是否已启动，以及进程状态：
```
$ systemctl status greatsql
● greatsql.service - GreatSQL Server
   Loaded: loaded (/usr/lib/systemd/system/greatsql.service; disabled; vendor preset: disabled)
   Active: active (running) since Tue 2022-07-12 10:08:06 CST; 6min ago
     Docs: man:mysqld(8)
           http://dev.mysql.com/doc/refman/en/using-systemd.html
  Process: 60129 ExecStartPre=/usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld_pre_systemd (code=exited, status=0/SUCCESS)
 Main PID: 60231 (mysqld)
   Status: "Server is operational"
    Tasks: 49 (limit: 149064)
   Memory: 5.6G
   CGroup: /system.slice/greatsql.service
           └─60231 /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld

Jul 12 10:07:58 db170 systemd[1]: Starting GreatSQL Server...
Jul 12 10:08:06 db170 systemd[1]: Started GreatSQL Server.

$ ps -ef | grep mysqld
mysql      60231       1  2 10:08 ?        00:00:10 /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld

$ ss -lntp | grep mysqld
LISTEN 0      70                 *:33060            *:*    users:(("mysqld",pid=60231,fd=38))
LISTEN 0      128                *:3306             *:*    users:(("mysqld",pid=60231,fd=43))

# 查看数据库文件
$ ls /data/GreatSQL
 auto.cnf          client-key.pem       '#ib_16384_14.dblwr'  '#ib_16384_6.dblwr'   ib_logfile1           mysql.pid            server-key.pem
 binlog.000001     error.log            '#ib_16384_15.dblwr'  '#ib_16384_7.dblwr'   ib_logfile2           mysql.sock           slow.log
 binlog.000002    '#ib_16384_0.dblwr'   '#ib_16384_1.dblwr'   '#ib_16384_8.dblwr'   ibtmp1                mysql.sock.lock      sys
 binlog.index     '#ib_16384_10.dblwr'  '#ib_16384_2.dblwr'   '#ib_16384_9.dblwr'   innodb_status.60231   performance_schema   undo_001
 ca-key.pem       '#ib_16384_11.dblwr'  '#ib_16384_3.dblwr'    ib_buffer_pool      '#innodb_temp'         private_key.pem      undo_002
 ca.pem           '#ib_16384_12.dblwr'  '#ib_16384_4.dblwr'    ibdata1              mysql                 public_key.pem
 client-cert.pem  '#ib_16384_13.dblwr'  '#ib_16384_5.dblwr'    ib_logfile0          mysql.ibd             server-cert.pem
```
可以看到，GreatSQL服务已经正常启动了。


## 5. 连接登入GreatSQL

二进制包方式安装GreatSQL后，初始化的root密码是空的，可以直接登入并修改成安全密码：
```
$ mysql -uroot 
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 11
Server version: 8.0.25-16 GreatSQL, Release 16, Revision 8bb0e5af297
...
Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> alter user user() identified by 'GreatSQL@2022';  #<--修改密码
Query OK, 0 rows affected (0.02 sec)

mysql> \s
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

Threads: 2  Questions: 19  Slow queries: 0  Opens: 137  Flush tables: 3  Open tables: 53  Queries per second avg: 0.020
--------------
```
GreatSQL数据库安装并初始化完毕。

接下来安装MySQL Shell，以及进行MGR初始化等操作和用RPM包方式安装一样，这里就不赘述了。

参考文档[RPM安装并构建MGR集群](./4-2-install-with-rpm.md#安装mysql-shell)，从“”这节开始及往后内容即可。


**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
