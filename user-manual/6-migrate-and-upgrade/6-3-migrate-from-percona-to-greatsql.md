# 从Percona Server迁移/升级到GreatSQL
---

本文档介绍如何从Percona迁移/升级到GreatSQL数据库。

## 1. 为什么要迁移/升级

GreatSQL是在Percona Server的基础上Fork的开源分支，专注于提升MGR可靠性及性能，支持InnoDB并行查询等特性。

GreatSQL相对于Percona Server有着众多优秀特性，包括且不仅限以下：

| 特性 | GreatSQL| Percona Server|
|---| --- | --- |
| 投票节点/仲裁节点 | ✅ | ❎ |
| 快速单主模式 | ✅ | ❎ |
| 地理标签 | ✅ | ❎ |
| 全新流控算法 | ✅ | ❎ |
| InnoDB并行查询优化 | ✅ | ❎ |
| InnoDB事务锁优化 | ✅ | ❎ |
| 网络分区异常应对 |  ⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 完善节点异常退出处理 |   ⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 一致性读性能 |   ⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 提升MGR吞吐量 |⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
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

1. 从Percona 5.7直接一次性迁移+升级到GreatSQL 8.0.25。
2. 从Percona 8.0.25及以下版本迁移/升级到GreatSQL 8.0.25。
3. 从Percona 8.0.26及以上版本迁移/降级到GreatSQL 8.0.25。
4. 从Percona 5.6及更低版本迁移+升级到GreatSQL 8.0.25，则应该先逐次升级大版本，例如5.5=>5.6，5.6=>5.7最新版本，而后再一次性升级到GreatSQL 8.0.25。

如果是前两种，可以参考文档：[GreatSQL 5.7升级到8.0](./6-1-upgrade-to-greatsql8.md) 的方法进行迁移/升级即可，过程是完全一样的。

如果是第三种场景，可以参考文档：[从MySQL迁移/升级到GreatSQL](./6-2-migrating-from-mysql-to-greatsql.md) 中介绍的 **逻辑备份+导入** 方法，进行降级处理。

从Percona迁移到GreatSQL是最快捷的，元数据库表几乎没有区别，而InnoDB表数据则是通用的，几乎可以做到平滑迁移。

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
