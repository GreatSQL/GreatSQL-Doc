# 13. 分布式恢复 | 深入浅出MGR

本文介绍节点加入时是如何进行分布式恢复的。

## 1. 数据恢复过程
每当有节点新加入或重新加入MGR集群时，该节点必须要先追平落后（有差异）的事务，这个追平最新数据的过程称为分布式恢复。先进行 **本地恢复**，然后再进行 **全局恢复**。

本地恢复主要工作是先启动本地group_replication_applier恢复通道，MGR节点信息再次初始化，然后读取本地relay log并进行恢复，接收远程节点发送的事务信息，先缓存到xcom cache中（`group_replication_message_cache_size`，默认值为1GB）。

全局恢复则是在应用完本地relay log的事务后，再经过 group_replication_recover 通道从 donor节点获取增量事务进行恢复，此外还要恢复上面第一步提到的xcom cache里缓存的事务，然后根据 `group_replication_recovery_complete_at` 选项设置（**TRANSACTIONS_CERTIFIED** 或 **TRANSACTIONS_APPLIED**，默认是 **TRANSACTIONS_APPLIED**）决定该节点是否可以正式宣告为online状态。

在这个过程中，准备加入的节点，称之为 joiner（加入者），而向joiner提供复制数据的节点称为 donor（捐献者）。

数据恢复时，MGR会随机选择某个节点作为donor角色，如果无法从当前的donor获取数据，则会尝试下一个donor节点，直到重试次数达到 `group_replication_recovery_retry_count` 阈值（默认为5）。

数据恢复的方式默认是采用增量恢复，当需要恢复的不在binlog中 或者 差异的事务达到 group_replication_clone_threshold 阈值（默认值非常大，是GTID允许的最大值），则采用clone方式进行恢复。个人建议：可以先判断差异的事务数有多大，如果超过10万个事务（这个值具体多少要看实际业务场景、服务器性能等条件，且不考虑大事务因素），则建议采用clone方式，可能恢复起来会更快些。

想要使用clone plugin的几个前提条件是：
1. 源和目标节点运行相同MySQL版本。
2. 相同的OS环境。
3. 相同的CPU架构。
4. 两端都启用clone plugin。
5. 都授予BACKUP_ADMIN权限。

执行clone时要特别注意下，目标节点上原来的数据都会被清空，重新写入源节点上的数据，因此如果目标节点上有些本地事务产生的数据，要先做好备份。

新加入的节点在clone结束后会重启mysql实例，它将重新选择一个新的donor节点执行基于binlog的状态传输，这个新的donor节点可能与重启前用于clone时的donor节点不是同一个。

在GreatSQL 8.0.32-26起，当有新成员节点加入 MGR 时，如果选择 Clone 方式复制数据，支持自动选择从最新事务数据的成员节点复制数据，可有效提升 Clone 速度，提高 MGR 的服务可靠性。当新加入节点触发 Clone 方式复制数据时，也支持该特性。

选项 `group_replication_donor_threshold` 用于定义选择 Donor 节点时判断事务延迟阈值，取值范围 [1, MAX]，默认值为 MAX。MAX 值取决于 CPU 类型，在 32-bit 系统中是 2147483647（2^31-1），而在 64-bit 系统中是 9223372036854775807（2^63-1）。

当新成员节点加入 MGR 时，新成员节点只会选择那些延迟小于 `group_replication_donor_threshold` 的节点作为 Donor 节点。

假设 `group_replication_donor_threshold = 100`，那么：
1. 现在 MGR 中有两个节点A、B，它们的 GTID 分别是 [1-300]、[1-280]，新节点 C 加入，由于 A & B 节点的 GTID 差值小于预设阈值，则随机选择 A 或 B 其中一个节点作为 Donor 节点。
2. 现在 MGR 中有两个节点A、B，它们的 GTID 分别是 [1-400]、[1-280]，新节点 C 加入，由于 A & B 节点的 GTID 差值大于预设阈值，则只会选择 A 作为 Donor 节点。
3. 现在 MGR 中有三个节点A、B、C，它们的 GTID 分别是 [1-400]、[1-350]、[1-280]，新节点 D 加入，由于 C 节点的 GTID 差值大于预设阈值，A & B 节点 GTID 延迟小于预设阈值，则会随机选择 A 或 B 其中一个作为 Donor 节点。

| System Variable Name  | group_replication_donor_threshold |
| --- | --- |
| Variable Scope        | Global |
| Dynamic Variable      | YES |
| Type      | Integer |
| Permitted Values |    [1 ~ 9223372036854775807] |
| Default       | 9223372036854775807 |

## 2. 小结
本文主要介绍MGR集群中当有新节点加入，数据是如何完成同步复制的，以及数据恢复过程中的一些关键点。


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
