# Changes in GreatSQL 8.0.25-16 (2022-5-16)
---
[toc]

## 1. New features
### 1.1 Add the role of arbitrator node (voting node)
This node only participates in the MGR voting arbitration, does not store user data and binary logs, and does not need to apply relay logs. Therefore, a very cheap server can be used to ensure the reliability of MGR and reduce server costs.

Added parameter `group_replication_arbitrator` for setting the arbiter node.

To add a new quorum node, just add the following configuration to the `my.cnf` configuration file:
`group_replication_arbitrator=true`

When only Arbitrator nodes remain in the MGR cluster, they will automatically exit.
````
mysql> select * from performance_schema.replication_group_members;
+--------------------------+--------------------- -----------------+-------------+-------------+--- -------------+-------------+----------------+------- ---------------------+
| CHANNEL_NAME | MEMBER_ID | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION | MEMBER_COMMUNICATION_STACK |
+--------------------------+--------------------- -----------------+-------------+-------------+--- -------------+-------------+----------------+------- ---------------------+
| group_replication_applier | 4b2b46e2-3b13-11ec-9800-525400fb993a | 172.16.16.16 | 3306 | ONLINE | SECONDARY | 8.0.27 | XCom |
| group_replication_applier | 4b51849b-3b13-11ec-a180-525400e802e2 | 172.16.16.10 | 3306 | ONLINE | ARBITRATOR | 8.0.27 | XCom |
| group_replication_applier | 4b7b3b88-3b13-11ec-86e9-525400e2078a | 172.16.16.53 | 3306 | ONLINE | PRIMARY | 8.0.27 | XCom |
+--------------------------+--------------------- -----------------+-------------+-------------+--- -------------+-------------+----------------+------- ---------------------+
````
As you can see, the `MEMBER_ROLE` column is displayed as **ARBITRATOR**, indicating that the node is an arbitrator node.

Then look at the system load of each node during the benchmark, first look at the **Primary** node:
````
$ top
...
  PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
20198 mysql 20 0 11.9g 3.4g 23440 S 207.6 21.6 21:33.48 mysqld

$ vmstat -S m 1
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu -----
 r b swpd free buff cache si so bi bo in cs us sy id wa st
 1 3 0 5637 152 6385 0 0 0 56311 53024 53892 36 17 43 3 0
 0 3 0 5633 152 6389 0 0 0 46053 51900 52435 35 17 44 4 0
 6 0 0 5628 152 6393 0 0 0 47024 52026 52388 36 17 44 3 0
 7 1 0 5623 152 6397 0 0 0 51673 52165 53113 36 17 43 3 0
 3 1 0 5621 152 6401 0 0 0 44231 52164 52875 35 17 45 3 0
 3 4 0 5616 152 6404 0 0 0 49278 52854 53139 37 17 43 3 0
 4 0 0 5613 152 6408 0 0 0 49738 52848 53361 37 17 43 3 0
````

On one of the **Secondary** nodes:
````
$ top
...
  PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
26824 mysql 20 0 11.6g 3.0g 22880 S 175.7 19.4 19:27.34 mysqld

$ vmstat -S m 1
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu -----
 r b swpd free buff cache si so bi bo in cs us sy id wa st
 2 0 0 2089 128 10757 0 0 0 53671 31463 46803 30 11 55 4 0
 3 0 0 2082 128 10765 0 0 0 52737 31475 45862 30 11 55 4 0
 2 0 0 2073 128 10772 0 0 0 52121 31035 45820 29 12 55 4 0
 3 0 0 2065 128 10781 0 0 0 51469 31081 44831 30 12 55 4 0
 1 0 0 2057 128 10788 0 0 0 53071 31442 45664 30 11 55 4 0
 3 0 0 2049 128 10795 0 0 0 51357 29848 43391 30 12 54 4 0
 0 0 0 2041 128 10803 0 0 0 52404 30545 45020 29 12 56 4 0
 3 0 0 2034 128 10811 0 0 0 51355 31483 45582 32 12 53 3 0
````

On the **Arbitrator** node:
````
$ top
...
  PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
16997 mysql 20 0 11.2g 2.5g 22184 S 29.6 16.4 3:47.84 mysqld

$ vmstat -S m 1
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu -----
 r b swpd free buff cache si so bi bo in cs us sy id wa st
 1 0 0 6145 141 7095 0 0 0 44 17767 16010 4 4 93 0 0
 1 0 0 6146 141 7095 0 0 0 0 17020 16189 4 4 93 0 0
 0 0 0 6144 141 7095 0 0 0 0 16958 15365 3 4 93 0 0
 0 0 0 6145 141 7095 0 0 0 0 15942 14969 3 3 93 0 0
 1 0 0 6146 141 7095 0 0 0 0 17698 16320 4 4 92 0 0
````
It can be seen that the system load is significantly lower, which makes it possible to run multiple arbitrator node roles on one server.

