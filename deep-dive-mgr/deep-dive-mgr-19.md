# 19. GreatSQL特性 | 深入浅出MGR

[toc]

本文介绍GreatSQL的一些关键新特性，相关特性主要针对GreatSQL 8.0.x版本（不含GreatSQL 5.7.x版本中的相关特性）。

## 1. 地理标签
可以对每个节点设置地理标签，主要用于解决多机房数据同步的问题。

新增选项 `group_replication_zone_id`，用于标记节点地理标签。该选项值支持范围 0 ~ 8，默认值为0。

当集群中各节点该选项值设置为不同的时候，就被认定为设置了不同的地理标签。

在同城多机房部署方案中，同一个机房的节点可以设置相同的数值，另一个机房里的节点设置另一个不同的数值，这样在事务提交时会要求每组 `group_replication_zone_id` 中至少
有个节点确认事务，然后才能继续处理下一个事务。这就可以确保每个机房的某个节点里，总有最新的事务。

| System Variable Name  | group_replication_zone_id |
| --- | --- |
| Variable Scope        | global |
| Dynamic Variable      | YES |
| Permitted Values |    [0 ~ 8] |
| Default       | 0 |
| Description   | 设置MGR各节点不同的地理标签，主要用于解决多机房数据同步的问题。<br/>修改完该选项值之后，要重启MGR线程才能生效。 |
| 引入版本 | 8.0.25-15 |

## 2. 仲裁节点
该节点仅参与MGR投票仲裁，不存放实际数据，也无需执行DML操作，因此可以用一般配置级别的服务器，在保证MGR可靠性的同时还能降低服务器成本。

新增参数```group_replication_arbitrator```用于设置仲裁节点。

若想新增一个仲裁节点，只需在 `my.cnf` 配置文件中添加如下配置：
`group_replication_arbitrator = true`

当集群中只剩下 Arbitrator 节点时，则会自动退出。

**注意：**
1. 在有仲裁节点的情况下，将单主切换成多主模式时，需要把投票节点先关闭再继续切换，否则可能会导致切换失败，并且仲裁节点报错退出MGR。
2. 即便是在关闭MGR服务状态下，仲裁节点中也无法执任何有数据变更的操作。

| System Variable Name  | group_replication_arbitrator |
| --- | --- |
| Variable Scope        | global |
| Dynamic Variable      | NO |
| Permitted Values |   0|1 |
| Default       | 0 |
| Description   | 设置本节点是否为仲裁节点。实例启动前先设置好，不可动态修改 |
| 引入版本 | 8.0.25-16 |

## 3. 快速单主
GreatSQL中增加一个新的工作模式：**单主快速模式**，在这个模式下，不再采用MySQL MGR原有的认证数据库方式。新增选项 `group_replication_single_primary_fast_mode` 用于
设置是否启用，以及具体采用哪种模式。

快速单主模式特别适合在跨机房部署，压力测试以及内存要求不高等多种场景。这种模式弱于传统的异步复制，但强于半同步复制，且没有MGR默认的认证数据库可能消耗较大内存的问
题。

**提醒**，启用快速单主模式时，不支持采用多主模式；所有节点都得设置必须相同，否则无法启动。

选项 `group_replication_single_primary_fast_mode` 可选值有：0、1、2，不同值分别表示如下：
- 0，表示不采取快速单主模式，这是默认值。
- 1，表示采用快速单主模式，支持并行回放。**强烈建议设置为1，即启用快速单主模式。
**- 2，表示采用快速单主模式，但不支持并行回放，加速relay log落盘，且让从库消耗更少的资源。

| System Variable Name    | group_replication_single_primary_fast_mode |
| --- | --- |
| Variable Scope    | Global |
| Dynamic Variable    | NO |
| Permitted Values |    0<br/>1<br/>2 |
| Default    | 0 |
| Description    | 设置是否启用快速单主模式，强烈建议启用（即设置为1）。|
| 引入版本 | 8.0.25-16 |

