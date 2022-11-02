# 从MySQL迁移/升级到GreatSQL
---

本文档介绍如何从MySQL迁移/升级到GreatSQL数据库。

## 1. 为什么要迁移/升级

GreatSQL相对于MySQL社区版有着众多优秀特性，包括且不仅限以下：

| 特性 | GreatSQL 8.0.25-16| MySQL 8.0.25 社区版 |
|---| --- | --- |
| 投票节点/仲裁节点 | ✅ | ❎ |
| 快速单主模式 | ✅ | ❎ |
| 地理标签 | ✅ | ❎ |
| 全新流控算法 | ✅ | ❎ |
| InnoDB并行查询优化 | ✅ | ❎ |
| 线程池（Thread Pool） | ✅ | ❎ |
|审计| ✅ | ❎ |
| InnoDB事务锁优化 | ✅ | ❎ |
|SEQUENCE_TABLE(N)函数|✅ | ❎ |
|InnoDB表损坏异常处理|✅ | ❎ |
|强制只能使用InnoDB引擎表|✅ | ❎ |
|杀掉空闲事务，避免长时间锁等待|✅ | ❎ |
|Data Masking（数据脱敏/打码）|✅ | ❎ |
|InnoDB碎片页统计增强|✅ | ❎ |
|支持MyRocks引擎|✅ | ❎ |
| InnoDB I/O性能提升 |  ⭐️⭐️⭐️⭐️⭐️ | ⭐️⭐️ | 
| 网络分区异常应对 |  ⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 完善节点异常退出处理 |   ⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 一致性读性能 |   ⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 提升MGR吞吐量 |⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 统计信息增强 |⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| slow log增强 |⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 大事务处理 |   ⭐️⭐️⭐️⭐️ | ⭐️ | 
| 修复多写模式下可能丢数据风险 | ⭐️⭐️⭐️⭐️⭐️ | /  | 
| 修复单主模式下切主丢数据风险 | ⭐️⭐️⭐️⭐️⭐️ | / | 
| MGR集群启动效率提升 | ⭐️⭐️⭐️⭐️⭐️ |  / | 
| 集群节点磁盘满处理 |   ⭐️⭐️⭐️⭐️⭐️ | /  | 
| 修复TCP self-connect问题| ⭐️⭐️⭐️⭐️⭐️ | / | 
| PROCESSLIST增强 | ⭐️⭐️⭐️⭐️⭐️ | /  | 

## 2. 迁移/升级前准备

首先下载GreatSQL 8.0版本安装包，推荐选择最新的[GreatSQL 8.0.25-16版本](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-16)，至于选择RPM还是二进制包看具体情况及个人喜好。

本文选用二进制包方式安装。

正式迁移/升级之前，务必做好数据备份，可以采用以下几种方式：

1. 停机维护，复制当前的数据库目录，做一个全量物理备份，这种方式恢复起来最快。
2. 利用mysqldump/xtrabackup等备份工具，执行一个全量备份。
3. 利用主从复制或MGR，在其中一个节点执行备份，或者令某个节点临时下线/退出，作为备用节点。

接下来，要区分本次迁移/升级属于以下哪种情况：

1. 从MySQL 5.7直接一次性迁移+升级到GreatSQL 8.0.25。
2. 从MySQL 8.0.25及以下版本迁移/升级到GreatSQL 8.0.25。
3. 从MySQL 8.0.26及以上版本迁移/降级到GreatSQL 8.0.25。
4. 从MySQL 5.6及更低版本迁移+升级到GreatSQL 8.0.25，则应该先逐次升级大版本，例如5.5=>5.6，5.6=>5.7最新版本，而后再一次性升级到GreatSQL 8.0.25。

如果是前两种，直接参考文档：[GreatSQL 5.7升级到8.0](./6-1-upgrade-to-greatsql8.md) 的方法进行迁移/升级即可，过程是完全一样的。

本文重点说说第三种场景。

## 3. 迁移过程

GreatSQL数据库是不支持直接原地(in-place)降级的，因此需要采用 **逻辑备份+导入** 的方式完成迁移。

如果是直接在MySQL 8.0.26及以上版本的datadir下，指定GreatSQL 8.0.25-16版本的mysqld二进制文件启动，则可能会报告类似下面的错误：
```
[ERROR] [MY-012530] [InnoDB] Unknown redo log format (5). Please follow the instructions at http://dev.mysql.com/doc/refman/8.0/en/ upgrading-downgrading.html.
[ERROR] [MY-012930] [InnoDB] Plugin initialization aborted with error Generic error.
[ERROR] [MY-010334] [Server] Failed to initialize DD Storage Engine
[ERROR] [MY-010020] [Server] Data Dictionary initialization failed.
[ERROR] [MY-010119] [Server] Aborting
```
即便用xtrabackup工具物理备份的文件恢复后，也是无法启动的，也会报告类似上面的错误信息。

因此，只有一种方法，那就是 **逻辑备份+导入**。

首先，用 `mysqldump` 备份全部数据：
```
$ mysqldump -S/data/MySQL/mysql.sock -A --triggers --routines --events > /backup/MySQL/fullbackup-`date +'%Y%m%d'`.sql
```

将备份文件copy到GreatSQL版本环境中，并执行导入即可，导入过程中可能会报错，加上 `-f` 选项并忽略这些错误就好（高版本中有些表在低版本中不存在，略过）。
```
$ mysql -S/data/GreatSQL/mysql.sock -f < /backup/MySQL/fullbackup-`date +'%Y%m%d'`.sql

#可能会报告类似下面的错误信息，忽略即可
...
ERROR 3723 (HY000) at line 543: The table 'replication_group_configuration_version' may not be created in the reserved tablespace 'mysql'.
ERROR 1146 (42S02) at line 554: Table 'mysql.replication_group_configuration_version' doesn't exist
ERROR 1146 (42S02) at line 555: Table 'mysql.replication_group_configuration_version' doesn't exist
ERROR 1146 (42S02) at line 556: Table 'mysql.replication_group_configuration_version' doesn't exist
ERROR 1146 (42S02) at line 557: Table 'mysql.replication_group_configuration_version' doesn't exist
ERROR 3723 (HY000) at line 567: The table 'replication_group_member_actions' may not be created in the reserved tablespace 'mysql'.
ERROR 1146 (42S02) at line 583: Table 'mysql.replication_group_member_actions' doesn't exist
ERROR 1146 (42S02) at line 584: Table 'mysql.replication_group_member_actions' doesn't exist
ERROR 1146 (42S02) at line 585: Table 'mysql.replication_group_member_actions' doesn't exist
ERROR 1146 (42S02) at line 586: Table 'mysql.replication_group_member_actions' doesn't exist
...
```
如果数据量较大的话，逻辑备份+导入过程耗时较久，要有心理准备。

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
