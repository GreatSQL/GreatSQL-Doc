# 7. 利用MySQL Router构建读写分离MGR集群 | 深入浅出MGR

[toc]

本文介绍如何在MGR集群前端部署MySQL Router以实现读写分离、读负载均衡，以及故障自动转移。

MySQL Router是一个轻量级的中间件，它采用多端口的方案实现读写分离以及读负载均衡，而且同时支持mysql和mysql x协议。

建议把MySQL Router部署在应用服务器上，每个应用服务器都部署一套，这样应用程序可以直接连接本机IP，连接的效率更高，而且后端数据库发生变化时，程序端也无需修改IP配置。

## 1. 部署MySQL Router
MySQL Router第一次启动时要先初始化：
```
#
#参数解释
# 参数 --bootstrap 表示开始初始化
# 参数 GreatSQL@172.16.16.10:3306 是MGR服务专用账号
# --user=mysqlrouter 是运行mysqlrouter进程的系统用户名
#
$ mysqlrouter --bootstrap GreatSQL@172.16.16.10:3306 --user=mysqlrouter
Please enter MySQL password for GreatSQL:   <-- 输入密码
# 然后mysqlrouter开始自动进行初始化
# 它会自动读取MGR的元数据信息，自动生成配置文件
Please enter MySQL password for GreatSQL:
# Bootstrapping system MySQL Router instance...

- Creating account(s) (only those that are needed, if any)
- Using existing certificates from the '/var/lib/mysqlrouter' directory
- Verifying account (using it to run SQL queries that would be run by Router)
- Storing account in keyring
- Adjusting permissions of generated files
- Creating configuration /etc/mysqlrouter/mysqlrouter.conf

# MySQL Router configured for the InnoDB Cluster 'MGR1'

After this MySQL Router has been started with the generated configuration

    $ /etc/init.d/mysqlrouter restart
or
    $ systemctl start mysqlrouter
or
    $ mysqlrouter -c /etc/mysqlrouter/mysqlrouter.conf

the cluster 'MGR1' can be reached by connecting to:

## MySQL Classic protocol  <-- MySQL协议的两个端口

- Read/Write Connections: localhost:6446
- Read/Only Connections:  localhost:6447

## MySQL X protocol  <-- MySQL X协议的两个端口

- Read/Write Connections: localhost:6448
- Read/Only Connections:  localhost:6449
```
如果想自定义名字和目录，还可以在初始化时自行指定 `--name` 和 `--directory` 选项，这样可以实现在同一个服务器上部署多个Router实例，参考这篇文章：[MySQL Router可以在同一个系统环境下跑多实例吗](https://mp.weixin.qq.com/s/9eLnQ2EJIMQnZuEvScIhiw)

## 2. 启动mysqlrouter服务
这就初始化完毕了，按照上面的提示，直接启动 **mysqlrouter** 服务即可：
```
[root@greatsql]# systemctl start mysqlrouter

[root@greatsql]# ps -ef | grep -v grep | grep mysqlrouter
mysqlro+  6026     1  5 09:28 ?        00:00:00 /usr/bin/mysqlrouter

[root@greatsql]# netstat -lntp | grep mysqlrouter
tcp        0      0 0.0.0.0:6446            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:6447            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:6448            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:6449            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:8443            0.0.0.0:*               LISTEN      6026/mysqlrouter
```
可以看到 **mysqlrouter** 服务正常启动了。

**mysqlrouter** 初始化时自动生成的配置文件是 `/etc/mysqlrouter/mysqlrouter.conf`，主要是关于R/W、RO不同端口的配置，例如：
```
[routing:greatsqlMGR_rw]
bind_address=0.0.0.0
bind_port=6446
destinations=metadata-cache://greatsqlMGR/?role=PRIMARY
routing_strategy=first-available
protocol=classic
```
可以根据需要自行修改绑定的IP地址和端口，也可以在初始化时指定 `--conf-base-port` 选项自定义初始端口号。

## 3. 确认读写分离效果
现在，用客户端连接到6446（读写）端口，确认连接的是PRIMARY节点：
```
$ mysql -h172.16.16.10 -u GreatSQL -p -P6446
Enter password:
...
#记住下面几个 MEMBER_ID
mysql> select MEMBER_ID,MEMBER_ROLE from performance_schema.replication_group_members;
+--------------------------------------+-------------+
| MEMBER_ID                            | MEMBER_ROLE |
+--------------------------------------+-------------+
| 4ebd3504-11d9-11ec-8f92-70b5e873a570 | PRIMARY     |
| 549b92bf-11d9-11ec-88e1-70b5e873a570 | SECONDARY   |
| 5596116c-11d9-11ec-8624-70b5e873a570 | SECONDARY   |
+--------------------------------------+-------------+

mysql> select @@server_uuid;
+--------------------------------------+
| @@server_uuid                        |
+--------------------------------------+
| 4ebd3504-11d9-11ec-8f92-70b5e873a570 |
+--------------------------------------+
# 确实是连接的PRIMARY节点
```

同样地，连接6447（只读）端口，确认连接的是SECONDARY节点：
```
$ mysql -h172.16.16.10 -u GreatSQL -p -P6447
Enter password:
...
mysql> select @@server_uuid;
+--------------------------------------+
| @@server_uuid                        |
+--------------------------------------+
| 549b92bf-11d9-11ec-88e1-70b5e873a570 |
+--------------------------------------+
# 确实是连接的SECONDARY节点
```

## 4. 确认只读负载均衡效果
MySQL Router连接读写节点（Primary节点）默认的策略是 **first-available**，即只连接第一个可用的节点。Router连接只读节点（Secondary节点）默认的策略是 **round-robin-with-fallback**，会在各个只读节点间轮询。

保持6447端口原有的连接不退出，继续新建到6447端口的连接，查看 **server_uuid**，这时应该会发现读取到的是其他只读节点的值，因为 **mysqlrouter** 的读负载均衡机制是在几个只读节点间自动轮询。在默认的 **round-robin-with-fallback** 策略下，只有当所有只读节点都不可用时，只读请求才会打到PRIMARY节点上。

关于Router的连接策略，可以参考 FAQ文档中的：[24. MySQL Router可以配置在MGR主从节点间轮询吗](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/GreatSQL-FAQ.md)，或者MySQL Router官方文档：[routing_strategy参数/选项](https://dev.mysql.com/doc/mysql-router/8.0/en/mysql-router-conf-options.html#option_mysqlrouter_routing_strategy)

## 5. 确认故障自动转移功能
接下来模拟PRIMARY节点宕机或切换时，**mysqlrouter** 也能实现自动故障转移。

登入MGR集群任意节点：
```
$ mysqlsh --uri GreatSQL@172.16.16.10:3306
...
MySQL  172.16.16.10:3306 ssl  JS >  var c=dba.getCluster();
MySQL  172.16.16.10:3306 ssl  JS >  c.setPrimaryInstance('172.16.16.11:3306');   <-- 切换PRIMARY节点
Setting instance '172.16.16.11:3306' as the primary instance of cluster 'MGR1'...

Instance '172.16.16.10:3306' was switched from PRIMARY to SECONDARY.   <-- 切换了，从PRIMARY到SECONDARY
Instance '172.16.16.11:3306' was switched from SECONDARY to PRIMARY.   <-- 切换了，从SECONDARY到PRIMARY
Instance '172.16.16.12:3306' remains SECONDARY.   <-- 保持不变

WARNING: The cluster internal session is not the primary member anymore. For cluster management operations please obtain a fresh cluster handle using dba.getCluster().

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
| 549b92bf-11d9-11ec-88e1-70b5e873a570 |   <-- 确认server_uuid变成新的
+--------------------------------------+
```
这就实现了自动故障转移。

至此，利用MySQL Router配合GreatSQL构建一套支持读写分离、读负载均衡以及故障自动转移的MGR集群就部署完毕了。

## 6. 小结
本文介绍了如何利用MySQL Router实现读写分离、读负载均衡，以及故障自动转移，利用MySQL Router可以提升应用端的透明性，后端数据库发生一些变化时，应用端无需跟着频繁变更。

## 参考资料、文档
- [MySQL 8.0 Reference Manual](https://dev.mysql.com/doc/refman/8.0/en/group-replication.html) 
- [数据库内核开发 - 温正湖](https://www.zhihu.com/column/c_206071340)
- [Group Replication原理 - 宋利兵](https://mp.weixin.qq.com/s/LFJtdpISVi45qv9Wksv19Q)

## 免责声明
因个人水平有限，专栏中难免存在错漏之处，请勿直接复制文档中的命令、方法直接应用于线上生产环境。请读者们务必先充分理解并在测试环境验证通过后方可正式实施，避免造成生产环境的破坏或损害。

## 加入团队
如果您有兴趣一起加入协作，欢迎联系我们，可直接提交PR，或者将内容以markdown的格式发送到邮箱：greatsql@greatdb.com。

亦可通过微信、QQ联系我们。

![Contact Us](../docs/contact-us.png)