**Note:** When there is an arbitrator node, when switching from single-master to multi-master mode, you need to turn off the arbitrator node first and then switch the mode, otherwise the switch may fail, and the arbitrator node will report an error and exit MGR.

### 1.2 Added single primary fast mode
A new working mode has been added to GreatSQL: **single-primary fast mode**. In this mode, the original certification database of MGR is no longer used. The new option `group_replication_single_primary_fast_mode` is used to set whether to enable and which mode to use.

The fast single-primary mode is especially suitable for multiple scenarios such as cross IDCs deployment, benchmark, and low memory. This mode is slower than asynchronous replication, but faster than semi-synchronous replication, and does not have the problem that MGR's default certification database may consume a lot of memory.

**Reminder**, when fast single-master mode is enabled, multi-master mode is not supported; an all nodes must have the same settings, otherwise MGR cannot be started.

Option `group_replication_single_primary_fast_mode` optional values ​​are: 0, 1, 2:
- 0, do not take fast single-primary mode, which is the default value.
- 1, the fast single-master mode is adopted, which supports relay logs applied parallelly. **Highly recommended to set to 1, enable fast single master mode.
**- 2, which means fast single-master mode is used, but relay logs applied parallelism is not supported.

| System Variable Name | group_replication_single_primary_fast_mode |
| --- | --- |
| Variable Scope | Global |
| Dynamic Variable | NO |
| Permitted Values ​​| 0<br/>1<br/>2 |
| Default | 0 |
| Description | Set whether to enable fast single master mode, it is strongly recommended to enable (set to 1). |

### 1.3 Added MGR network overhead threshold
Added new option `group_replication_request_time_threshold`.

In MGR, the overhead of a transaction includes network layer and local resource (such as CPU, disk I/O, etc.) overhead. When the transaction response is slow and you want to analyze the performance bottleneck, you can first determine whether it is caused by the overhead of the network layer or the local resource performance bottleneck. Events exceeding the threshold can be logged by setting the option `group_replication_request_time_threshold` for further analysis. The output is recorded in the error log, for example:
````
2022-03-04T09:45:34.602093+08:00 128 [Note] Plugin group_replication reported: 'MGR request time:30808us, server id:3306879, thread_id:17368'
````
It means that the network overhead of this transaction at the MGR layer took 30808 microseconds (30.808 milliseconds) at that time, and then check the network monitoring of that period and analyze the reasons for the large network delay.

The option `group_replication_request_time_threshold` is in milliseconds, the default value is 0, the minimum value is 0, and the maximum value is 100000. If the MGR runs in a local area network environment, it is recommended to set it to a range of 50 to 100 milliseconds. If it runs in a cross WANs network environment, it is recommended to set it to about 1 to 10 seconds. In addition, when the value is set between 1 and 9, it will be automatically adjusted to 10 (milliseconds) and no warning will be prompted. If it is set to 0, it will be disabled.

| System Variable Name | group_replication_request_time_threshold |
| --- | --- |
| Variable Scope | Global |
| Dynamic Variable | YES |
| Permitted Values ​​| [0 ~ 100000] |
| Default | 0 |
| Description | Unit: milliseconds. <br/>Set a threshold. When the MGR layer network overhead of a transaction exceeds the threshold, a record will be output in the error log. <br/>When set to 0, it means disabled. <br/>When it is suspected that the MGR communication may take too long to become the bottleneck of transaction performance, turn it on again. Usually, it is not recommended to turn it on. |

### 1.4 Custom Primary node election strategy
Improve the automatic Primary election strategy, the new election of Primary node based on the latest GTID set.

By default, MGR elects the primary according to the following rules:
1. When there are mixed deployment of nodes with different versions of MySQL 5.7 and MySQL 8.0, only the node running 5.7 will be elected as the master node. Also, when <= MySQL 8.0.16, the ordering is by major version number, that is, 5.7 comes before 8.0. In > MySQL 8.0.17 version, it is sorted by patch version number, that is, 8.0.17 comes before 8.0.25.
2. When the version numbers of all nodes are the same, they are sorted according to the node weight value (the option `group_replication_member_weight` defines the weight value, this option is not available in version 5.7, and it was added in 8.0), and the nodes with higher weight values ​​are ranked first.
3. Sort by node server_uuid.

In some cases, when all MGR nodes unexpectedly need to be restarted, the transaction application status of each node will not be checked, and a new Primary node will be incorrectly elected, which may result in the loss of some transaction data. Or when the original Primary node crashes and needs to elect a new Primary node, a node with a higher weight value but no latest transaction may also be elected, and there is also a risk of losing some transaction data.

In GreatSQL, the new option `group_replication_primary_election_mode` is used to customize the primary election strategy. The optional values ​​are as follows:
- WEIGHT_ONLY, choose the Primary automatically according to the traditional strategy, which is the default value.
- GTID_FIRST, firstly judges the transaction application status of each node, and automatically elects the node with the latest transaction as the new Primary node. **Recommended setting to this mode. **
- WEIGHT_FIRST, the traditional strategy is preferred, and if there is no suitable result, the transaction status of each node will be judged.

