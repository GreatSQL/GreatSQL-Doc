# Changes in GreatSQL 5.7.36 (2022-4-7)

[toc]

## 1. New features
### 1.2 Added MGR role column
In MySQL 5.7, the table `performance_schema.replication_group_members` is no `MEMBER_ROLE` column, which is very inconvenient to quickly see which node is the primary node.

In GreatSQL, this column is added, it is more convenient to view node roles, and it is more friendly to some middleware support.
````
mysql> select * from performance_schema.replication_group_members;
+--------------------------+--------------------- -----------------+-------------+-------------+---- ------------+-------------+
| CHANNEL_NAME | MEMBER_ID | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE |
+--------------------------+--------------------- -----------------+-------------+-------------+---- ------------+-------------+
| group_replication_applier | 4c21e81e-953f-11ec-98da-d08e7908bcb1 | 127.0.0.1 | 3308 | ONLINE | SECONDARY |
| group_replication_applier | b5e398ac-8e33-11ec-a6cd-d08e7908bcb1 | 127.0.0.1 | 3306 | ONLINE | PRIMARY |
| group_replication_applier | b61e7075-8e33-11ec-a5e3-d08e7908bcb1 | 127.0.0.1 | 3307 | ONLINE | SECONDARY |
+--------------------------+--------------------- -----------------+-------------+-------------+---- ------------+-------------+
````

### 1.2 Adopt a new flow control mechanism
The native flow control algorithm not so good. When the flow control threshold is triggered, there will be a short flow control pause, and then the transaction will continue to be passed, which will cause 1-second performance jitter, and does not really play the role of continuous flow control.

In GreatSQL, the flow control algorithm is redesigned, the primary-secondary delay time is increased to calculate the flow control threshold, and the synchronization of large transaction processing and primary-secondary nodes is considered at the same time, the flow control granularity is more detailed, and there will be no some seconds small jitter problem.

The new option `group_replication_flow_control_replay_lag_behind` is used to control the replication delay threshold of MGR primary and secondary nodes. When the delay of MGR primary and secondary nodes exceeds the threshold due to large transactions and other reasons, the flow control mechanism will be triggered.

| System Variable Name | group_replication_flow_control_replay_lag_behind |
| --- | --- |
| Variable Scope | global |
| Dynamic Variable | YES |
| Permitted Values ​​| [0 ~ ULONG_MAX] |
| Default | 600 |
| Description | Used to control the replication delay threshold of MGR primary-secondary nodes. When the delay of MGR primary-secondary nodes exceeds the threshold due to large transactions and other reasons, the flow control mechanism will be triggered |

