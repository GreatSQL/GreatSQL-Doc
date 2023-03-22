# GreatSQL 5.7升级到8.0
---

本文档介绍如何从GreatSQL 5.7/MySQL 5.7版本升级到GreatSQL 8.0版本。

## 1. 为什么要升级

GreatSQL 8.0相对于5.7有着众多优秀新特性，包括且不仅限以下：

| 特性 |  GreatSQL 8.0 |GreatSQL/MySQL 5.7 |
| --- | ---|---|
| MGR投票节点/仲裁节点 | ✅ | ❎ |
| MGR快速单主模式 | ✅ | ❎ |
| MGR地理标签 | ✅ | ❎ |
| MGR优化流控算法 | ✅ | ❎ |
| MGR网络分区异常处理 | ✅ | ❎ |
| MGR节点异常退出处理 | ✅ | ❎ |
| MGR节点磁盘满处理 | ✅ | ❎ |
| InnoDB并行查询优化 | ✅ | ❎ |
| 秒级加新列 | ✅ | ❎ |
| Hash Join|  ✅ | ❎ |
| Anti Join优化 | ✅ | ❎ |
| 直方图 | ✅ | ❎ |
| 倒序索引 | ✅ | ❎ |
| 不可见索引 | ✅ | ❎ |
| 函数索引/表达式索引 | ✅ | ❎ |
| 多值索引 | ✅ | ❎ |
| CTE | ✅ | ❎ |
| 窗口函数 | ✅ | ❎ |
| EXPLAIN ANALYZE | ✅ | ❎ |
| Clone Plugin | ✅ | ❎ |
| 全新数据字典 | ✅ | ❎ |
| DDL原子性 | ✅ | ❎ |
| 升级更灵活 |  ✅ | ❎ |
| 数个安全增强 | ✅ | ❎ |
| 数个InnODB增强 | ✅ | ❎ |
| 数个优化器增强 | ✅ | ❎ |

## 2. 升级前准备

首先下载GreatSQL 8.0版本安装包，推荐选择最新的[GreatSQL 8.0.25-16版本](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-16)，至于选择RPM还是二进制包看具体情况及个人喜好。

本文假定升级前后都是二进制包方式安装。

正式升级之前，务必做好数据备份，可以采用以下几种方式：

1. 停机维护，复制当前的数据库目录，做一个全量物理备份，这种方式恢复起来最快。
2. 利用mysqldump/xtrabackup等备份工具，执行一个全量备份。
3. 利用主从复制或MGR，在其中一个节点执行备份，或者令某个节点临时下线/退出，作为备用节点。

需要特别注意的事，您原先运行中的GreatSQL/MySQL 5.7版本，可能也是从其他旧版本中升级而来的，此时有可能MySQL系统库下的部分元数据表还是旧格式。这种情况下，需要先在原来的环境下执行 `mysql_upgrade` 进行升级修复旧格式。例如：
```
# 切换到当前运行的数据库实例datadir下
$ cd /data/GreatSQL

# 执行mysql_upgrade程序
# 参数 -s 表示只升级MySQL系统库表文件，不升级其他用户数据文件，一般建议去掉，对所有数据都进行升级
# 参数 -f 表示强制升级，如果升级过程中遇到报错，也会继续升级后面的库表文件，而不会直接退出
# 假定socket文件路径是 /data/GreatSQL/mysql.sock，用参数 -S 指向
$ /usr/local/GreatSQL-5.7.36-39-Linux-glibc2.28-x86_64/bin/mysql_upgrade -s -f -S/data/GreatSQL/mysql.sock

/usr/local/GreatSQL-5.7.36-39-Linux-glibc2.28-x86_64/bin/mysql_upgrade -s -S./mysql.sock
The --upgrade-system-tables option was used, databases won't be touched.
Checking if update is needed.
Checking server version.
Running queries to upgrade MySQL server.

...

mysql.time_zone_transition_type                    OK
mysql.user                                         OK
The sys schema is already up to date (version 1.5.2).
Checking databases.
sys.sys_config                                     OK
test.sbtest1                                       OK
Upgrade process completed successfully.
Checking if update is needed.
``` 

## 3. 升级过程

