# RPM安装
---

本文档主要介绍如何用RPM包方式安装GreatSQL数据库，假定本次安装是在CentOS 8.x x86_64环境中安装，并且是以root用户身份执行安装操作。

## 下载安装包

[点击此处](https://gitee.com/GreatSQL/GreatSQL/releases/)下载最新的安装包，下载以下几个就可以：

- greatsql-client-8.0.25-16.1.el8.x86_64.rpm 
- greatsql-devel-8.0.25-16.1.el8.x86_64.rpm  
- greatsql-shared-8.0.25-16.1.el8.x86_64.rpm
- greatsql-server-8.0.25-16.1.el8.x86_64.rpm 


## 运行环境配置
关闭selinux和防火墙
```
#关闭selinux
$ setenforce=0
$ sed -i '/^SELINUX=/c'SELINUX=disabled /etc/selinux/config

#关闭防火墙
$ systemctl disable firewalld
$ systemctl stop firewalld
$ systemctl disable iptables
$ systemctl stop iptables
```

另外，要先确认YUM源可用，因为安装GreatSQL时还要先安装其他依赖包，通过YUM安装最省事。

如果需要配置YUM源，可以参考[这篇文档](https://developer.aliyun.com/mirror/centos)。

## 安装依赖包

安装GreatSQL RPM包时，要先安装这些相关依赖包。
```
$ yum install -y pkg-config perl libaio-devel numactl-devel numactl-libs net-tools openssl openssl-devel jemalloc jemalloc-devel
```
如果有更多依赖包需要安装，请自行添加。


## 安装RPM包

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

## 启动GreatSQL

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
   Active: active (running) since Wed 2022-07-06 10:35:57 CST; 42s ago
     Docs: man:mysqld(8)
           http://dev.mysql.com/doc/refman/en/using-systemd.html
  Process: 43570 ExecStartPre=/usr/bin/mysqld_pre_systemd (code=exited, status=0/SUCCESS)
 Main PID: 43653 (mysqld)
   Status: "Server is operational"
    Tasks: 39 (limit: 149064)
   Memory: 446.4M
   CGroup: /system.slice/mysqld.service
           └─43653 /usr/sbin/mysqld
...

$ ps -ef | grep mysqld
mysql      43653       1  3 10:35 ?        00:00:02 /usr/sbin/mysqld

$ ss -lntp | grep mysqld
LISTEN 0      70                 *:33060            *:*    users:(("mysqld",pid=43653,fd=23))
LISTEN 0      128                *:3306             *:*    users:(("mysqld",pid=43653,fd=26))

# 查看数据库文件
$ ls /var/lib/mysql
 auto.cnf        ca.pem              '#ib_16384_1.dblwr'   ib_logfile1     mysql.ibd         mysqlx.sock.lock     server-cert.pem   undo_002
 binlog.000001   client-cert.pem      ib_buffer_pool       ibtmp1          mysql.sock        performance_schema   server-key.pem
 binlog.index    client-key.pem       ibdata1             '#innodb_temp'   mysql.sock.lock   private_key.pem      sys
 ca-key.pem     '#ib_16384_0.dblwr'   ib_logfile0          mysql           mysqlx.sock       public_key.pem       undo_001
```
可以看到，GreatSQL服务已经正常启动了。

## 连接登入GreatSQL

RPM方式安装GreatSQL后，会随机生成管理员root的密码，通过搜索日志文件获取：
```
$ grep -i root /var/log/mysqld.log
2022-07-06T02:35:54.691879Z 6 [Note] [MY-010454] [Server] A temporary password is generated for root@localhost: K<f9Iapd#wwp
```
可以看到，root账户的密码是："K<f9Iapd#wwp" (不包含双引号)，复制到粘贴板里。

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
UNIX socket:        /var/lib/mysql/mysql.sock
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

## 关闭/重启GreatSQL

执行下面的命令关闭GreatSQL数据库。
```
$ systemctl stop mysqld
```

执行下面的命令重启GreatSQL数据库。
```
$ systemctl restart mysqld
```

至此，RPM包方式安装GreatSQL数据库完成。

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
