# 14. 流量控制（流控） | 深入浅出MGR

本文介绍MGR中的流量控制（流控）是怎么工作的。

## 1. MGR流控
在MGR中，各个节点的事务处理能力不尽相同，这就可能会造成个别节点上存在事务复制延迟，在这些节点上就有可能读取到旧事务数据。复制延迟的另一个风险时，当有新节点加入时，需要选择一个节点作为donor节点，若该节点存在延迟，则可能最后会选中Primary节点，影响事务写入性能。还有，当某节点中堆积大量延迟事务队列时，也很容易造成该节点发生OOM风险。

综上几点，为了避免个别节点存在严重的事务复制延迟及其他风险，必要时可以采用流量控制（下面简称“流控”）来避免/缓解这个问题，降低节点间的事务延迟差距。

MGR流控有几个要点：
- 基于 **事务认证队列** 及 **等待被applied的relay log队列** 这两个队列（`group_replication_flow_control_applier_threshold`、`group_replication_flow_control_certifier_threshold`，默认值均为：25000），实行配额控制。
- 启用流控（`group_replication_flow_control_mode`，默认值：QUOTA）后，当任何一个队列大小超过设定阈值（配额）后，就会触发流控机制。
- 只影响启用流控的节点，不影响MGR中的其他节点（在PXC里是所有节点同时被流控影响）。
- 当设置流控配额百分比（`group_replication_flow_control_member_quota_percent`）时，会在多个启用流控的Primary节点间平摊配额。
- 流控只针对写事务，不影响只读事务。

触发流控后，会暂缓事务写入请求，在 **group_replication_flow_control_period**（默认值：1）秒后再次检查是否还超过阈值。如果还是超过则继续流控，否则的话就放开事务写入请求。不过这个流控机制在真实业务场景中效果很有限，在事务写入高峰期，可能会频繁造成TPS抖动，但却不能真正起到流控作用。在GreatSQL中， 针对这个缺陷进行了优化，重新设计流控算法。增加主从延迟时间来计算流控阈值，并且同时考虑了大事务处理和主从节点的同步，流控粒度更细致，不会出现官方社区版本的1秒小抖动问题。

在GreatSQL中，新增选项 `group_replication_flow_control_replay_lag_behind` 用于控制MGR主从节点复制延迟阈值，当MGR主从节点因为大事务等原因延迟超过阈值时，就会触发流控机制。
参数范围 0 ~ ULONG_MAX，默认值600秒，可在线动态修改，且立即生效。

此外，针对不同业务场景，流控阈值设置也不尽相同。对于事务实时性要求不高的业务，可以设置较大阈值。对于内存较大的节点，可以适当调大阈值；反之，在内存紧张的节点上，就要降低阈值以避免OOM风险。

## 2. 小结
本节介绍了为什么MGR需要流控，已经GreatSQL如何改进优化流控算法。

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
