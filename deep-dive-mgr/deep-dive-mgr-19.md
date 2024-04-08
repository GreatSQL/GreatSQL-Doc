# 19. GreatSQL特性 | 深入浅出MGR

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
- 1，表示采用快速单主模式，支持并行回放。**强烈建议设置为1，即启用快速单主模式**
- 2，表示采用快速单主模式，但不支持并行回放，加速relay log落盘，且让从库消耗更少的资源。

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

更多关于GreatSQL的优势特性详见：[优势特性](https://greatsql.cn/docs/8032-25/user-manual/1-docs-intro/1-3-greatsql-features.html)。

## 6. GreatSQL VS MySQL社区版

下面是GreatSQL 和 MySQL社区版本的对比表格：

| **1.主要特性** | GreatSQL 8.0.32-25 | MySQL 8.0.32 |
| :--- | :---: | :---: |
| 开源 |  :heavy_check_mark: |  :heavy_check_mark: |
|ACID完整性| :heavy_check_mark: | :heavy_check_mark: |
|MVCC特性| :heavy_check_mark:     | :heavy_check_mark: |
|支持行锁| :heavy_check_mark: | :heavy_check_mark: |
|Crash自动修复| :heavy_check_mark: | :heavy_check_mark: |
|表分区(Partitioning)| :heavy_check_mark: | :heavy_check_mark: |
|视图(Views)| :heavy_check_mark: | :heavy_check_mark: |
|子查询(Subqueries)| :heavy_check_mark: | :heavy_check_mark: |
|触发器(Triggers)| :heavy_check_mark: | :heavy_check_mark: |
|存储程序(Stored Programs)| :heavy_check_mark: | :heavy_check_mark: |
|外键(Foreign Keys)| :heavy_check_mark: | :heavy_check_mark: |
|窗口函数(Window Functions)| :heavy_check_mark: | :heavy_check_mark: |
|通用表表达式CTE| :heavy_check_mark: | :heavy_check_mark: |
|地理信息(GIS)| :heavy_check_mark: | :heavy_check_mark: |
|基于GTID的复制| :heavy_check_mark: | :heavy_check_mark: |
|组复制(MGR)| :heavy_check_mark: | :heavy_check_mark: |
|MyRocks引擎| :heavy_check_mark: | |
| **2. 性能提升扩展** | GreatSQL 8.0.32-25 | MySQL 8.0.32 |
|AP引擎| :heavy_check_mark: | 仅云上HeatWave |
|InnODB并行查询| :heavy_check_mark: | 仅主键扫描 |
|并行LOAD DATA| :heavy_check_mark: | ❌ |
|InnoDB事务ReadView无锁优化| :heavy_check_mark: | ❌ |
|InnoDB事务大锁拆分优化| :heavy_check_mark: | ❌ |
|InnoDB资源组| :heavy_check_mark: | :heavy_check_mark: |
|自定义InnoDB页大小| :heavy_check_mark: | :heavy_check_mark: |
|Contention-Aware Transaction Scheduling| :heavy_check_mark: | :heavy_check_mark: |
|InnoDB Mutexes拆分优化| :heavy_check_mark: | ❌ |
|MEMORY引擎优化| :heavy_check_mark: | ❌ |
|InnoDB Flushing优化| :heavy_check_mark: | ❌ |
|并行Doublewrite Buffer| :heavy_check_mark: | :heavy_check_mark: |
|InnoDB快速索引创建优化| :heavy_check_mark: | ❌ |
|VARCHAR/BLOB/JSON类型存储单列压缩| :heavy_check_mark: | ❌ |
|数据字典中存储单列压缩信息| :heavy_check_mark: | ❌ |
| **3. 面向开发者提升改进** | GreatSQL 8.0.32-25 | MySQL 8.0.32 |
|X API| :heavy_check_mark: | :heavy_check_mark: |
|JSON| :heavy_check_mark: | :heavy_check_mark: |
|NoSQL Socket-Level接口| :heavy_check_mark: | :heavy_check_mark: |
|InnoDB全文搜索改进| :heavy_check_mark: | ❌ |
|更多Hash/Digest函数| :heavy_check_mark: | ❌ |
|Oracle兼容-数据类型| :heavy_check_mark: | ❌ |
|Oracle兼容-函数| :heavy_check_mark: | ❌ |
|Oracle兼容-SQL语法| :heavy_check_mark: | ❌ |
|Oracle兼容-存储程序| :heavy_check_mark: | ❌ |
| **4. 基础特性提升改进** | GreatSQL 8.0.32-25 | MySQL 8.0.32 |
|MGR提升-地理标签| :heavy_check_mark: | ❌ |
|MGR提升-仲裁节点| :heavy_check_mark: | ❌ |
|MGR提升-读写节点绑定VIP| :heavy_check_mark: | ❌ |
|MGR提升-快速单主模式| :heavy_check_mark: | ❌ |
|MGR提升-智能选主机制| :heavy_check_mark: | ❌ |
|MGR提升-全新流控算法| :heavy_check_mark: | ❌ |
|information_schema表数量|95|65|
|全局性能和状态指标|853|434|
|优化器直方图(Histograms)| :heavy_check_mark: | :heavy_check_mark: |
|Per-Table性能指标| :heavy_check_mark: | ❌ |
|Per-Index性能指标| :heavy_check_mark: | ❌ |
|Per-User性能指标| :heavy_check_mark: | ❌ |
|Per-Client性能指标| :heavy_check_mark: | ❌ |
|Per-Thread性能指标| :heavy_check_mark: | ❌ |
|全局查询相应耗时统计| :heavy_check_mark: | ❌ |
|SHOW INNODB ENGINE STATUS增强| :heavy_check_mark: | ❌ |
|回滚段信息增强| :heavy_check_mark: | ❌ |
|临时表信息增强| :heavy_check_mark: | ❌ |
|用户统计信息增强| :heavy_check_mark: | ❌ |
|Slow log信息增强| :heavy_check_mark: | ❌ |
| **5.安全性提升** | GreatSQL 8.0.32-25 | MySQL 8.0.32 |
|国密支持| :heavy_check_mark: | ❌ |
|备份加密| :heavy_check_mark: | ❌ |
|审计日志入库| :heavy_check_mark: | ❌ |
|SQL Roles| :heavy_check_mark: | :heavy_check_mark: |
|SHA-2密码Hashing| :heavy_check_mark: | :heavy_check_mark: |
|密码轮换策略| :heavy_check_mark: | :heavy_check_mark: |
|PAM认证插件| :heavy_check_mark: | 仅企业版 |
|审计插件| :heavy_check_mark: | 仅企业版 |
|Keyring存储在文件中| :heavy_check_mark: | :heavy_check_mark: |
|Keyring存储在Hashicorp Vault中| :heavy_check_mark: | 仅企业版 |
|InnoDB数据加密| :heavy_check_mark: | :heavy_check_mark: |
|InnoDB日志加密| :heavy_check_mark: | :heavy_check_mark: |
|InnoDB各种表空间文件加密| :heavy_check_mark: | :heavy_check_mark: |
|二进制日志加密| :heavy_check_mark: | ❌ |
|临时文件加密| :heavy_check_mark: | ❌ |
|强制加密| :heavy_check_mark: | ❌ |
| **6. 运维便利性提升** | GreatSQL 8.0.32-25 | MySQL 8.0.32 |
|DDL原子性| :heavy_check_mark: | :heavy_check_mark: |
|数据字典存储InnoDB表| :heavy_check_mark: | :heavy_check_mark: |
|快速DDL| :heavy_check_mark: | :heavy_check_mark: |
|SET PERSIST| :heavy_check_mark: | :heavy_check_mark: |
|不可见索引| :heavy_check_mark: | :heavy_check_mark: |
|线程池(Threadpool)| :heavy_check_mark: | 仅企业版 |
|备份锁| :heavy_check_mark: | ❌ |
|SHOW GRANTS扩展| :heavy_check_mark: | ❌ |
|表损坏动作扩展| :heavy_check_mark: | ❌ |
|杀掉不活跃事务| :heavy_check_mark: | ❌ |
|START TRANSACTION WITH CONSISTENT SNAPSHOT扩展| :heavy_check_mark: | ❌ |

此外，GreatSQL 8.0.32-25基于Percona Server for MySQL 8.0.32版本，它在MySQL 8.0.32基础上做了大量的改进和提升以及众多新特性，详情请见：[**Percona Server for MySQL feature comparison**](https://docs.percona.com/percona-server/8.0/feature-comparison.html)，这其中包括线程池、审计、数据脱敏等MySQL企业版才有的特性，以及performance_schema提升、information_schema提升、性能和可扩展性提升、用户统计增强、PROCESSLIST增强、Slow log增强等大量改进和提升，这里不一一重复列出。

GreatSQL同时也是gitee（码云）平台上的GVP项目，详见：[https://gitee.com/gvp/database-related](https://gitee.com/gvp/database-related) **数据库相关**类目。

## 免责声明
因个人水平有限，专栏中难免存在错漏之处，请勿直接复制文档中的命令、方法直接应用于线上生产环境。请读者们务必先充分理解并在测试环境验证通过后方可正式实施，避免造成生产环境的破坏或损害。

## 加入团队
如果您有兴趣一起加入协作，欢迎联系我们，可直接提交PR，或者将内容以markdown的格式发送到邮箱：greatsql@greatdb.com。

亦可通过微信、QQ联系我们。

![Contact Us](../docs/contact-us.png)
