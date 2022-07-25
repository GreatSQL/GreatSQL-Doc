# 单机多实例
---

本文档介绍如何在单机环境下部署多个GreatSQL数据库实例。

有时候，需要在同一个系统环境中运行多个数据库实例，以便节省服务器资源。

从MySQL 5.7开始，官方默认采用 `systemd` 来管理mysqld服务，不建议再使用 `mysqld_safe` 这种守护进程方式了。

单机单实例模式下，用 `systemd` 管理mysqld服务可参考这里：[增加GreatSQL系统服务](../4-install-guide/4-3-install-with-tarball.md#34-增加greatsql系统服务)。

无论是RPM还是二进制包方式安装的GreatSQL，都可以利用 `systemd` 管理多实例。

假定现在已经实现了用 `systemd` 管理mysqld单实例，接下来要实现管理多实例。

## 1. 添加systemd服务文件

手动编辑systemd服务文件：
```
$ vim /lib/systemd/system/greatsql@.service

[Unit]
Description=GreatSQL Server
Documentation=man:mysqld(8)
Documentation=http://dev.mysql.com/doc/refman/en/using-systemd.html
After=network.target
After=syslog.target
[Install]
WantedBy=multi-user.target
[Service]
User=mysql
Group=mysql
Type=notify
TimeoutSec=0
PermissionsStartOnly=true

#for single instance
#ExecStartPre=/usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld_pre_systemd
#ExecStart=/usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld $MYSQLD_OPTS

#for multi instance
ExecStartPre=/usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld_pre_systemd %I
ExecStart=/usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld --defaults-group-suffix=@%I $MYSQLD_OPTS

EnvironmentFile=-/etc/sysconfig/mysql
LimitNOFILE = 10000
Restart=on-failure
RestartPreventExitStatus=1
Environment=MYSQLD_PARENT_PID=1
PrivateTmp=false
```
注意到系统服务文件名相比单实例服务文件名多了 "@" 符，并且文件中 `ExecStartPre` 和 `ExecStart` 的内容也略有不同。

## 2. 编辑 /etc/my.cnf 配置文件

可以直接利用原来的 `/etc/my.cnf` 配置文件，将 `datadir`、`port`、`socket`、`server_id` 等几个选项注释掉，然后在文件末尾再加入类似下面的内容：
```
# 注意这里的写法和mysqld_multi不同
[mysqld@mgr01]
datadir=/data/GreatSQL/mgr01
socket=/data/GreatSQL/mgr01/mysql.sock
port=3306
server_id=103306
log-error=/data/GreatSQL/mgr01/error.log
group_replication_local_address= "172.16.16.10:33061"

[mysqld@mgr02]
datadir=/data/GreatSQL/mgr02
socket=/data/GreatSQL/mgr02/mysql.sock
port=3307
server_id=103307
log-error=/data/GreatSQL/mgr02/error.log
group_replication_local_address= "172.16.16.10:33071"

#更多实例照此方法继续复制即可
```

重新加载systemd，使其生效：
```
$ systemctl daemon-reload
```

即可识别到这些新增加的服务列表了：
```
$ systemctl -l
...
greatsql@mgr01.service                              loaded active running   GreatSQL Server...
greatsql@mgr02.service                              loaded active running   GreatSQL Server...
greatsql@mgr03.service                              loaded active running   GreatSQL Server...
...
```

现在可以直接执行类似下面的命令启停多实例服务：
```
$ systemctl start greatsql@mgr01
```

这就可以在单机环境下很方便的管理多实例服务了。


**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
