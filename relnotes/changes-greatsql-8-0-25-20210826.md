# Changes in GreatSQL 8.0.25 (2021-8-26)
---
[toc]

## 1. New features
### 1.1 Node Geotag

Geographic tags can be set for each node. When MGR is deployed in multiple IDCs, it is ensured that each zone has a copy of data.

A new dynamic configuration option `group_replication_zone_id`, which is used to mark the node's geographic label. When the value of this option is set to different for each node in MGR, it is deemed to have set different geographic tags.

The nodes in the same IDC can be set to the same value, and the nodes in another IDC can be set to a different value, so that at least one node in each group of `group_replication_zone_id` will be required to confirm when the transaction is committed, before proceeding to the next transaction. This can ensure that there is always the latest transaction in a certain node in each IDC.

| System Variable Name | group_replication_zone_id |
| --- | --- |
| Variable Scope | global |
| Dynamic Variable | YES |
| Permitted Values ​​| [0 ~ 8] |
| Default | 0 |
| Description | Set different geographic tags for each node of MGR, When MGR is deployed in multiple IDCs, it is ensured that each zone has a copy of data.<br/>After modifying the value of this option, restart the MGR thread to take effect. |

### 1.2 A new flow control mechanism
The native flow control algorithm is bit rough. After triggering the flow control threshold, there will be a short flow control pause action, and then the transaction will continue to be processed, which will cause 1 second of performance jitter, and does not really play the role of continuous flow control.

In GreatSQL, the flow control algorithm is redesigned, the primary-secondary delay time is adopted to calculate the flow control threshold, and the large transaction processing and the synchronization of the primary-secondary node are considered at the same time, the flow control granularity is more detailed, and there will be no performance jitter in seconds.

A new dynamic configuration option `group_replication_flow_control_replay_lag_behind` is used to control the replication delay threshold of the MGR primary and secondary nodes. When the delay of the MGR primary and secondary nodes exceeds the threshold due to large transactions, the flow control mechanism will be triggered.

| System Variable Name | group_replication_flow_control_replay_lag_behind |
| --- | --- |
| Variable Scope | global |
| Dynamic Variable | YES |
| Permitted Values ​​| [0 ~ ULONG_MAX] |
| Default | 60 |
| Description | Used to control the replication delay threshold of the MGR primary and secondary nodes. When the delay of the MGR primary and secondary nodes exceeds the threshold due to large transactions, the flow control mechanism will be triggered |

This option default value is 60 seconds and can be dynamically modified, for example:
```sql
mysql> SET GLOBAL group_replication_flow_control_replay_lag_behind = 60;
```
Normally, this option does not need to be changed.

## 2. Stability improvement
### 2.1 Improve the majority writing mechanism in AFTER mode
In the event of a network partition failure, the availability of the MGR cluster can still be guaranteed.

In the event of a network partition failure, as long as the majority node has been replayed, the MGR cluster can continue to process new transactions.

### 2.2 Avoid the problem of blocking the MGR cluster when the disk space is full
In MySQL, once a node's disk space is full, it will cause the entire MGR cluster to be blocked. In this case, the greater the number of nodes, the worse the availability.

In GreatSQL, once the disk space of a node is found to be full, the node will be allowed to exit the MGR cluster actively, which can avoid the problem of the entire MGR cluster being blocked.

### 2.3 Avoid the problem of data loss in multi-primary mode or when switching primary node
In MySQL, transaction certification data is processed in advance.

In GreatSQL, the transaction certification processing flow has been adjusted to put it in the **applier queue** to be processed in paxos order, which avoid the problem of data loss in multi-primary mode or when switching primary node.

### 2.4 Avoid the problem of performance jitter when the node exits the cluster abnormally
In MySQL, the paxos communication mechanism is a bit rough. When a node exits abnormally, it will cause performance jitter for a long time (about 20 to 30 seconds). In the worst case, TPS may drop to 0 for several seconds.

In GreatSQL, it will only produce a small performance jitter of about 1 to 3 seconds. In the worst case, TPS may only lose about 20% to 30%.

### 2.5 Improved node abnormal state determine
When an abnormal node crash or network partition occurs, GreatSQL can find these abnormal conditions faster. MySQL it takes 5 seconds to find out, while GreatSQL only takes about 1 second, which can effectively reduce the waiting time for switchover and abnormal nodes.

### 2.6 Optimize the log output format
Add more DEBUG information to help troubleshoot problems encountered when MGR is running.

## 3. Performance improvement
### 3.1 Redesign the transaction certification queue cleaning algorithm
In MySQL, an algorithm similar to a full table scan is used to clean up the transaction certification queue, which has low cleaning efficiency and large performance jitter.

In GreatSQL, a similar indexing mechanism is added to the transaction certification queue, and the time of each cleaning is controlled, which can effectively solve the problems of low cleaning efficiency and large performance jitter.

