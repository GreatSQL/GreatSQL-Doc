# GreatSQL优化
---

本文档主要介绍从GreatSQL数据库层的几个优化参考。

通常情况下，运行GreatSQL数据库时，采用 [**这份my.cnf**](/docs/my.cnf-example-greatsql-8.0.25-16) 参考就足够了。

下面针对其中的几个关键参数选项稍作解读：

- no-auto-rehash
mysql客户端登入时，不读取全部metadata，避免影响性能以及产生MDL等待。

- skip_name_resolve = 1
不进行DNS反解析，提高用户端连接性能。

- default_time_zone = "+8:00"
显示指定时区，避免频繁调用时区转换函数，提升性能。请务必根据实际情况调整本参数。

- lock_wait_timeout = 3600
限制表级锁、MDL锁、备份锁等最大等待时长。

- log_error_verbosity = 3
设置为3可以记录更多日志信息，便于问题分析排查。

- slave_parallel_type = LOGICAL_CLOCK
- slave_parallel_workers = 64
采用LOGICAL_CLOCK模式，并行复制线程数最高可以设置为逻辑CPU数量的2倍，提高SQL线程应用事务的并行效率。

- binlog_transaction_dependency_tracking = WRITESET
采用WRITESET模式提高从节点事务并行回放度。

- slave_preserve_commit_order = 1
从节点回放事务时，要保证事务顺序，避免和主节点数据不一致。

- loose-force_parallel_execute = OFF
启用InnoDB并行查询优化功能。

- loose-parallel_default_dop = 8
设置每个SQL语句的并行查询最大并发度。

- loose-parallel_max_threads = 64
设置系统中总的并行查询线程数，可以和最大逻辑CPU数量一样。

- loose-parallel_memory_limit = 12G
并行执行时leader线程和worker线程使用的总内存大小上限，可以设置物理内存的5-10%左右

- loose-group_replication_flow_control_mode = "DISABLED"
关闭MySQL原生的MGR流控模式，因为其作用不大。

- loose-group_replication_majority_after_mode = ON
在AFTER模式下，当发生个别节点异常时，只要多数派达成一致即可，不会导致整个MGR都被hang住。

- loose-group_replication_communication_max_message_size = 10M
设置MGR通信消息分片，避免一次性发送消息太大，导致网络拥塞，影响MGR性能。

- loose-group_replication_single_primary_fast_mode = 1
启用快速单主模式。

- loose-group_replication_request_time_threshold = 100
记录因MGR通信超过阈值的事件，便于后续检查确认MGR通信性能是否存在瓶颈。

- loose-group_replication_primary_election_mode = GTID_FIRST
设置MGR选主模式为GTID_FIRST，在发生主节点切换时，会优先选择事务应用效率最高的那个节点。

- innodb_io_capacity = 4000
- innodb_io_capacity_max = 8000
配置高端PCIe SSD卡的话，则可以调整的更高，比如 50000 - 80000

- innodb_thread_concurrency = 0 
不限制InnoDB并行线程数，使其发挥最大性能。但如果业务端发起的业务请求并行度总是超过服务器逻辑CPU数，则可能导致CPU调度频繁等待，此时可以考虑将本选项设置为逻辑CPU的数量。

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