**Reminder**, all nodes must be set the same, otherwise MGR will not start.

| System Variable Name | group_replication_primary_election_mode |
| --- | --- |
| Variable Scope | Global |
| Dynamic Variable | NO |
| Permitted Values ​​| WEIGHT_ONLY<br/>GTID_FIRST<br/>WEIGHT_FIRST |
| Default | WEIGHT_ONLY |
| Description | What strategy is used when the MGR cluster needs to elect for the Primary node. |

## 2. Stability improvement
1. Optimized the problem that may cause severe performance jitter when nodes joinned.
2. Optimize the mechanism of Primary selection manually, and solve the problem that the Primary cannot be selected due to long life transactions.
3. Improve the foreign key constraint mechanism in MGR to reduce or avoid the risk of exiting MGR from the node reporting an error.

## 3. Other adjustments
1. The default value of the option `group_replication_flow_control_replay_lag_behind` has been adjusted from 60 seconds to 600 seconds to suit more business scenarios. This option is used to control the replication delay threshold of MGR primary-secondary nodes. When the delay of MGR primary-secondary nodes exceeds the threshold due to large transactions and other reasons, the flow control mechanism will be triggered.
2. Added option `group_replication_communication_flp_timeout` (unit: seconds). When the majority node exceeds this threshold and receives a message sent by a node, the node will be judged as a suspicious node. In environments with poor network conditions, this threshold can be appropriately adjusted to avoid frequent jitters.

## 4. Bug fix
01. Fixed the crash of InnoDB parallel query ([issue#I4J1IH](https://gitee.com/GreatSQL/GreatSQL/issues/I4J1IH)).
02. Fixed the problem that bind fails unexpectedly when dns or hostname is enabled.
03. Fixed the problem of unreasonable coroutine scheduling, which may cause the system to mistakenly judge as a network error during large transactions.
04. Fixed the problem that the connection was closed in advance due to the write timeout when the newly added node was chasing paxos data.
05. Fixed the abnormal data problem caused by the recovery node being stopped halfway.
06. Fixed the view problem caused by multiple exceptions at the same time.
07. Fixed the problem that adding nodes at the same time failed in some scenarios.
08. Fixed the problem of abnormal group view in special scenes.
09. Fixed the crash caused by member_stats related queries during the rejoin process.
10. Fixed an issue that might cause assert failure in before mode.
11. Fixed the problem that it may wait for a long time when stop group_replication.
12. Fixed the problem that importing the binlog generated in the traditional master-slave environment into MGR may cause an infinite loop.
13. Fixed the crash caused by large transaction memory allocation failure.

## 5. GreatSQL VS MySQL Community Edition

| Features | GreatSQL 8.0.25-16| MySQL 8.0.25 Community Server |
|---| --- | --- |
| Arbitration Node/Voting Node | ✅ | ❎ |
| Single primary fast mode | ✅ | ❎ |
| Geo tag | ✅ | ❎ |
| New flow control algorithm | ✅ | ❎ |
| InnoDB Parallel Query Optimization | ✅ | ❎ |
| Thread Pool | ✅ | ❎ |
|Audit | ✅ | ❎ |
| InnoDB transaction lock optimization | ✅ | ❎ |
|SEQUENCE_TABLE(N) function|✅ | ❎ |
|InnoDB table corruption exception handling|✅ | ❎ |
|Forced to use only InnoDB engine tables|✅ | ❎ |
|Kill idle transactions and avoid long lock waits|✅ | ❎ |
|Data Masking (data masking/coding)|✅ | ❎ |
|InnoDB fragmented page statistics enhancement|✅ | ❎ |
|Support MyRocks engine|✅ | ❎ |
| InnoDB I/O performance improvements | ⭐️⭐️⭐️⭐️⭐️ | ⭐️⭐️ |
| Network Partition Abnormal Response | ⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| Improve node exception exit handling | ⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| Consistent Read Performance | ⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| Improve MGR throughput |⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| Statistics Enhancements |⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| slow log enhancement | ⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| Big Transaction | ⭐️⭐️⭐️⭐️ | ⭐️ |
| Fix the risk of data loss in multi-write mode | ⭐️⭐️⭐️⭐️⭐️ | / |
| Fix the risk of losing data in single-master mode | ⭐️⭐️⭐️⭐️⭐️ | / |
| MGR cluster startup efficiency improved | ⭐️⭐️⭐️⭐️⭐️ | / |
| Cluster node disk full processing | ⭐️⭐️⭐️⭐️⭐️ | / |
| Fix TCP self-connect issue | ⭐️⭐️⭐️⭐️⭐️ | / |
| PROCESSLIST Enhancement | ⭐️⭐️⭐️⭐️⭐️ | / |

## 6. GreatSQL Release Notes
- [Changes in MySQL 8.0.25-15 (2022-8-26)](https://github.com/GreatSQL/GreatSQL-Doc/blob/main/relnotes/changes-greatsql-8-0-25-20210826.md)
