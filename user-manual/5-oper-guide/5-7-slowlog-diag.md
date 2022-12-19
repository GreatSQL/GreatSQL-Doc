# 慢查询SQL诊断
---

本文档介绍如何定位数据库运行时那些性能较差的SQL（即通常所说的慢查询SQL），并分析慢查询SQL，以及对这些SQL进行优化。

## 1. 慢查询SQL相关设置

在默认设置模式下，是不会记录慢查询SQL的，需要自行配置，可以参考以下设置模板：
```
slow_query_log = 1
slow_query_log_file = slow.log
log_slow_extra = 1
log_slow_verbosity = FULL
long_query_time = 0.01
log_queries_not_using_indexes = 1
log_throttle_queries_not_using_indexes = 60
min_examined_row_limit = 100
log_slow_admin_statements = 1
log_slow_slave_statements = 1
```

各个选项分别简介如下：

| 选项 | 简介 |
| --- | --- |
| slow_query_log | 总开关，是否启用slow query log。|
| slow_query_log_file | 设置slow query log的文件名。|
| log_slow_extra | MySQL 8.0.14起新增选项，支持在slow query log中记录更多信息，例如线程ID、读写字节数、是否有临时表、是否有排序等。只有当`log_output=FILE`时才有效，如果是设置为`TABLE`则无效。|
| log_slow_verbosity | Percona/GreatSQL数据库特有选项，和 `log_slow_extra` 类似，可以设置为FULL，记录更详细的信息，便于分析慢查询SQL的性能瓶颈。|
| log_slow_admin_statements | 是否记录ALTER TABLE/ANALYZE TABLE等DDL管理指令的慢查询。
| log_slow_slave_statements | 是否记录主从复制中，从节点上SQL线程应用SQL时产生的慢查询。只有当 `binlog_format=STATEMENT` 才生效，设置为ROW/MIXED时都不生效。|
| long_query_time | SQL运行耗时超过该阈值时，就会被判定为慢查询。单位是：秒。|
| log_queries_not_using_indexes | 当执行的SQL没有可用索引时，也被判定为慢查询。|
| log_throttle_queries_not_using_indexes | 当选项 `log_queries_not_using_indexes=ON`时，每分钟记录的慢查询可能会很多，本选项用于设置每分钟最多记录几次这样的慢查询。|
| min_examined_row_limit | 符合条件的慢查询SQL，当扫描行数低于本选项阈值时，不再被认定为是慢查询。|

一条经典的慢查询SQL记录如下：
```
# Time: 2022-07-26T09:59:16.979869+08:00
# User@Host: root[root] @ localhost []  Id: 945574
# Query_time: 0.001096  Lock_time: 0.000127 Rows_sent: 199  Rows_examined: 1600 Thread_id: 945574 Errno: 0 Killed: 0 Bytes_received: 0 Bytes_sent: 25143 Read_first: 1 Read_last: 0 Read_key: 1601 Read_next: 0 Read_prev: 0 Read_rnd: 0 Read_rnd_next: 1801 Sort_merge_passes: 0 Sort_range_count: 0 Sort_rows: 0 Sort_scan_count: 0 Created_tmp_disk_tables: 0 Created_tmp_tables: 1 Start: 2022-07-26T09:59:16.978773+08:00 End: 2022-07-26T09:59:16.979869+08:00 Schema: sbtest Rows_affected: 0
# Tmp_tables: 1  Tmp_disk_tables: 0  Tmp_table_sizes: 0
# InnoDB_trx_id: 0
# Full_scan: Yes  Full_join: No  Tmp_table: Yes  Tmp_table_on_disk: No
# Filesort: No  Filesort_on_disk: No  Merge_passes: 0
#   InnoDB_IO_r_ops: 0  InnoDB_IO_r_bytes: 0  InnoDB_IO_r_wait: 0.000000
#   InnoDB_rec_lock_wait: 0.000000  InnoDB_queue_wait: 0.000000
#   InnoDB_pages_distinct: 24
SET timestamp=1658800756;
select c, count(*) from t1 group by c;
```

从上述日志中可以看到几个信息：

