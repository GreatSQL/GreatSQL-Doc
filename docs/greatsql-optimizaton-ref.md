### 0. Preface
> GreatSQL runs more smoothly and there will be no big jitter.
> MySQL MGR is more suitable for operation in small and medium-scale business environments.

### 1. Advantages of GreatSQL

The advantage of GreatSQL is that it improves the performance and reliability of MGR, and fixes many bugs. The main points are as follows:
- Improve the concurrent performance and stability of large transactions in MGR.
- Improve MGR's GC and flow control algorithms, and reduce the amount of data sent each time to avoid performance jitter.
- In the AFTER mode of the MGR, the problem that the node is prone to errors when joining the cluster is fixed.
- In the AFTER mode of the MGR, the principle of majority consistency is adopted to adapt to the network partition scene.
- When the MGR node crashes, the abnormal state of the node can be found faster, effectively reducing the waiting time for the switchover and abnormal state.
- Optimize the InnoDB transaction lock mechanism to effectively improve transaction concurrency performance by at least 10% in high concurrency scenarios.
- Realize the InnoDB parallel query mechanism, which greatly improves the efficiency of aggregate query. In the TPC-H test, it can be increased by more than 40 times, and the average increase is 15 times. Especially suitable for SAP, financial statistics and other businesses such as periodic data summary reports.
- Fixed multiple defects or bugs that may cause data loss, performance jitter, and extremely slow node join recovery in MGR.

### 2. GreatSQL MGR optimization suggestions

In order to make better use of the advantages of GreatSQL running MGR, there are several optimization suggestions

#### 2.1 Turn off flow control
Compared with MySQL, GreatSQL MGR is more elegant and perfect in controlling the playback speed in secondary node.

Therefore, it is recommended to disable the flow control mode directly in the scenario where the transaction concurrency is not too high, so that GreatSQL can play a greater performance advantage.
```
# QUOTA => Turn on flow control (default)
# DISABLED => Turn off flow control
group_replication_flow_control_mode = "DISABLED"
```
Generally, it is not recommended to enable flow control. Of course, if the online production environment has almost reached the hardware performance limit of the server, in this case, it is still necessary to turn on flow control, but the default flow control threshold can be adjusted higher, for example, set to the original 10 Times or higher.

In addition, in the benchmark environment, it is also best to disable flow control, and obtain a balance point between transaction performance indicators and server performance through benchmark.

This is similar to another parameter ```innodb_thread_concurrency```. It is generally not recommended to set it to non-zero to avoid InnoDB threads always waiting to be queued in high concurrency scenarios, which will affect concurrency performance.

#### 2.1 Modify the concurrency of playback in secondary node
In order to improve the playback efficiency of the MGR secondary node and reduce the delay, it is necessary to increase the number of playback threads.
```
slave_parallel_type = LOGICAL_CLOCK
slave_parallel_workers = 128 #The number of playback threads can be set to 4 times or higher than the logical CPU
```

The rest is the normal MySQL optimization rules. The following is a list of several key variables. It is recommended to adjust appropriately according to the hardware configuration level:
```
innodb_buffer_pool_size = 128G
innodb_buffer_pool_instances = 8
innodb_log_file_size = 2G
innodb_log_files_in_group = 3
innodb_io_capacity = 20000
innodb_io_capacity_max = 40000
innodb_flush_sync = OFF
```

In addition, it is strongly recommended to use **jemalloc** instead of the system's own memory allocation mechanism.

Finally, I put a benchmark comparison chart in a high-traffic, high-load business scenario, which fully reflects the advantages of GreatSQL 

![enter image description here](https://images.gitee.com/uploads/images/2021/0412/111846_5aeddef0_8779455.png "6.GreatSQL-vs-MySQL-MGR-benchmark.png")

We once again sincerely invite more friends to use GreatSQL together, and use MGR with more confidence, improve the available time of database services, and ensure business reliability.

### 3. About GreatSQL
GreatSQL is a branch of Percona Server.

GreatSQL focuses on improving the performance and reliability of MGR (MySQL Group Replication), and fixing some bugs. In addition, GreatSQL also merged two Patches contributed by the Huawei Kunpeng Compute Community, respectively for OLTP and OLAP business scenarios, especially the InnoDB parallel query feature. In the TPC-H test, the performance of aggregate analytical SQL was improved by an average of 15 times, the highest increased by more than 40 times, especially suitable for SAP, financial statistics and other businesses such as periodic data summary reports.

GreatSQL can be used as an alternative to MySQL or Percona Server.

GreatSQL is completely free and compatible with MySQL or Percona Server.

- github: [https://github.com/GreatSQL/GreatSQL](https://github.com/GreatSQL/GreatSQL)
- The latest version GreatSQL-8.0.25-15: [https://github.com/GreatSQL/GreatSQL/releases](https://github.com/GreatSQL/GreatSQL/releases)