从GreatSQL/MySQL 5.7升级到8.0需要注意以下几点变化：

1. 升级前的版本要求是GA版本，即5.7.9之后的版本。如果不是的话，要先在5.7大版本内升级小版本。
2. 建议先把当前的5.7升级到最新的子版本，截止本文档时间，最新版本是5.7.38。
3. 升级到8.0版本后，主要区别是默认密码验证插件(`default_authentication_plugin`)从 `mysql_native_password` 变成了 `caching_sha2_password`，会影响一些版本比较低的API/驱动，在创建用户时仍旧指定为 `mysql_native_password` 即可，或者在 `my.cnf` 中设置 `default_authentication_plugin=mysql_native_password`。
4. 在8.0中，不能直接利用 `GRANT` 创建新用户，需要手动先 `CREATE USER` 才能 `GRANT`，对应 `SQL_MODE = NO_AUTO_CREATE_USER`。
5. 在8.0中，除了InnoDB引擎，其他引擎表都不支持原生PARTITION特性。
6. 默认字符集、校验集分别从 `latin1 & latin1_swedish_ci` 升级成 `utf8mb4 & utf8mb4_0900_ai_ci`。**注意** ，在5.7版本中，`utf8mb4` 默认的校验集是 `utf8mb4_general_ci`，而在8.0中，对应的默认校验集则变成 `utf8mb4_0900_ai_ci`。如果有数据库、表、存储函数等数据对象没有显式声明校验集的话，注意是否发生变化。

只要注意上述这几点区别，做到心中有数，升级到8.0就不慌了。

升级的方法有以下几种可选。

### 3.1 原地升级

如果数据库能停机维护，则采用原地升级（in-place upgrade）方法最为简单。

备份完成后，关闭数据库实例，在关闭数据库实例前，务必确保设置选项 `innodb_fast_shutdown=0`，以确保得到的是个干净的、正常关闭的数据库文件集。

首先修改 `my.cnf`，增加一行
```
upgrade = FORCE
```

然后修改正确的 `basedir` 指向新版本二进制文件路径，再次启动GreatSQL 8.0服务，即可实现自动升级，除了系统表，用户表也会全部升级。

**注意：** 这种方法不支持从5.6版本直接升级到8.0。

升级过程的日志输入类似下面这样：
```
...
[System] [MY-011012] [Server] Starting upgrade of data directory.
...
[System] [MY-011003] [Server] Finished populating Data Dictionary tables with data.
[System] [MY-013381] [Server] Server upgrade from '50700' to '80025' started.
[System] [MY-013381] [Server] Server upgrade from '50700' to '80025' completed.
...
[System] [MY-010931] [Server] /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld: ready for connections. Version: '8.0.25-16'  socket: 'mysql.sock'  port: 3306  GreatSQL, Release 16, Revision 8bb0e5af297.
```

是不是觉得有点惊喜，有点意外，怎么怎么简单，事实的确如此。