1. 这个SQL的耗时0.001096秒，即1毫秒。
2. 返回结果有199行，总共需要扫描1600行数据。如果扫描行数很多，但返回行数很少，说明该SQL效率很低，可能索引不当。
3. Read_* 等几个指标表示这个SQL读记录的方式，是否顺序读、随机读等。
4. Sort_* 等几个指标表示该SQL是否产生了排序，及其代价。如果有且代价较大，需要想办法优化。
5. *tmp* 等几个指标表示该SQL是否产生临时表，及其代价。如果有且代价较大，需要想办法优化。
6. Full_scan/Full_join表示是否产生了全表扫描或全表JOIN，如果有且SQL耗时较大，需要想办法优化。
7. InnoDB_IO_* 等几个指标表示InnoDB逻辑读相关数据。
8. InnoDB_rec_lock_wait 表示是否有行锁等待。
9. InnoDB_queue_wait 表示是否有排队等待。
10. InnoDB_pages_distinct 表示该SQL总共读取了多少个InnoDB page，是个非常重要的指标。

甚至还可以设置 `log_slow_verbosity = 'FULL,profiling'`，在慢查询日志中中，记录详细的profiling探针信息，例如：
```
# Time: 2022-07-26T10:35:15.599728+08:00
# User@Host: root[root] @ localhost []  Id: 950529
# Query_time: 0.001020  Lock_time: 0.000118 Rows_sent: 199  Rows_examined: 1600 Thread_id: 950529 Errno: 0 Killed: 0 Bytes_received: 0 Bytes_sent: 25143 Read_first: 1 Read_last: 0 Read_key: 1601 Read_next: 0 Read_prev: 0 Read_rnd: 0 Read_rnd_next: 1801 Sort_merge_passes: 0 Sort_range_count: 0 Sort_rows: 0 Sort_scan_count: 0 Created_tmp_disk_tables: 0 Created_tmp_tables: 1 Start: 2022-07-26T10:35:15.598708+08:00 End: 2022-07-26T10:35:15.599728+08:00 Schema: sbtest Rows_affected: 0
# Tmp_tables: 1  Tmp_disk_tables: 0  Tmp_table_sizes: 0
# Profile_starting: 0.000070 Profile_starting_cpu: 0.000069 Profile_Executing_hook_on_transaction_begin.: 0.000006 Profile_Executing_hook_on_transaction_begin._cpu: 0.000006 Profile_starting: 0.000009 Profile_starting_cpu: 0.000009 Profile_checking_permissions: 0.000003 Profile_checking_permissions_cpu: 0.000003 Profile_Opening_tables: 0.000028 Profile_Opening_tables_cpu: 0.000028 Profile_init: 0.000003 Profile_init_cpu: 0.000002 Profile_System_lock: 0.000006 Profile_System_lock_cpu: 0.000006 Profile_optimizing: 0.000003 Profile_optimizing_cpu: 0.000003 Profile_statistics: 0.000010 Profile_statistics_cpu: 0.000010 Profile_preparing: 0.000007 Profile_preparing_cpu: 0.000007 Profile_Creating_tmp_table: 0.000026 Profile_Creating_tmp_table_cpu: 0.000026 Profile_executing: 0.000823 Profile_executing_cpu: 0.000807 Profile_end: 0.000003 Profile_end_cpu: 0.000003 Profile_query_end: 0.000002 Profile_query_end_cpu: 0.000002 Profile_waiting_for_handler_commit: 0.000008 Profile_waiting_for_handler_commit_cpu: 0.000010 Profile_closing_tables: 0.000006 Profile_closing_tables_cpu: 0.000005 Profile_freeing_items: 0.000009 Profile_freeing_items_cpu: 0.000009 Profile_logging_slow_query: 0.000001 Profile_logging_slow_query_cpu: 0.000001
# Profile_total: 0.001024 Profile_total_cpu: 0.001007
# InnoDB_trx_id: 0
# Full_scan: Yes  Full_join: No  Tmp_table: Yes  Tmp_table_on_disk: No
# Filesort: No  Filesort_on_disk: No  Merge_passes: 0
#   InnoDB_IO_r_ops: 0  InnoDB_IO_r_bytes: 0  InnoDB_IO_r_wait: 0.000000
#   InnoDB_rec_lock_wait: 0.000000  InnoDB_queue_wait: 0.000000
#   InnoDB_pages_distinct: 24
SET timestamp=1658802915;
select c, count(*) from t1 group by c;
```
这样可以通过profiling信息更快定位该SQL的性能瓶颈可能在什么地方了。

