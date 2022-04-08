# 6. MGR状态监控 | 深入浅出MGR

[toc]

MGR和传统主从复制类似，在运行过程中主要关注各节点的运行状态，以及Secondary节点的事务是否有延迟。本文介绍如何监控MGR节点状态、事务状态等。

## 1. 节点状态监控
通过查询 `performance_schema.replication_group_members` 表即可知道MGR各节点的状态：
```
mysql> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST  | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | af39db70-6850-11ec-94c9-00155d064000 | 192.168.6.27 |        4306 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | b05c0838-6850-11ec-a06b-00155d064000 | 192.168.6.27 |        4307 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | b0f86046-6850-11ec-92fe-00155d064000 | 192.168.6.27 |        4308 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
输出结果中主要几个列的解读如下：
- **MEMBER_ID** 列值就是各节点的 **server_uuid**，用于唯一标识每个节点，在命令行模式下，调用 udf 时传入 MEMBER_ID 以指定各节点。
- **MEMBER_ROLE** 表示各节点的角色，如果是 **PRIMARY** 则表示该节点可接受读写事务，如果是 **SECONDARY** 则表示该节点只能接受只读事务。如果只有一个节点是 PRIMARY，其余都是 SECONDARY，则表示当前处于 **单主模式**；如果所有节点都是 PRIMARY，则表示当前处于 **多主模式**。
- **MEMBER_STATE** 表示各节点的状态，共有几种状态：ONLINE、RECOVERING、OFFLINE、ERROR、UNREACHABLE 等，下面分别介绍几种状态。
    - **ONLINE**，表示节点处于正常状态，可提供服务。
    - **RECOVERING**，表示节点正在进行分布式恢复，等待加入集群，这时候有可能正在从donor节点利用clone复制数据，或者传输binlog中。
    - **OFFLINE**，表示该节点当前处于离线状态。提醒，在正要加入或重加入集群时，可能也会有很短瞬间的状态显示为 OFFLINE。
    - **ERROR**，表示该节点当前处于错误状态，无法成为集群的一员。当节点正在进行分布式恢复或应用事务时，也是有可能处于这个状态的。当节点处于ERROR状态时，是无法参与集群事务裁决的。节点正在加入或重加入集群时，在完成兼容性检查成为正式MGR节点前，可能也会显示为ERROR状态。
    - **UNREACHABLE**，当组通信消息收发超时时，故障检测机制会将本节点标记为怀疑状态，怀疑其可能无法和其他节点连接，例如当某个节点意外断开连接时。当在某个节点上看到其他节点处于 UNREACHABLE 状态时，有可能意味着此时部分节点发生了网络分区，也就是多个节点分裂成两个或多个子集，子集内的节点可以互通，但子集间无法互通。

当节点的状态不是 ONLINE 时，就应当立即发出告警并检查发生了什么。

在节点状态发生变化时，或者有节点加入、退出时，表 `performance_schema.replication_group_members` 的数据都会更新，各节点间会交换和共享这些状态信息，因此可以在任意节点查看。

## 2. MGR事务状态监控
另一个需要重点关注的是Secondary节点的事务状态，更确切的说是关注待认证事务及待应用事务队列大小。

可以执行下面的命令查看当前除了 **PRIMARY** 节点外，其他节点的 `trx_tobe_certified` 或 `relaylog_tobe_applied` 值是否较大：
```
[root@GreatSQL]> SELECT MEMBER_ID AS id, COUNT_TRANSACTIONS_IN_QUEUE AS trx_tobe_certified, COUNT_TRANSACTIONS_REMOTE_IN_APPLIER_QUEUE AS relaylog_tobe_applied, COUNT_TRANSACTIONS_CHECKED AS trx_chkd, COUNT_TRANSACTIONS_REMOTE_APPLIED AS trx_done, COUNT_TRANSACTIONS_LOCAL_PROPOSED AS proposed FROM performance_schema.replication_group_member_stats;
+--------------------------------------+-------------------+---------------------+----------+----------+----------+
| id                                   |trx_tobe_certified |relaylog_tobe_applied| trx_chkd | trx_done | proposed |
+--------------------------------------+-------------------+---------------------+----------+----------+----------+
| 4ebd3504-11d9-11ec-8f92-70b5e873a570 |                 0 |                   0 |   422248 |        6 |   422248 |
| 549b92bf-11d9-11ec-88e1-70b5e873a570 |                 0 |              238391 |   422079 |   183692 |        0 |
| 5596116c-11d9-11ec-8624-70b5e873a570 |              2936 |              238519 |   422115 |   183598 |        0 |
| ed5fe7ba-37c2-11ec-8e12-70b5e873a570 |              2976 |              238123 |   422167 |   184044 |        0 |
+--------------------------------------+-------------------+---------------------+----------+----------+----------+
```
其中，`relaylog_tobe_applied` 的值表示远程事务写到relay log后，等待回放的事务队列，`trx_tobe_certified` 表示等待被认证的事务队列大小，这二者任何一个值大于0，都表示当前有一定程度的延迟。

还可以通过关注上述两个数值的变化，看看两个队列是在逐步加大还是缩小，据此判断Primary节点是否"跑得太快"了，或者Secondary节点是否"跑得太慢"。

多提一下，在启用流控（flow control）时，上述两个值超过相应的阈值时（group_replication_flow_control_applier_threshold 和 group_replication_flow_control_certifier_threshold 默认阈值都是 25000），就会触发流控机制。

## 3. 其他监控
另外，也可以查看接收到的事务和已执行完的事务之间的差距来判断：
```
mysql> SELECT RECEIVED_TRANSACTION_SET FROM performance_schema.replication_connection_status WHERE  channel_name = 'group_replication_applier' UNION ALL SELECT variable_value FROM performance_schema.global_variables WHERE  variable_name = 'gtid_executed'\G
*************************** 1. row ***************************
RECEIVED_TRANSACTION_SET: 6cfb873b-573f-11ec-814a-d08e7908bcb1:1-3124520
*************************** 2. row ***************************
RECEIVED_TRANSACTION_SET: 6cfb873b-573f-11ec-814a-d08e7908bcb1:1-3078139
```
可以看到，接收到的事务 GTID 已经到了 3124520，而本地只执行到 3078139，二者的差距是 46381。

可以顺便持续关注这个差值的变化情况，估算出本地节点是否能及时追平延迟，还是会加大延迟。

另外，当原来的主节点发生故障，想要手动选择某个节点做为新的主节点时，也应该先判断哪个节点已执行的事务GTID值更大，应优先选择该节点。

## 4. 小结
本文介绍了MGR监控的主要关注点，包括节点状态以及复制延迟状态，以及如何预判复制延迟会继续扩大还是能及时追上的方法。

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