如果有强迫症的话，想要看到完整升级过程，还可以加上两个选项 `log_error_verbosity=3` 以及 `innodb_print_ddl_logs = ON`，输出的日志就会多很多：
```
...
[System] [MY-011012] [Server] Starting upgrade of data directory.
...
[Note] [MY-011088] [Server] Data dictionary initializing version '80023'.
[Note] [MY-010337] [Server] Created Data Dictionary for upgrade
...
[System] [MY-011003] [Server] Finished populating Data Dictionary tables with data.
[Note] [MY-011008] [Server] Finished migrating TABLE statistics data.
[Note] [MY-011008] [Server] Finished migrating TABLE statistics data.
[Note] [MY-010006] [Server] Using data dictionary with version '80023'.
[System] [MY-013381] [Server] Server upgrade from '50700' to '80025' started.
[Note] [MY-013386] [Server] Running queries to upgrade MySQL server.
...
[Note] [MY-012477] [InnoDB] DDL log insert : [DDL record: REMOVE CACHE, id=1, thread_id=5, table_id=1072, new_file_path=mysql/default_roles
]
[Note] [MY-012478] [InnoDB] DDL log delete : 1
[Note] [MY-012472] [InnoDB] DDL log insert : [DDL record: FREE, id=2, thread_id=5, space_id=4294967294, index_id=57, page_no=542]
[Note] [MY-012478] [InnoDB] DDL log delete : 2
[Note] [MY-012485] [InnoDB] DDL log post ddl : begin for thread id : 5
[Note] [MY-012486] [InnoDB] DDL log post ddl : end for thread id : 5
[Note] [MY-012477] [InnoDB] DDL log insert : [DDL record: REMOVE CACHE, id=3, thread_id=5, table_id=1073, new_file_path=mysql/role_edges]
[Note] [MY-012478] [InnoDB] DDL log delete : 3
[Note] [MY-012472] [InnoDB] DDL log insert : [DDL record: FREE, id=4, thread_id=5, space_id=4294967294, index_id=58, page_no=543]
[Note] [MY-012478] [InnoDB] DDL log delete : 4
[Note] [MY-012485] [InnoDB] DDL log post ddl : begin for thread id : 5
[Note] [MY-012486] [InnoDB] DDL log post ddl : end for thread id : 5
[Note] [MY-012477] [InnoDB] DDL log insert : [DDL record: REMOVE CACHE, id=744, thread_id=5, table_id=1171, new_file_path=mysql/help_relation]
...
[Note] [MY-012478] [InnoDB] DDL log delete : 744
[Note] [MY-012472] [InnoDB] DDL log insert : [DDL record: FREE, id=745, thread_id=5, space_id=4294967294, index_id=189, page_no=1183]
[Note] [MY-012478] [InnoDB] DDL log delete : 745
[Note] [MY-012485] [InnoDB] DDL log post ddl : begin for thread id : 5
[Note] [MY-012479] [InnoDB] DDL log replay : [DDL record: DROP, id=743, thread_id=5, table_id=1146]
[Note] [MY-012479] [InnoDB] DDL log replay : [DDL record: FREE, id=742, thread_id=5, space_id=4294967294, index_id=156, page_no=835]
[Note] [MY-012486] [InnoDB] DDL log post ddl : end for thread id : 5
[Note] [MY-013400] [Server] Upgrade of help tables completed.
[Note] [MY-013394] [Server] Checking 'mysql' schema.
[Note] [MY-013394] [Server] Checking 'greatsql' schema.
[Note] [MY-013394] [Server] Checking 'sys' schema.
[System] [MY-013381] [Server] Server upgrade from '50700' to '80025' completed.
...
[System] [MY-010931] [Server] /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/bin/mysqld: ready for connections. Version: '8.0.25-16'  socket: 'mysql.sock'  port: 3306  GreatSQL, Release 16, Revision 8bb0e5af297.
```
这样就完成升级了，非常便捷省事。

### 3.2 滚动升级

可借助主从复制或MGR架构，利用滚动升级方法，先在从节点升级验证无误后，再升级主节点，最终实现所有节点都升级到GreatSQL 8.0版本。

具体可参考文章：[MySQL 5.7 MGR平滑升级到GreatSQL 5.7](https://mp.weixin.qq.com/s/u0UAijfM8jHH948ml1PREg)。根据该文章提供的思路，把MySQL 5.7平滑升级到GreatSQL 5.7之后，仍旧采用同样方法升级到GreatSQL 8.0版本。

最后要注意检查升级过程中输出的日志是否有报错信息，如果没有就说明升级过程很顺利。

确定升级完成后，记得注释掉 `my.cnf` 文件中的 `upgrade = FORCE` 选项，或者将其修改成 `upgrade = AUTO`。

**参考文档**

- [Percona Server for MySQL In-Place Upgrading Guide: From 5.7 to 8.0](https://docs.percona.com/percona-server/latest/upgrading_guide.html)
- [Changes in MySQL 8.0](https://dev.mysql.com/doc/refman/8.0/en/upgrading-from-previous-series.html)
- [Before You Begin](https://dev.mysql.com/doc/refman/8.0/en/upgrade-before-you-begin.html)
- [What the MySQL Upgrade Process Upgrades](https://dev.mysql.com/doc/refman/8.0/en/upgrading-what-is-upgraded.html)
- [MySQL 5.7 MGR平滑升级到GreatSQL 5.7](https://mp.weixin.qq.com/s/u0UAijfM8jHH948ml1PREg)

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
