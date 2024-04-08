# 17. MGR性能优化 | 深入浅出MGR

本文介绍MGR性能优化相关内容。

## 1. 性能瓶颈
在MGR架构中，可能存在众多可能会影响整体性能，包括本地节点中常见的一些性能瓶颈点，也可能包括MGR层产生的。

一般而言，造成MGR性能瓶颈的原因可能有以下几种情况：
1. 集群中，个别节点存在性能瓶颈。
2. 不恰当的流控阈值，导致性能受限。
3. 官方版本流控算法缺陷，导致性能抖动大。
4. 大事务造成延迟，甚至节点退出。
5. 网络成为瓶颈，导致消息延迟大。
6. 其他MySQL常见性能瓶颈导致。

接下来，我们针对以上几种情况，分别进行瓶颈分析并给出优化建议。

## 2. 优化建议
### 2.1 本地节点存在性能瓶颈
在MGR中，可能各个节点服务器配置等级各不相同，所能承载的业务压力也不同。因此，各节点可能会分别产生不同的事务延迟，或者等待被应用的事务堆积越来越多。

这种情况下，最有效的办法就是提升该节点的服务器配置级别，提高业务承载能力。同时，也要检查MySQL配置选项，是否有设置不合理的地方，并且可以考虑将选项 `innodb_flush_log_at_trx_commit` 和 `sync_binlog` 都设置为 0，以降低该节点的磁盘I/O负载，提升事务应用效率。

在GreatSQL中，还可以设置选项 `group_replication_single_primary_fast_mode = 1`（要求所有节点都这么设置），启用快速单主模式，提升MGR事务应用效率。

### 2.2 不恰当的流控
在 [14.流量控制（流控）](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-14.md) 这节内容中我们讲过，MySQL的流控机制有明显的缺陷，实际流控效果很有限，并且还可能会起到反作用，因此不建议启用MySQL的流控机制。即设置选项 `group_replication_flow_control_mode = DISABLED`。

在GreatSQL中，除了关闭流控外，只需设置选项 `group_replication_flow_control_replay_lag_behind = 600`，控制MGR主从节点复制延迟阈值，当MGR主从节点因为大事务等原因延迟超过阈值时，就会触发优化后的新的流控机制。

### 2.3 大事务造成延迟
当Primary上有大事务产生时，很容易造成Secondary在应用大事务过程中存在延迟。

因此，要尽量避免执行大事务。可以将大事务拆分成多个小事务，例如当执行load data导入大批数据时，就可以将导入文件切分成多个小文件。

此外，还可以适当调低 `group_replication_transaction_size_limit` 阈值，限制事务大小。

还可以通过监控事务状态，防止有个别事务运行时间过久：
```
# 活跃时间最长的事务
SELECT * FROM information_schema.innodb_trx ORDER BY trx_started ASC LIMIT N;

# 等待时间最长的事务
SELECT * FROM sys.innodb_lock_waits ORDER BY wait_age_secs DESC LIMIT N;

# 要特别关注的大事务
SELECT * FROM information_schema.innodb_trx WEHRE
  trx_lock_structs >= 5 OR    -- 超过5把锁
  trx_rows_locked >= 100 OR   -- 超过100行被锁
  trx_rows_modified >= 100 OR -- 超过100行被修改
  TIME_TO_SEC(TIMEDIFF(NOW(),trx_started)) > 100;    -- 事务活跃超过100秒
```
当然了，上述这些监控SQL的阈值可根据实际情况自行适当调整。

### 2.4 网络存在瓶颈
一般来说，最好是在局域网内运行MGR，甚至在同一个VLAN里运行，使得网络质量尽量有保证。

如果怀疑是因为网络质量比较差导致MGR性能问题的话，可以通过设置选项 `group_replication_request_time_threshold` 记录那些因为网络延迟较大导致的MGR性能瓶颈（这个选项在GreatSQL中才有，MySQL不支持）。这个选项的单位是毫秒，如果是在局域网内，可以设置为10-50（毫秒）左右；如果是网络质量较差或者跨公网的环境，可以设置为100-10000（即100毫秒 - 10秒）之间。

### 2.5 其他MySQL性能瓶颈因素
其他因素导致的MySQL性能瓶颈，可以参考这篇文章 [比较全面的MySQL优化参考（上篇）](https://mp.weixin.qq.com/s/V51yKzCKUSIm28sMhvQl8Q) 和 [比较全面的MySQL优化参考（下篇）](https://mp.weixin.qq.com/s/p2IBlGguf4Vaq_AO_jja9A)。

## 小结
本文介绍了MGR几个性能优化建议。

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
