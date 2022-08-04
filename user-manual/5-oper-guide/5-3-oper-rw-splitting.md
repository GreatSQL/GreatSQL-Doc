# 读写分离
---

本文档描述如何为MGR集群构建读写分离方案。

## 1. InnoDB Cluster简介
MySQL InnoDB Cluster（简称MIC）是MySQL推出的整套解决方案，由几个部分组成：
- MySQL Server，核心是Group Replication（组复制），简称MGR。
- MySQL Shell，可编程的高级客户端，支持标准SQL语法、JavaScript语法、Python语法，以及API接口，可以更方便的管理和使用MySQL服务器。
- MySQL Router，轻量级中间件，支持透明路由规则（读写分离及读负载均衡）。

MySQL Router是一个轻量级的中间件，它采用多端口的方案实现读写分离以及读负载均衡，而且同时支持mysql和mysql x协议。

整体系统架构如下图所示：
![MySQL InnoDB Cluser架构](https://images.gitee.com/uploads/images/2021/0623/172104_653e92d0_8779455.png "MySQL InnoDB Cluser架构")

## 2. MySQL Router安装&初始化

MySQL Router最好和应用服务器部署在一起，所以本次将MySQL Router安装在另一个服务器上，IP地址是 *172.16.16.14*。

将MySQL Router和应用服务器部署在一起的好处在于，当某个后端数据库服务器发生宕机并下线及导致MGR发生切换时，部署在应用程序端的router程序能通过MGR的metadata信息感知到这个变化，并自动更新MGR拓扑结构，无需在应用程序上做任何变更，也无需针对router再次部署高可用切换方案。

[戳此下载MySQL Router RPM安装包](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-16)，选择下面的安装包：

- greatsql-mysql-router-8.0.25-16.1.el8.x86_64.rpm

下载到本地后，执行安装：
```
$ rpm -ivh greatsql-mysql-router-8.0.25-16.1.el8.x86_64.rpm
Verifying...                          ################################# [100%]
Preparing...                          ################################# [100%]
Updating / installing...
   1:greatsql-mysql-router-8.0.25-16.1################################# [100%]
```

MySQL Router对应的服务器端程序文件是 `/usr/bin/mysqlrouter`，第一次启动时要先进行初始化：
```
#
#参数解释
# 参数 --bootstrap 表示开始初始化
# 参数 GreatSQL@172.16.16.10:3306 是MGR集群管理员账号
# --user=mysqlrouter 是运行mysqlrouter进程的系统用户名
#
$ mysqlrouter --bootstrap GreatSQL@172.16.16.10:3306 --user=mysqlrouter
Please enter MySQL password for GreatSQL:   <-- 输入密码
# 然后mysqlrouter开始自动进行初始化
# 它会自动读取MGR的元数据信息，自动生成配置文件
# Bootstrapping system MySQL Router instance...

- Creating account(s) (only those that are needed, if any)
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

## MySQL Classic protocol  <-- MySQL协议的两个端口

- Read/Write Connections: localhost:6446
- Read/Only Connections:  localhost:6447

## MySQL X protocol  <-- MySQL X协议的两个端口

- Read/Write Connections: localhost:6448
- Read/Only Connections:  localhost:6449
```

这就初始化完毕了，按照上面的提示，直接启动 mysqlrouter 服务即可：
```
$ systemctl start mysqlrouter

$ ps -ef | grep -v grep | grep mysqlrouter
mysqlro+  6026     1  5 09:28 ?        00:00:00 /usr/bin/mysqlrouter

$ netstat -lntp | grep mysqlrouter
tcp        0      0 0.0.0.0:6446            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:6447            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:6448            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:6449            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:8443            0.0.0.0:*               LISTEN      6026/mysqlrouter
```
可以看到 mysqlrouter 服务正常启动了。

## 3. MySQL Router配置

MySQL Router初始化时自动生成的配置文件是 `/etc/mysqlrouter/mysqlrouter.conf`，主要是关于R/W、RO不同端口以及请求转发规则等配置，例如：
```
[routing:GreatSQLMGR_rw]
bind_address=0.0.0.0
bind_port=6446
destinations=metadata-cache://GreatSQLMGR/?role=PRIMARY
routing_strategy=first-available
protocol=classic

[routing:GreatSQLMGR_ro]
bind_address=0.0.0.0
bind_port=6447
destinations=metadata-cache://GreatSQLMGR/?role=SECONDARY
routing_strategy=round-robin-with-fallback
protocol=classic
```
可以根据需要自行修改绑定的IP地址和端口，以及请求转发规则。

关于请求转发规则，更详细的解释可参考以下内容：

- [MySQL Router可以配置在MGR主从节点间轮询吗](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/GreatSQL-FAQ.md#24-mysql-router%E5%8F%AF%E4%BB%A5%E9%85%8D%E7%BD%AE%E5%9C%A8mgr%E4%B8%BB%E4%BB%8E%E8%8A%82%E7%82%B9%E9%97%B4%E8%BD%AE%E8%AF%A2%E5%90%97)
- [routing_strategy参数/选项](https://dev.mysql.com/doc/mysql-router/8.0/en/mysql-router-conf-options.html#option_mysqlrouter_routing_strategy)

修改完配置后，重启mysqlrouter服务即可。

## 4. 确认读写分离

现在，用客户端连接到6446（读写）端口，确认连接的是PRIMARY节点：
```
$ mysql -h172.16.16.14 -uGreatSQL -p -P6446
Enter password:
...
mysql> select @@server_uuid;
+--------------------------------------+
| @@server_uuid                        |
+--------------------------------------+
| 66c5a894-07e6-11ed-b1ff-00155d064000 |
+--------------------------------------+

# 确实是连接的PRIMARY节点
mysql> select MEMBER_ID,MEMBER_HOST,MEMBER_ROLE from performance_schema.replication_group_members;
+--------------------------------------+--------------+-------------+
| MEMBER_ID                            | MEMBER_HOST  | MEMBER_ROLE |
+--------------------------------------+--------------+-------------+
| 62edd23f-07fa-11ed-aad1-00155d064000 | 172.16.16.13 | SECONDARY   |
| 66c5a894-07e6-11ed-b1ff-00155d064000 | 172.16.16.10 | PRIMARY     |
| 6e65ef68-07e6-11ed-a6d8-00155d064000 | 172.16.16.11 | SECONDARY   |
| 6f367f17-07e6-11ed-825d-00155d064000 | 172.16.16.12 | ARBITRATOR  |
+--------------------------------------+--------------+-------------+
```

同样地，连接6447（只读）端口，确认连接的是SECONDARY节点：
```
$ mysql -h172.16.16.14 -uGreatSQL -p -P6447
Enter password:
...
mysql> select @@server_uuid;
+--------------------------------------+
| @@server_uuid                        |
+--------------------------------------+
| 62edd23f-07fa-11ed-aad1-00155d064000 |
+--------------------------------------+
# 确实是连接的SECONDARY节点
```

该连接保持住不退出，继续新建到6447端口的连接，查看 `server_uuid`，应该会发现读取到的是另一个 SECONDARY 节点的值，因为 MySQL Router 默认的读负载均衡机制是在几个只读节点间自动轮询，除非所有 SECONDARY 节点都不可用，否则只读请求不会转发到PRIMARY节点。

**特别说明：** 由于ARBITRATOR角色是在GreatSQL中特有的，原生的MySQL Router并不支持。这个节点不存储用户数据、日志等，仅参与MGR的网络投票，因此当MySQL Router轮询连接到该节点时，可能会出现类似下面的提示：
```
$ mysql -h172.16.16.14 -uGreatSQL -p -P6447
mysql: [Warning] Using a password on the command line interface can be insecure.
ERROR 1045 (28000): Access denied for user 'GreatSQL'@'172.16.16.14' (using password: YES)
```
忽略这个错误提示，并尝试重连即可。

当然了，也可以通过修改MySQL Router的配置文件，把ARBITRATOR节点从只读节点列表中排除，例如：
```
[routing:GreatSQLMGR_ro]
bind_address=0.0.0.0
bind_port=6447
#destinations=metadata-cache://GreatSQLMGR/?role=SECONDARY
destinations=172.16.16.11,172.16.11.13
#routing_strategy=round-robin-with-fallback
routing_strategy=round-robin
protocol=classic
```
由于直接指定了只读节点列表，就无法再使用 *round-robin-with-fallback* 策略了，可以改成 *round-roubin* 策略。

## 5. 确认故障自动转移

如果PRIMARY节点宕机或切换，mysqlrouter也能实现自动故障转移，应用端不需要做任何变更，只需最多尝试重连或重新发起请求。

登入MGR集群任意节点：
```
$ mysqlsh --uri GreatSQL@172.16.16.10:3306
...
MySQL  172.16.16.10:3306 ssl  Py > c=dba.get_cluster();
MySQL  172.16.16.10:3306 ssl  Py > c.set_primary_instance('172.16.16.11:3306');   <-- 切换PRIMARY节点
Setting instance '172.16.16.11:3306' as the primary instance of cluster 'GreatSQLMGR'...

Instance '172.16.16.10:3306' was switched from PRIMARY to SECONDARY.   <-- 切换了，从PRIMARY到SECONDARY
Instance '172.16.16.11:3306' was switched from SECONDARY to PRIMARY.   <-- 切换了，从SECONDARY到PRIMARY
Instance '172.16.16.12:3306' remains ARBITRATOR.   <-- 保持不变
Instance '172.16.16.13:3306' remains SECONDARY.   <-- 保持不变

WARNING: The cluster internal session is not the primary member anymore. For cluster management operations please obtain a fresh cluster handle using dba.get_cluster().

The instance '172.16.16.11:3306' was successfully elected as primary.
```

回到前面连接6446端口的那个会话，再次查询 **server_uuid**，此时会发现连接自动断开了：
```
mysql> select @@server_uuid;
ERROR 2013 (HY000): Lost connection to MySQL server during query
mysql> select @@server_uuid;
ERROR 2006 (HY000): MySQL server has gone away
No connection. Trying to reconnect...
Connection id:    157990
Current database: *** NONE ***

+--------------------------------------+
| @@server_uuid                        |
+--------------------------------------+
| 6e65ef68-07e6-11ed-a6d8-00155d064000 |   <-- 确认server_uuid变成172.16.16.11节点的值
+--------------------------------------+
```
这就实现了自动故障转移。

再次查看切换后的MGR集群状态：
```
MySQL  172.16.16.10:3306 ssl  Py >  c.status();
...
        "topology": {
            "172.16.16.10:3306": {
                "address": "172.16.16.10:3306",
                "memberRole": "SECONDARY",   <-- 切换成SECONDARY节点
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.25"
            },
            "172.16.16.11:3306": {
                "address": "172.16.16.11:3306",
                "memberRole": "PRIMARY",   <-- 新的PRIMARY节点
                "mode": "R/W",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.25"
            },
...
```

利用MySQL Router构建一套支持读写分离、读负载均衡以及故障自动转移的MGR集群就部署完成。


**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
