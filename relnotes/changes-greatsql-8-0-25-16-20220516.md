# Changes in GreatSQL 8.0.25-16（2022-5-16）
---
[toc]

## 1.新增特性
### 1.1 新增仲裁节点（投票节点）角色
该节点仅参与MGR投票仲裁，不存放实际数据，也无需执行DML操作，因此可以用一般配置级别的服务器，在保证MGR可靠性的同时还能降低服务器成本。

新增参数```group_replication_arbitrator```用于设置仲裁节点。

若想新增一个仲裁节点，只需在 `my.cnf` 配置文件中添加如下配置：
`group_replication_arbitrator = true`

当集群中只剩下 Arbitrator 节点时，则会自动退出。
```
mysql> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+----------------------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST  | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION | MEMBER_COMMUNICATION_STACK |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+----------------------------+
| group_replication_applier | 4b2b46e2-3b13-11ec-9800-525400fb993a | 172.16.16.16 |        3306 | ONLINE       | SECONDARY   | 8.0.27         | XCom                       |
| group_replication_applier | 4b51849b-3b13-11ec-a180-525400e802e2 | 172.16.16.10 |        3306 | ONLINE       | ARBITRATOR  | 8.0.27         | XCom                       |
| group_replication_applier | 4b7b3b88-3b13-11ec-86e9-525400e2078a | 172.16.16.53 |        3306 | ONLINE       | PRIMARY     | 8.0.27         | XCom                       |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+----------------------------+
```
可以看到，`MEMBER_ROLE` 这列显示为 **ARBITRATOR**，表示该节点是一个仲裁节点。

再看压测期间各节点负载数据，先看 **Primary** 节点：
```
$ top
...
  PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
20198 mysql     20   0   11.9g   3.4g  23440 S 207.6 21.6  21:33.48 mysqld

$ vmstat -S m 1
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  3      0   5637    152   6385    0    0     0 56311 53024 53892 36 17 43  3  0
 0  3      0   5633    152   6389    0    0     0 46053 51900 52435 35 17 44  4  0
 6  0      0   5628    152   6393    0    0     0 47024 52026 52388 36 17 44  3  0
 7  1      0   5623    152   6397    0    0     0 51673 52165 53113 36 17 43  3  0
 3  1      0   5621    152   6401    0    0     0 44231 52164 52875 35 17 45  3  0
 3  4      0   5616    152   6404    0    0     0 49278 52854 53139 37 17 43  3  0
 4  0      0   5613    152   6408    0    0     0 49738 52848 53361 37 17 43  3  0
```

在其中一个 **Secondary** 节点上：
```
$ top
...
  PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
26824 mysql     20   0   11.6g   3.0g  22880 S 175.7 19.4  19:27.34 mysqld

$ vmstat -S m 1
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 2  0      0   2089    128  10757    0    0     0 53671 31463 46803 30 11 55  4  0
 3  0      0   2082    128  10765    0    0     0 52737 31475 45862 30 11 55  4  0
 2  0      0   2073    128  10772    0    0     0 52121 31035 45820 29 12 55  4  0
 3  0      0   2065    128  10781    0    0     0 51469 31081 44831 30 12 55  4  0
 1  0      0   2057    128  10788    0    0     0 53071 31442 45664 30 11 55  4  0
 3  0      0   2049    128  10795    0    0     0 51357 29848 43391 30 12 54  4  0
 0  0      0   2041    128  10803    0    0     0 52404 30545 45020 29 12 56  4  0
 3  0      0   2034    128  10811    0    0     0 51355 31483 45582 32 12 53  3  0
```

在 **Arbitrator** 节点上：
```
$ top
...
  PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
16997 mysql     20   0   11.2g   2.5g  22184 S  29.6 16.4   3:47.84 mysqld

$ vmstat -S m 1
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0      0   6145    141   7095    0    0     0    44 17767 16010  4  4 93  0  0
 1  0      0   6146    141   7095    0    0     0     0 17020 16189  4  4 93  0  0
 0  0      0   6144    141   7095    0    0     0     0 16958 15365  3  4 93  0  0
 0  0      0   6145    141   7095    0    0     0     0 15942 14969  3  3 93  0  0
 1  0      0   6146    141   7095    0    0     0     0 17698 16320  4  4 92  0  0
```
可以看到负载明显小了很多，这就可以在一个服务器上跑多个仲裁节点角色。

**注意：** 在有仲裁节点的情况下，将单主切换成多主模式时，需要把投票节点先关闭再机型切换，否则可能会导致切换失败，并且仲裁节点报错退出MGR。

### 1.2 新增快速单主模式
GreatSQL中增加一个新的工作模式：**单主快速模式**，在这个模式下，不再采用MySQL MGR原有的认证数据库方式。新增选项 `group_replication_single_primary_fast_mode` 用于设置是否启用，以及具体采用哪种模式。

快速单主模式特别适合在跨机房部署，压力测试以及内存要求不高等多种场景。这种模式弱于传统的异步复制，但强于半同步复制，且没有MGR默认的认证数据库可能消耗较大内存的问题。

**提醒**，启用快速单主模式时，不支持采用多主模式；所有节点都得设置必须相同，否则无法启动。

选项 `group_replication_single_primary_fast_mode` 可选值有：0、1、2，不同值分别表示如下：
- 0，表示不采取快速单主模式，这是默认值。
- 1，表示采用快速单主模式，支持并并回放。**强烈建议设置为1，即启用快速单主模式。
**- 2，表示采用快速单主模式，但不支持并行回放，加速relay log落盘，且让从库消耗更少的资源。

| System Variable Name    | group_replication_single_primary_fast_mode |
| --- | --- | 
| Variable Scope    | Global |
| Dynamic Variable    | NO |
| Permitted Values |    0<br/>1<br/>2 |
| Default    | 0 |
| Description    | 设置是否启用快速单主模式，强烈建议启用（即设置为1）。|