This option defaults to 600 seconds and can be dynamically modified online, for example:
```sql
mysql> SET GLOBAL group_replication_flow_control_replay_lag_behind = 600;
````
Under normal circumstances, this parameter does not need to be adjusted.


### 1.3 Added MGR network overhead threshold
Added new option `group_replication_request_time_threshold`.

In MGR, the overhead of a transaction includes network layer and local resource (such as CPU, disk I/O, etc.) overhead. When the transaction response is slow and you want to analyze the performance bottleneck, you can first determine whether it is caused by the overhead of the network layer or the local resource performance bottleneck. Events exceeding the threshold can be logged by setting the option `group_replication_request_time_threshold` for further analysis. The output is recorded in the error log, for example:
````
2022-03-04T09:45:34.602093+08:00 128 [Note] Plugin group_replication reported: 'MGR request time:30808us, server id:3306879, thread_id:17368'
````
It means that the network overhead of this transaction at the MGR layer took 30808 microseconds (30.808 milliseconds) at that time, and then check the network monitoring of that period and analyze the reasons for the large network delay.

The option `group_replication_request_time_threshold` is in microseconds, the default value is 0, the minimum value is 0, and the maximum value is 100000000. If the MGR runs in a local area network environment, it is recommended to set it to a range of 50 to 100 milliseconds. If it runs in a cross WANs network environment, it is recommended to set it to about 1 to 10 seconds. In addition, when the value is set between 1 and 9, it will be automatically adjusted to 10 (milliseconds) and no warning will be prompted. If it is set to 0, it will be disabled.

| System Variable Name | group_replication_request_time_threshold |
| --- | --- |
| Variable Scope | Global |
| Dynamic Variable | YES |
| Permitted Values ​​| [0 ~ 100000000] |
| Default | 0 |
| Description | Unit: microseconds. <br/>Set a threshold. When the MGR layer network overhead of a transaction exceeds the threshold, a record will be output in the error log. <br/>When set to 0, it means disabled. <br/>When it is suspected that the MGR communication may take too long to become the bottleneck of transaction performance, turn it on again. Usually, it is not recommended to turn it on. |


### 1.4 Adjust MGR large transaction limit
Adjust the MGR transaction limit option `group_replication_transaction_size_limit`, which defaults to 150000000 (also the maximum value).

In MySQL 5.7, MGR transactions are not fragmented, and executing large transactions can easily cause timeout (and repeatedly resend transaction data), eventually causing nodes to report errors and exit the cluster.

In GreatSQL 5.7, this problem is optimized and a transaction upper limit is set. If the transaction exceeds the upper limit, the transaction will fail and roll back, but the node will not exit the cluster.

**Note**, this is a **hard limit**, even if it is set to 0, it will automatically adjust to 150000000.
````
mysql> set global group_replication_transaction_size_limit = 150000001;
Query OK, 0 rows affected, 1 warning (0.00 sec)

-- The prompt has been reset
mysql> show warnings;
+---------+------+-------------------------------- -----------------------------------------+
| Level | Code | Message |
+---------+------+-------------------------------- -----------------------------------------+
| Warning | 1292 | Truncated incorrect group_replication_transaction_si value: '150000001' |
+---------+------+-------------------------------- -----------------------------------------+
1 row in set (0.00 sec)

mysql> set global group_replication_transaction_size_limit=0;
Query OK, 0 rows affected (0.00 sec)

-- Although there is no error or warning, it has also been reset
mysql> select @@global.group_replication_transaction_size_limit;
+------------------------------------------------- --+
| @@global.group_replication_transaction_size_limit |
+------------------------------------------------- --+
| 150000000 |
+------------------------------------------------- --+
````

When executing an oversized large transaction, the following error is reported:
````
ERROR 3100 (HY000): Error on observer while running replication hook 'before_commit'.
````

Taking the table generated by the test tool sysbench as an example, the upper limit of data rows that can be executed in batches for a transaction is about 732,000 records:
````
mysql> insert into t1 select * from sbtest1 limit 732000;
Query OK, 732000 rows affected (16.07 sec)
Records: 732000 Duplicates: 0 Warnings: 0

mysql> insert into t1 select * from sbtest1limit 733000;
ERROR 3100 (HY000): Error on observer while running replication hook 'before_commit'.
````

If the large transaction can be successfully executed, a log similar to the following is also recorded, telling the number of bytes of the transaction:
````
[Note] Plugin group_replication reported: 'large transaction size:149856412'
````

| System Variable Name | group_replication_transaction_size_limit |
| --- | --- |
| Variable Scope | Global |
| Dynamic Variable | YES |
| Permitted Values ​​| [0 ~ 150000000] |
| Default | 150000000 |
| Description | Set the large transaction threshold, when an MGR transaction exceeds the threshold, a record will be output in the error log|

## 2. Stability improvement
1. Fixed severe performance jitter in abnormal situations (node ​​crash, node shutdown, network partition).
2. Improve the long-term blocking problem caused by several large transactions.

## 3. Performance improvement
1. Redesign the transaction certification queue cleaning algorithm. In the MySQL community version, an algorithm similar to a full table scan is used to clean up the transaction certification queue, which results in low cleanup efficiency and large performance jitter. In the GreatSQL version, a similar indexing mechanism is added to the transaction certification queue, and the time of each cleaning is controlled, which can effectively solve the problems of low cleaning efficiency and large performance jitter.
2. Improved the playback speed of large transaction concurrent applications on the Secondary node.
3. Added xcom cache entries to improve performance in scenarios with high network latency or slow transaction applications.

## 4. Bug fix
01. Fixed the problem that bind fails unexpectedly when dns or hostname is enabled.
02. Fixed the problem of unreasonable coroutine scheduling, which may cause the system to incorrectly judge as a network error during large transactions.
03. Fixed the problem that the connection was closed in advance due to the write timeout when the newly added node was chasing paxos data.
04. Fixed the abnormal data problem caused by the recovery node being stopped halfway.
05. Fixed the problem that data may be lost in some cases in the multi-primary multi-write mode.
06. Fixed that in some special scenarios, multiple nodes were started at the same time and kept in the state of recovery
07. Fixed the weird problem of applier thread in special scenarios.
08. Fixed an infinite loop problem caused by failure to create a thread under high concurrency.
09. Fixed an issue where the entire cluster was dragged down due to the hang of a secondary node.
10. Fixed the weird problem caused by tcp self connect when deploying multiple nodes on a single machine.
11. Fixed the view problem caused by multiple exceptions at the same time.
12. Fixed the view problem caused by the simultaneous restart of 5 or more nodes (a node will always be in the recovering state).
13. Fixed the problem that adding nodes at the same time failed in some scenarios.
14. Fixed the problem of abnormal group view in special scenes.