### 3.2 Improve MGR throughput
In high-latency scenarios, the throughput of applications accessing MGR is improved, and the impact of network latency on access performance is minimized.

### 3.3 Improve consistent read performance
Improve consistent read performance, greatly reducing read-only latency from the secondary node.

## 4. Merge two patches contributed by Huawei Kunpeng Compute Community
### 4.1 InnoDB transaction object mapping data structure optimization
In MySQL, a Red black tree structure is used to realize the rapid mapping relationship between transaction IDs and transaction objects. However, in the high-concurrency application scenario of this data structure, a large number of lock competitions will cause the bottleneck of transaction processing.

The use of a new lock-free hash structure in GreatSQL significantly reduces the critical area consumption of locks and improves transaction processing capabilities by at least 10%.
![Enter picture description](https://images.gitee.com/uploads/images/2021/0819/094257_f46e3522_8779455.jpeg "16291669854553.jpg")

### 4.2 InnoDB parallel query optimization
According to the characteristics of the B+ tree, the B+ tree can be divided into several subtrees. At this time, multiple threads can scan different parts of the same InnoDB table in parallel. Multi-threaded transformation of the execution plan. The execution plan of each sub-thread is consistent with the original execution plan of MySQL, but each sub-thread only needs to scan part of the data in the table, and the results are summarized after the sub-thread scan is completed. Through multi-threaded transformation, multi-core resources can be fully utilized and query performance can be improved.

After optimization, it performs well in the TPC-H test, with a maximum increase of 30 times and an average increase of 15 times. This feature is suitable for SAP, financial statistics and other businesses such as periodic data summary reports.

Use restrictions:
- Subqueries are not supported temporarily, and need to be transformed into JOIN first.
- At present, only ARM is supported, and X86 optimization will be completed as soon as possible.
![Enter picture description](https://images.gitee.com/uploads/images/2021/0819/094317_1c0fb43a_8779455.jpeg "16292668686865.jpg")

## 5. Bugs fix
- Fixed multiple bugs in AFTER mode, and improved the reliability of writing AFTER mode with consistency. For example, when a new node joins, problems such as improper message processing and thread synchronization can easily lead to a series of abnormal exits from the cluster.
- Fixed the problem of view update caused by the abnormal exit of the majority node from the cluster of different types. When the node crashes and the node exits at the same time, it may cause the MGR view to be inconsistent with the actual situation, resulting in a series of non-abnormal problems.
- Fixed the TCP self-connect problem of multi-node MGR deployment in a single-machine environment. Related [BUG#98151](https://bugs.mysql.com/bug.php?id=98151).
- Fixed the problem of long waiting during the recovery process. Starting multiple nodes at the same time may result in stuck in the recovering state for a long time (may even exceed several hours). Fixed several unreasonable sleep practices to solve this problem.
- Fixed an infinite loop of logic that might be caused by transferring big data.
- Fix some coredump issues
    - a) When executing the concurrent operations of `start group_replication` and querying `replication_group_member_stats`, it may cause the start of `start group_replication` to fail, or even node coredump.
    - b) The start process of executing `start group_replication` may fail. In the process of destroying internal objects, if you query the status of `replication_group_member_stats` at the same time, it may cause coredump.

## 6. Notes
- When any node in the MGR cluster is in the recovering state and there is still business traffic, **do not** execute `stop group_replicationt` to stop the MGR server, otherwise it may cause GTID disorder or even data loss.
- The option `slave_parallel_workers` is recommended to be set to 2 times the number of logical CPUs to improve the concurrency efficiency during playback from the secondary node.
- After setting the `group_replication_flow_control_replay_lag_behind` parameter, the flow control parameters in the MySQL MGR no longer work, GreatSQL will automatically perform flow control according to the queue length and size.
- Before the MGR node is started, be sure to set `super_read_only=ON` (or make sure that no one will modify the data at this time).
- The option `group_replication_unreachable_majority_timeout` is recommended not to be changed, otherwise an error will be returned to the user when the network is partitioned, but the majority of other partitions have already submitted the transaction.
- For problem diagnosis, it is recommended to set `log_error_verbosity=3`.
- When the InnoDB parallel query optimization feature (force_parallel_execute = ON) is enabled, it is recommended to increase the parallel_default_dop option value at the same time to improve the parallelism of a single SQL query.
- When the InnoDB parallel query optimization feature is enabled, it is recommended to increase the parallel_max_threads option value at the same time to improve the query parallelism of the entire instance.
- When the InnoDB parallel query optimization feature is enabled, if a temporary table needs to be generated during SQL runtime, a `table...full` error may be reported. This is MySQL [BUG#99100](https://bugs.mysql. com/bug.php?id=99100), which can be solved by increasing the option value of `temptable_max_ram`.
