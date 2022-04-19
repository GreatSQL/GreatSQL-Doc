# 15. 故障检测与网络分区 | 深入浅出MGR

[toc]

本文介绍MGR的故障检测机制，以及发生网络分区后如何处理。

## 1. 故障检测
当MGR中个别节点与其他节点通信异常时，就会触发故障检测机制，经过多数派节点投票判断后再决定是否将其驱逐出MGR。

发生故障时，只有当多数派节点存活前提下，故障检测机制才能工作正常，使得MGR恢复可用性；当多数派节点本身已经异常的时候，MGR是无法自行恢复的，需要人为介入。

MGR中，各节点间会定期交换消息，当超过5秒（在MySQL中是固定5秒，在GreatSQL中新增选项 `group_replication_communication_flp_timeout` 可配置）还没收到某个节点的任何消息时，就会将这个节点标记为可疑状态。MGR各正常存活节点会对可疑节点每隔15秒检测一次（在GreatSQL中，调整为每隔2秒检测，效率更高，下面再介绍），当确认可疑节点在超过`group_replication_member_expel_timeout`秒超时阈值后，再将该节点驱逐出MGR。

需要注意的是，选项 `group_replication_member_expel_timeout` 从MySQL 8.0.21开始，默认值为5。在MySQL 8.0.21之前，默认值为0。在 <= MySQL 8.0.20 的版本中，group_replication_member_expel_timeout 默认值为 0，也就是当某节点被判定为可疑状态后，会被立即驱逐。在MySQL 5.7中，没有该选项，行为模式也是一样的。

在MySQL中，MGR故障检测是由独立线程来完成的，该线程每隔15秒（MySQL在源码中硬编码定义了 `SUSPICION_PROCESSING_THREAD_PERIOD = 15`）进行一次检查。因此，节点发生故障时，极端情况下，可能要耗费 5（5秒没发送消息，被判定为可疑节点） + 15（SUSPICION_PROCESSING_THREAD_PERIOD） + 5（group_replication_member_expel_timeout） = 25秒 才能驱逐该节点。最好的情况下，最快 5 + 5 = 10秒 后即可驱逐该节点。

在GreatSQL中对此进行了优化，新增选项 `group_replication_communication_flp_timeout`（默认值5，最小3，最大60） 用于定义节点超过多少秒没发消息会被判定为可疑。此外，还修改了硬编码 `SUSPICION_PROCESSING_THREAD_PERIOD = 2`，也就是故障检测线程每2秒（而非15秒）就会检查一次。因此在GreatSQL中，最快 5（group_replication_communication_flp_timeout） + 5（group_replication_member_expel_timeout） = 10秒 完成驱逐，最慢 5 + 5 + 2（SUSPICION_PROCESSING_THREAD_PERIOD） = 12秒 完成驱逐。

