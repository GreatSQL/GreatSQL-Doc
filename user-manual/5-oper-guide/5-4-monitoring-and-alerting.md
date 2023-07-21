# 监控告警
---

本文档描述对GreatSQL数据库进行监控有哪几个主要关注点。

除去常规的服务的可用性、性能监控外，对GreatSQL数据库的监控建议关注以下几方面：

1. SQL平均响应耗时
2. 锁、等待事件
3. 大事务
4. MGR监控

下面我们针对这几个不同监控维度进行详细介绍。

## 1. SQL平均响应耗时

除了TPS、QPS外，SQL平均响应耗时也是衡量数据库性能的重要指标之一。

TPS、QPS好比高速公路收费站闸机每分钟能通过多少辆车，而SQL平均响应耗时则是每辆车通过闸机的平均耗时。

前者考验收费站单位时间内的处理能力，后者是作为用户体验的衡量维度。

前者通过增设闸机数量（提高并发度），即可提高处理能力；而后者则需要通过优化闸机处理机制（优化数据库 & 每条SQL），才能提高响应效率。

在GreatSQL中，可以利用 `benchmark()` 函数来衡量SQL平均响应耗时：
```
mysql> \help benchmark
Name: 'BENCHMARK'
Description:
Syntax:
BENCHMARK(count,expr)
...
Examples:
mysql> SELECT BENCHMARK(1000000,AES_ENCRYPT('hello','goodbye'));
+---------------------------------------------------+
| BENCHMARK(1000000,AES_ENCRYPT('hello','goodbye')) |
+---------------------------------------------------+
|                                                 0 |
+---------------------------------------------------+
1 row in set (4.74 sec)
```
即调用 `benchmark()` 函数进行固定次数的计算，根据其耗时，作为SQL平均响应耗时的衡量指标。

并且可以在业务空闲时段取得该值作为基准数据，再根据业务高峰时期的耗时作为对比，即可知道业务高峰期SQL平均响应耗时增加了多少，效率降低了多少。

例如：
```
time mysql -q -N -s -e "SELECT BENCHMARK(100000,AES_ENCRYPT('hello','goodbye'))"
0

real    0m0.024s
user    0m0.001s
sys     0m0.004s
```

这就可以得到耗时是 0.024s，即可认为当前SQL平均响应耗时是及24ms，通过监控系统在不同时段获取该值，即可知道这个指标的变化波动幅度了。

## 2. 锁、等待事件

### 2.1 当前行锁数量
```
mysql> select * from performance_schema.global_status where variable_name = 'Innodb_row_lock_current_waits';
+-------------------------------+----------------+
| VARIABLE_NAME                 | VARIABLE_VALUE |
+-------------------------------+----------------+
| Innodb_row_lock_current_waits | 0              |
+-------------------------------+----------------+
```
当该值大于0的时候，就要立即发出告警，表示当前存在行锁等待事件，要检查是否有事务持有行锁未释放。

### 2.2 IBP wait free
```
mysql> select * from performance_schema.global_status where variable_name = 'Innodb_buffer_pool_wait_free';
+-------------------------------+----------------+
| VARIABLE_NAME                 | VARIABLE_VALUE |
+-------------------------------+----------------+
| Innodb_buffer_pool_wait_free  | 0              |
+-------------------------------+----------------+
```
当该值大于0的时候，就要立即发出告警，表示InnoDB Buffer Pool严重不够用，如果物理内存足够，则适当加大，或者迁移到更高内存的服务器上。

### 2.3 InnoDB log wait
```
mysql> select * from performance_schema.global_status where variable_name = 'Innodb_log_waits';
+------------------+----------------+
| VARIABLE_NAME    | VARIABLE_VALUE |
+------------------+----------------+
| Innodb_log_waits | 0              |
+------------------+----------------+
```
当该值大于0的时候，就要立即发出告警，表示InnoDB Log Buffer严重不够用，如果物理内存足够，则适当加大，或者迁移到更高内存的服务器上。

