
### 0. 前言
> GreatSQL运行更平稳，不会有大的抖动。
> MySQL官方版本的MGR更适合在中小规模业务环境下运行。

### 1. GreatSQL的优势

GreatSQL的优势在于提升了MGR的性能及可靠性，及修复了众多bug。主要有以下几点：
- 提升大事务并发性能及稳定性
- 优化MGR队列garbage collect机制、改进流控算法，以及减少每次发送数据量，避免性能抖动
- 解决了AFTER模式下，存在节点加入集群时容易出错的问题
- 在AFTER模式下，强一致性采用多数派原则，以适应网络分区的场景
- 当MGR节点崩溃时，能更快发现节点异常状态，有效减少切主和异常节点的等待时间
- 修复了可能导致数据丢失、性能抖动等多个缺陷/bug问题

### 2. GreatSQL MGR优化建议

为了能更好的发挥出GreatSQL运行MGR的优势，有几个优化建议
#### 2.1 关闭流控
GreatSQL MGR相较于官方版本，在从库回放速度控制方面做得更优雅、更完善。
因此，建议直接在事务并发量不是太高的场景下，关闭流控模式，让GreatSQL发挥出更大性能优势。
```
# QUOTA => 开启流控（默认）
# DISABLED => 关闭流控
group_replication_flow_control_mode = "DISABLED"
```
通常来说，不建议开启流控。当然了，如果实际生产环境中，已经快达到了服务器的硬件性能极限，这种情况下，还是要开启流控的，只不过可以把默认的流控阈值调高一些，比如设置为原来的10倍或更高。
此外，在正式上线前的压测环境下，也最好关闭流控，通过压测得到事务性能指标和服务器性能的一个平衡点。
这就类似另一个参数 ```innodb_thread_concurrency```，通常也不建议设置为非0，以避免在高并发场景下，InnoDB线程总是要等待排队，反倒影响并发性能。

#### 2.1 修改从库回放并发度
为了提高MGR从库的回放效率，降低从库延迟，需要提高从库回放线程数。
```
slave_parallel_type = LOGICAL_CLOCK
slave_parallel_workers = 128 #回放线程数可以设置为逻辑CPU的4倍甚至更高
```

剩下的就是正常的MySQL优化套路了，下面是几个关键参数列表，建议根据硬件配置级别适当调整：
```
innodb_buffer_pool_size = 128G
innodb_buffer_pool_instances = 8
innodb_log_file_size = 2G
innodb_log_files_in_group = 3
innodb_io_capacity = 20000
innodb_io_capacity_max = 40000
innodb_flush_sync = OFF
```

此外，也强烈建议采用 **jemalloc** 代替系统自带的内存分配机制。

最后放一张在大流量、高负载的业务场景下的压测对比图，充分体现了GreatSQL的优势（由不愿透露姓名的社区朋友提供）
![enter image description here](https://images.gitee.com/uploads/images/2021/0412/111846_5aeddef0_8779455.png "6.GreatSQL-vs-MySQL-MGR-benchmark.png")

我们再次诚邀更多的朋友们一起使用GreatSQL，更放心的用上MGR，提高数据库服务可用时间，保证业务可靠性。

### 3. 关于GreatSQL
GreatSQL是源于Percona server的分支版本，除了Percona Server已有的稳定可靠、高效、管理更方便等优势外，特别是进一步提升了MGR（MySQL Group Replication）的性能及可靠性，以及众多bug修复。

GreatSQL可以作为MySQL或Percona server的可选替代方案，用于线上生产环境。

- gitee官网：[https://gitee.com/GreatSQL/GreatSQL](https://gitee.com/GreatSQL/GreatSQL)
- 最新版本 GreatSQL-8.0.22-v20210410：[https://gitee.com/GreatSQL/GreatSQL/releases/v20210410](https://gitee.com/GreatSQL/GreatSQL/releases/v20210410)