## 4. 自定义选主策略
完善自动选主机制，增加基于最新GTID判断来选主，避免自动选择没有最新GTID的节点作为新主。

默认地，MGR根据以下规则选主：
1. 当有MySQL 5.7和MySQL 8.0不同版本的节点混合部署时，只会选择运行5.7的节点作为主节点。此外，在 <= MySQL 8.0.16 版本时，以主版本号进行排序，也就是说 5.7 排在 8.0
前面。在 > MySQL 8.0.17版本中，则是以补丁版本号排序，也就是 8.0.17 排在 8.0.25 前面。
2. 当所有节点版本号一致时，则根据节点权重值（选项 group_replication_member_weight 定义权重值，这个选项5.7版本没有，8.0开始新增）排序，权重值高的节点排在前面。
3. 根据节点 server_uuid 排序。

在一些情况下，在MGR所有节点都发生意外要重新拉起时，不会检查各节点事务应用状态，而错误选择新的主节点，这时可能会导致丢失一些事务数据。或者当原来的主节点crash需要
重新投票选择新的主节点时，可能也会选择一个权重值较高，但没有最新事务的节点，也会存在丢失一部分事务数据的风险。

在GreatSQL中，新增选项 `group_replication_primary_election_mode` 用于自定义选主策略，可选值有以下几个：
- WEIGHT_ONLY，还是按照上述传统模式自动选主，这是默认值。
- GTID_FIRST，优先判断各节点事务应用状态，自动选择拥有最新事务的节点作为新的主节点。**推荐设置为该模式。**
- WEIGHT_FIRST，传统模式优先，如果没有合适的结果再判断各节点事务状态。

**提醒**，所有节点都的设置必须相同，否则无法启动。

| System Variable Name    | group_replication_primary_election_mode |
| --- | --- |
| Variable Scope    | Global |
| Dynamic Variable    | NO |
| Permitted Values |    WEIGHT_ONLY<br/>GTID_FIRST<br/>WEIGHT_FIRST |
| Default    | WEIGHT_ONLY |
| Description    | 当MGR集群需要投票选主时，采用何种投票策略。|
| 引入版本 | 8.0.25-16 |

## 5. 并行查询
根据B+树的特点，可以将B+树划分为若干子树，此时多个线程可以并行扫描同一张InnoDB表的不同部分。对执行计划进行多线程改造，每个子线程执行计划与MySQL原始执行计划一致，
但每个子线程只需扫描表的部分数据，子线程扫描完成后再进行结果汇总。通过多线程改造，可以充分利用多核资源，提升查询性能。

优化后，在TPC-H测试中表现优异，最高可提升30倍，平均提升15倍。该特性适用于周期性数据汇总报表之类的SAP、财务统计等业务。

使用限制：
- 暂不支持子查询，可想办法改造成JOIN。

![输入图片说明](https://images.gitee.com/uploads/images/2021/0819/094317_1c0fb43a_8779455.jpeg "16292668686865.jpg")

| System Variable Name    | force_parallel_execute |
| --- | --- |
| Variable Scope    | Global |
| Dynamic Variable    | YES |
| Permitted Values |   ON | OFF |
| Default    | OFF |
| Description    | 是否启用InnoDB并行查询特性 |
| 引入版本 | 8.0.25-15 |

更多关于InnoDB并行查询相关选项参考文档 [InnoDB并行查询优化参考](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/innodb-parallel-execute.md)。


## 6. GreatSQL VS MySQL社区版

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


## 免责声明
因个人水平有限，专栏中难免存在错漏之处，请勿直接复制文档中的命令、方法直接应用于线上生产环境。请读者们务必先充分理解并在测试环境验证通过后方可正式实施，避免造成生产环境的破坏或损害。

## 加入团队
如果您有兴趣一起加入协作，欢迎联系我们，可直接提交PR，或者将内容以markdown的格式发送到邮箱：greatsql@greatdb.com。

亦可通过微信、QQ联系我们。

![Contact Us](../docs/contact-us.png)