### 1.3 新增MGR网络开销阈值
新增相应选项 `group_replication_request_time_threshold`。

在MGR结构中，一个事务的开销包含网络层以及本地资源（例如CPU、磁盘I/O等）开销。当事务响应较慢想要分析性能瓶颈时，可以先确定是网络层的开销还是本地性能瓶颈导致的。通过设置选项 `group_replication_request_time_threshold` 即可记录超过阈值的事件，便于进一步分析。输出的内容记录在error log中，例如：
```
2022-03-04T09:45:34.602093+08:00 128 [Note] Plugin group_replication reported: 'MGR request time:30808us, server id:3306879, thread_id:17368'
```
表示当时这个事务在MGR层的网络开销耗时30808微秒（30.808毫秒），再去查看那个时段的网络监控，分析网络延迟较大的原因。

选项 `group_replication_request_time_threshold` 单位是毫秒，默认值是0，最小值0，最大值100000。如果MGR跑在局域网环境，则建议设置为50 ~ 100毫秒区间，如果是运行在跨公网环境，则建议设置为1 ~ 10秒左右。另外，当该值设置为1 ~ 9之间时，会自动调整为10（毫秒）且不会提示warning，如果设置为0则表示禁用。

| System Variable Name    | group_replication_request_time_threshold |
| --- | --- | 
| Variable Scope    | Global |
| Dynamic Variable    | YES |
| Permitted Values |    [0 ~ 100000] |
| Default    | 0 |
| Description    |单位：毫秒。<br/>设置阈值，当一个事务的MGR层网络开销超过该阈值时，会在error log中输出一条记录。<br/>设置为0时，表示禁用。<br/>当怀疑可能因为MGR通信耗时过久成为事务性能瓶颈时，再开启，平时不建议开启。|

### 1.4 自定义选主模式
完善自动选主机制，增加基于最新GTID判断来选主，避免自动选择没有最新GTID的节点作为新主。

默认地，MGR根据以下规则选主：
1. 当有MySQL 5.7和MySQL 8.0不同版本的节点混合部署时，只会选择运行5.7的节点作为主节点。此外，在 <= MySQL 8.0.16 版本时，以主版本号进行排序，也就是说 5.7 排在 8.0 前面。在 > MySQL 8.0.17版本中，则是以补丁版本号排序，也就是 8.0.17 排在 8.0.25 前面。
2. 当所有节点版本号一致时，则根据节点权重值（选项 group_replication_member_weight 定义权重值，这个选项5.7版本没有，8.0开始新增）排序，权重值高的节点排在前面。
3. 根据节点 server_uuid 排序。

在一些情况下，在MGR所有节点都发生意外要重新拉起时，不会检查各节点事务应用状态，而错误选择新的主节点，这时可能会导致丢失一些事务数据。或者当原来的主节点crash需要重新投票选择新的主节点时，可能也会选择一个权重值较高，但没有最新事务的节点，也会存在丢失一部分事务数据的风险。

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

## 2.稳定性提升
1. 优化了加入节点时可能导致性能剧烈抖动的问题。
2. 优化手工选主机制，解决了长事务造成无法选主的问题。
3. 完善MGR中的外键约束机制，降低或避免从节点报错退出MGR的风险。

## 3.其他调整
1. 选项 `group_replication_flow_control_replay_lag_behind` 默认值由60秒调整为600秒，以适应更多业务场景。该选项用于控制MGR主从节点复制延迟阈值，当MGR主从节点因为大事务等原因延迟超过阈值时，就会触发流控机制。
2. 新增选项 `group_replication_communication_flp_timeout`（单位：秒）。当多数派节点超过该阈值为收到某节点发送的消息时，会将该节点判定为可疑节点。在网络条件较差的环境中，可以适当调大该阈值，以避免频繁抖动。
3. 新增选项 `group_replication_zone_id_sync_mode`（类型：布尔型，可选值：ON/OFF，默认值：ON）。如果设置了 `group_replication_zone_id` 启用地理标签功能，需要保证所有节点都同步数据。但当 `group_replication_zone_id_sync_mode = OFF` 时，地理标签就只是个标记，不再保证各节点都同步数据。


## 4.bug修复
01. 修复了InnoDB并行查询crash的问题（[issue#I4J1IH](https://gitee.com/GreatSQL/GreatSQL/issues/I4J1IH)）。
02. 修复了在启用dns或hostname的情况下，bind意外失败问题。
03. 修复了协程调度不合理的问题，该问题可能会造成在大事务时系统错误判断为网络错误。
04. 修复了新加入节点在追paxos数据时，由于write超时导致连接提前关闭的问题。
05. 修复了recovering节点被中途停止导致的数据异常问题。
06. 修复了同时多个异常导致的视图问题。
07. 修复了在某些场景下同时添加节点失败的问题。
08. 修复了在特殊场景下组视图异常的问题。
09. 修复了rejoin过程中，member_stats相关查询导致崩溃的问题。
10. 修复了在before模式下，可能导致assert失败的问题。
11. 修复了stop group_replication时可能长时间等待的问题。
12. 修复了将传统主从环境下产生的binlog导入MGR可能引起死循环的问题。
13. 修复了因为大事务内存分配失败导致的崩溃问题。

## 5. GreatSQL VS MySQL社区版

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

## 6. GreatSQL Release Notes
- [Changes in MySQL 8.0.25-16 (2022-5-16)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-16-20220516.md)
- [Changes in MySQL 8.0.25-15 (2021-8-26)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-20210820.md)
- [Changes in MySQL 5.7.36-39 (2022-4-7)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-5-7-36-20220407.md)