### 2.4 InnoDB Purge Lag
```
mysql> SELECT `COUNT`,`COMMENT` FROM INFORMATION_SCHEMA.INNODB_METRICS WHERE NAME = 'trx_rseg_history_len';
+-------+-------------------------------------+
| COUNT | COMMENT                             |
+-------+-------------------------------------+
|    14 | Length of the TRX_RSEG_HISTORY list |
+-------+-------------------------------------+

mysql> pager cat - | grep -i 'History list length'
PAGER set to 'cat - | grep -i 'History list length''

# 或者换一种方式查看
mysql> show engine innodb status\G
History list length 4
```
当该值超过2000后，就要立即发出告警，表示当前等待被purge的队列较大，需要检查是否物理I/O存在瓶颈，或者有个大事务提交了。

## 3. 大事务

在生产环境中，可能因为种种原因产生大事务，或者运行很长时间的事务。

这些事务中可能对数据库执行大量修改操作，需要持有行锁、MDL锁等资源，如果事务长时间不提交/回滚，则可能对其他业务请求造成严重影响，这些请求可能会被长时间阻塞。

因此，需要关注运行中的大事务、长事务，一旦发现超过阈值，就应当发出告警。
```
# 找到活跃时间最长的事务
mysql> SELECT * FROM information_schema.innodb_trx ORDER BY trx_started ASC LIMIT 1;

# 找到等待时间最长的事务
mysql> SELECT * FROM sys.innodb_lock_waits ORDER BY wait_age_secs DESC LIMIT 1;

# 找到特别需要关注的事务
mysql> SELECT * FROM information_schema.innodb_trx WEHRE
  trx_lock_structs >= 5 OR    -- 持有超过5把锁
  trx_rows_locked >= 100 OR   -- 超过100行被锁
  trx_rows_modified >= 100 OR -- 超过100行被修改
  TIME_TO_SEC(TIMEDIFF(NOW(),trx_started)) > 100;    -- 事务活跃超过100秒
```
以上阈值可根据实际情况进行调整，需要对生产环境中的活跃大事务保持关注，避免造成连锁影响。

## 4. MGR监控

对MGR除了监控其服务状态外，更重要的是监控各节点间的事务延迟情况，以此判断各节点的事务处理能力，以及评估是否需要提升服务器配置等级。
```
mysql> SELECT MEMBER_ID AS id, COUNT_TRANSACTIONS_IN_QUEUE AS trx_tobe_certified,
  COUNT_TRANSACTIONS_REMOTE_IN_APPLIER_QUEUE AS relaylog_tobe_applied,
  COUNT_TRANSACTIONS_CHECKED AS trx_chkd,
  COUNT_TRANSACTIONS_REMOTE_APPLIED AS trx_done,
  COUNT_TRANSACTIONS_LOCAL_PROPOSED AS proposed
  FROM performance_schema.replication_group_member_stats;
+--------------------------------------+-------------------+---------------------+----------+----------+----------+
| id                                   |trx_tobe_certified |relaylog_tobe_applied| trx_chkd | trx_done | proposed |
+--------------------------------------+-------------------+---------------------+----------+----------+----------+
| 4ebd3504-11d9-11ec-8f92-70b5e873a570 |                 0 |                   0 |   422248 |        6 |   422248 |
| 549b92bf-11d9-11ec-88e1-70b5e873a570 |                 0 |              238391 |   422079 |   183692 |        0 |
| 5596116c-11d9-11ec-8624-70b5e873a570 |              2936 |              238519 |   422115 |   183598 |        0 |
| ed5fe7ba-37c2-11ec-8e12-70b5e873a570 |              2976 |              238123 |   422167 |   184044 |        0 |
+--------------------------------------+-------------------+---------------------+----------+----------+----------+
```
其中，`relaylog_tobe_applied` 的值表示远程事务写到relay log后，等待回放的事务队列，`trx_tobe_certified` 表示等待被认证的事务队列大小，这二者任何一个值大于0，都表示当前有一定程度的延迟，应当发出告警。

还可以通过关注上述两个数值的变化，看看两个队列是在逐步加大还是缩小，据此判断Primary节点是否"跑得太快"了，或者Secondary节点是否"跑得太慢"。

如果某个节点上的 `relaylog_tobe_applied` 值特别大，则要引起关注，检查该节点上的业务压力是否过大，或者服务器配置是否有问题。

关于MGR监控，更多详情参考文档：[MGR状态监控](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-06.md)。

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