更详细解读请参考：[Slow Query Log](https://www.percona.com/doc/percona-server/5.6/diagnostics/slow_extended.html#id1)。

## 2. 利用pt-query-digest分析慢查询SQL

`pt-query-digest`是Percona出品的`pt-toolkit`包中的一个工具，主要用于分析MySQL慢查询。除了慢查询外，它还可以分析binlog、general log，也可以通过 `SHOW PROCESSLIST` 或者通过tcpdump抓取的MySQL数据包进行实时分析。

安装过程略过，请参考文档：[Installing Percona Toolkit](https://www.percona.com/doc/percona-toolkit/LATEST/installation.html)。

本文中以简单分析slow query log文件为例：
```
$ pt-query-digest /data/GreatSQL/slow.log > /tmp/slow-digest.txt
```

可以不用加任何额外参数，直接分析，并将分析结果输出到另一个文件，在这个文件中可以直接展示各查询的执行时间、次数、占比等信息，例如：
```
/* 工具分析日志消耗的用户时间、系统时间，以及物理内存，虚拟内存大小 */
# 15.7s user time, 360ms system time, 41.25M rss, 186.59M vsz
# Current date: Sat Jan  7 23:11:32 2022
# Hostname: greatsql
# Files: slow.log
/* 共有多少条慢查询，格式化之后共有435条SQL */
# Overall: 29.40k total, 435 unique, 0 QPS, 0x concurrency _______________
# Attribute          total     min     max     avg     95%  stddev  median
# ============     ======= ======= ======= ======= ======= ======= =======
/* 所有SQL总耗时、最小耗时、平均耗时，95%耗时，平均方差，中位数耗时 */
# Exec time         37138s   500ms    142s      1s      3s      2s   705ms
/* 锁等待耗时 */
# Lock time          3535s       0    135s   120ms   609ms   927ms   224us
/* 发送到客户端数据量 */
# Rows sent        435.22M       0   1.70M  15.16k  65.68k  52.60k       0
/* 扫描数据量 *
# Rows examine       1.45G       0   3.40M  51.87k  65.68k  71.73k  65.68k
/* insert/update/delete 影响的行数 */
# Rows affecte       1.87M       0   1.70M   66.53    2.90  10.07k    1.96
/* 发送字节数 */
# Bytes sent        32.88G       0  57.75M   1.14M   2.88M   4.74M   51.63
/* SQL大小 */
# Query size         7.75M       6 1014.67k  276.42  487.09   6.15k  124.25
```
首先是汇总的统计信息。

其次是根据响应总耗时排序，就可以看到哪些SQL可能存在性能瓶颈：
```
...
# Profile
/* 排名、SQL语句ID/标识符、响应总耗时、占比、总请求数、平均每次请求耗时、响应时间Variance-to-mean的比率、SQL语句 */
# Rank Query ID           Response time    Calls R/Call V/M   Item
# ==== ================== ================ ===== ====== ===== ============
#    1 0xCBFFFDC5A18B5CD4 13077.1621 35.2% 14945 0.8750  0.44 UPDATE wp_statistics_visit
#    2 0x813031B8BBC3B329  4878.6998 13.1%  2245 2.1731  5.10 COMMIT
#    3 0x67A347A2812914DF  2798.8377  7.5%  1515 1.8474  7.88 SELECT wp_statistics_visitor
#    4 0xD1A3ED0A00CB8636  2261.3010  6.1%  3807 0.5940  0.03 SELECT wp_statistics_visit
#    5 0x0359C20B19D50ED6   937.8136  2.5%   505 1.8571  0.56 UPDATE wp_statistics_visitor
#    6 0x8A0E5C140D1FEAE6   883.8182  2.4%   433 2.0412  2.44 UPDATE aws_sessions
#    7 0x94350EA2AB8AAC34   817.2749  2.2%   292 2.7989 22.57 UPDATE wp_options
#    8 0xA766EE8F7AB39063   657.8637  1.8%   348 1.8904  2.49 SELECT wp_terms wp_term_taxonomy wp_term_relationships
#    9 0xE35B37A6116CF667   657.3250  1.8%   322 2.0414  4.78 SELECT drupal_cache_field
#   10 0x3249292D0F4247BD   655.1189  1.8%   237 2.7642  7.89 INSERT drupal_cache_page
#   11 0xC6E83D2D23B205EB   548.1317  1.5%   263 2.0842  4.72 DELETE pre_common_session
#   12 0xC88DD5CE28F8574B   535.7342  1.4%   189 2.8346 10.93 INSERT pre_common_session
#   13 0x7FF1B2B54A693E87   509.4790  1.4%   287 1.7752  5.14 SELECT INFORMATION_SCHEMA.FILES INFORMATION_SCHEMA.PARTITIONS
#   14 0x0D7200302E76DA57   449.4795  1.2%   125 3.5958 42.33 INSERT drupal_captcha_sessions
```

接下来是具体某条SQL的分析情况，平均及最大耗时，平均及最大扫描行数，不同响应耗时区间占比情况等：
```
# Query 1: 0 QPS, 0x concurrency, ID 0xCBFFFDC5A18B5CD4 at byte 9260279 __
# This item is included in the report because it matches --limit.
# Scores: V/M = 0.44
# Attribute    pct   total     min     max     avg     95%  stddev  median
# ============ === ======= ======= ======= ======= ======= ======= =======
# Count         50   14945
# Exec time     35  13077s   500ms     11s   875ms      2s   623ms   640ms
# Lock time     83   2955s    89us      7s   198ms   900ms   481ms   247us
# Rows sent      0       0       0       0       0       0       0       0
# Rows examine  66 986.11M  67.36k  67.72k  67.57k  65.68k       0  65.68k
# Rows affecte   1  32.31k       1       7    2.21    2.90    0.51    1.96
# Bytes sent     0 758.93k      52      52      52      52       0      52
# Query size    23   1.80M     126     126     126     126       0     126
# String:
# Databases    greatsql
# Hosts        greatsql
# Last errno   0
# Time         2022-07-13... (1/0%), 2022-07-13... (1/0%)... 14943 more
# Users        greatsql
# Query_time distribution
#   1us
#  10us
# 100us
#   1ms
#  10ms
# 100ms  ################################################################
#    1s  ################
#  10s+  #
# Tables
#    SHOW TABLE STATUS FROM `greatsql` LIKE 'wp_statistics_visit'\G
#    SHOW CREATE TABLE `greatsql`.`wp_statistics_visit`\G
UPDATE wp_statistics_visit SET `visit` = `visit` + 1, `last_visit` = '2021-10-17 00:04:53' WHERE `last_counter` = '2021-10-17'\G
# Converted for EXPLAIN
# EXPLAIN /*!50100 PARTITIONS*/
select  `visit` = `visit` + 1, `last_visit` = '2021-10-17 00:04:53' from wp_statistics_visit where  `last_counter` = '2021-10-17'\G
```
在最后，甚至还直接把UPDATE改写成SELECT，方便直接查看该SQL的执行计划。

`pt-query-digest` 分析结果中已经做好排序，按照这个顺序优先对排在前面的慢查询SQL进行优化，对数据库性能提升会有显著效果。

P.S，还可以利用pt-query-digest工具将慢查询SQL分析后写入数据库，并结合Anemometer构建慢查询管理系统。

## 3. 慢查询SQL优化

接下来以一个慢查询SQL为例，来看看如何优化。

首先，查看该SQL的执行计划：
```
mysql> explain select c, count(*) from t1 group by c\G
           id: 1
  select_type: SIMPLE
        table: t1
   partitions: NULL
         type: ALL
possible_keys: NULL
          key: NULL
      key_len: NULL
          ref: NULL
         rows: 1613
     filtered: 100.00
        Extra: Using temporary
```
可以看到，执行计划表明这条SQL需要进行全表扫描，没有索引可用，并且会产生临时表。

针对上述情况，且上面的SQL也比较简单，只需要对 `c` 列添加索引即可：
```
mysql> alter table t1 add index (c );

# 再次查看执行计划
mysql> explain select c, count(*) from t1 group by c\G
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: t1
   partitions: NULL
         type: index
possible_keys: c
          key: c
      key_len: 480
          ref: NULL
         rows: 1613
     filtered: 100.00
        Extra: Using index
```
可以看到，已经能走索引，并且没有临时表了。

生产环境中的业务SQL一般比这种更复杂，SQL优化需要根据实际情况灵活变化，通常不只是添加索引这么简单。

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