在网络条件不好的情况下，建议适当加大 group_replication_member_expel_timeout 值，避免网络波动造成节点频繁被驱逐。不过也要注意另一个风险，见这篇文章所述：[为什么MGR一致性模式不推荐AFTER](https://mp.weixin.qq.com/s/rNeq479RNsklY1BlfKOsYg)。

存活的节点会把被驱逐的节点从成员列表中删除，但被驱逐的节点自身可能还没“意识”到（可能只是因为临时短时间的网络异常），在状态恢复后，该节点会先收到一条包含该节点已被驱逐出MGR的新视图信息，而后再重新加入MGR。被驱逐的节点会尝试 `group_replication_autorejoin_tries` 次重新加入MGR。

选项 `group_replication_exit_state_action` 定义了被驱逐节点之后的行为模式，默认是设置为 `super_read_only = ON`，进入只读模式。

## 2. 少数派成员失联时
当集群中的少数派成员失联时（Unreachable），默认不会自动退出MGR集群。这时可以设置 `group_replication_unreachable_majority_timeout`，当少数派节点和多数派节点失联超过该阈值时，少数派节点就会自动退出MGR集群。如果设置为0，则会立即退出，而不再等待。节点退出集群时，相应的事务会被回滚，然后节点状态变成ERROR，并执行选项 `group_replication_exit_state_action` 定义的后续行为模式。如果设置了 `group_replication_autorejoin_tries`，也会再自动尝试重新加入MGR集群。

## 3. 多数派成员失联时
当多数派节点也失联时（Unreachable），例如在一个3节点的MGR集群中，有2个节点失联了，剩下的1个节点不能成为多数派，也就无法对新事务请求做出决策，这种情况就是发生了网络分区（脑裂）。也就是一个MGR集群分裂成两个或多个区域，也因此缺少多数派，这种情况下，MGR集群无法提供写入服务。

此时需要人工介入，通过设置 `group_replication_force_members` 强行指定新的成员列表。例如MGR集群由3个节点组成，其中两个节点都意外失联了，仅剩一个节点存活，此时就需要手动设置`group_replication_force_members` 强行指定成员列表，也就是只有最后存活的节点。

**两个重要提醒：**
1. 使用该方法基本上是最后迫不得已的选择，因此需要非常谨慎。若使用不当，可能会造成一个人为的脑裂场景，或者造成整个系统被完全阻塞。也有可能会选错新的节点列表。
2. 强制设定新的节点列表并解除MGR阻塞后，记得再将该选项值清空，否则无法再次执行START GROUP_REPLICATION。

## 4. Xcom cache
当有节点处于可疑状态时，在它被确定踢出MGR集群之前，事务会缓存在其他节点的Xcom cache中。这个cache对应选项 `group_replication_message_cache_size`。当可疑节点短时内又恢复后，就会先从Xcom cache中读取记录进行恢复，然后再进行分布式恢复。因此，在 **网络不太稳定** 或 **并发事务较大**，且物理内存也足够的场景里，可以适当加大Xcom cache size；反之，在物理内存较小，或者网络较为稳定的场景里，不应设置太大，降低发生OOM的风险。

在MySQL 5.7里，Xcom cache size最大值1G，且不可动态调整。从MySQL 8.0开始，可对其动态调整。在 <= MySQL 8.0.20的版本中，最小值1G。在>= MySQL 8.0.21的版本中，最小值128M。

可以执行下面的SQL查看当前Xcom cache消耗情况：
```
[root@GreatSQL]> SELECT * FROM performance_schema.memory_summary_global_by_event_name
  WHERE EVENT_NAME LIKE ‘memory/group_rpl/GCS_XCom::xcom_cache';
```

在MySQL中，是动态按需分配Xcom cache的，如果太多有空闲，就释放；如果不够用，再动态分配更多内存，一次分配大概250000个cache item，很容易造成约150ms的响应延迟。也就是说，会随着事务多少的变化而可能频繁产生响应延迟。

在GreatSQL中，对Xcom cache采用了静态化分配机制，即一开始就预分配约1GB内存用于xcom cache，这可以避免前面提到的响应延迟抖动风险，不过“副作用”是mysqld进程所占用的内存会比原来多，在内存特别紧张的服务器上不太适合。

## 5. 网络分区
在MGR里，事务是需要经过多数派节点达成一致性共识（要么都提交，要么都回滚）。同样的，前面提到的节点间通信消息也是需要在多数派节点间达成共识。当MGR中的多数派节点失联时，就无法就此形成共识，也无法满足多数派投票/仲裁要求，此时MGR将拒绝写事务请求。这种情况，也称为网络分区，及一个MGR集群分裂成两个或多个分区，彼此间相互无法连通，任何一个分区中的节点都不能达成多数派。

可能Primary节点会因为网络分区时被踢出MGR集群，它在重新加回时，可能会因为本地有此前还没来得及同步到其他节点的事务，而造成本地有更多事务，会报告类似下面的错误：
```
This member has more executed transactions than those present in the group. Local transactions: xx:1-300917674 > Group transactions: xx:1-300917669
```
此时需要人工介入处理，选择哪个节点作为最新的Primary节点。

## 小结
本文介绍了MGR的故障检测机制、Xcom cache，什么是网络分区，以及发生故障时都有什么影响，如何恢复故障等。

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
