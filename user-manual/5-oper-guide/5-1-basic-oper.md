# 日常管理
---

本文档描述GreatSQL数据库的日常管理操作，主要包括服务管理、参数选项调整等。

## 1. 服务管理

无论是RPM、二进制包还是Ansible等何种方式安装GreatSQL，都建议采用systemd来管理GreatSQL服务。在Docker容器环境中，无需利用systemd来管理GreatSQL，直接整个容器启停即可。

如果是RPM包方式安装GreatSQL，则服务名为 `mysqld`，如果采用二进制包和Ansible方式安装，则服务名为 `greatsql`。为了方便，本文档中统一约定为 `greatsql`。

**启动服务**
```
$ systemctl start greatsql
```

**停止服务**
```
$ systemctl stop greatsql
```

**重启服务**
```
$ systemctl restart greatsql
```

**查看服务状态**
```
$ systemctl status greatsql
```

如果执行过程中有报错，则运行下面的命令查看错误信息：
```
$ journalctl -ex
```

## 2. 修改参数选项

### 2.1 SQL命令行修改并立即生效

可以通过SQL命令在线修改GreatSQL中的大多数参数选项并立即生效。

首先，查看要修改的参数选项当前值：
```
mysql> show global variables like 'innodb_buffer_pool_size';
+-------------------------+------------+
| Variable_name           | Value      |
+-------------------------+------------+
| innodb_buffer_pool_size | 6442450944 |
+-------------------------+------------+
```

执行SET命令修改该选项值：
```
# 修改为8G
mysql> set global innodb_buffer_pool_size = 8589934592;
Query OK, 0 rows affected (0.00 sec)

# 再次查看，确认生效
mysql> show global variables like 'innodb_buffer_pool_size';
+-------------------------+------------+
| Variable_name           | Value      |
+-------------------------+------------+
| innodb_buffer_pool_size | 4294967296 |
+-------------------------+------------+
```

直接在线修改选项值有个风险，就是只记得动态修改当前值，但是忘记修改 `my.cnf` 中的选项，数据库重启后，这个修改会被重置。

因此，建议用另一种方式修改：
```
myqsl> set persist innodb_buffer_pool_size = 4294967296;
Query OK, 0 rows affected (0.00 sec)

mysql> show global variables like 'innodb_buffer_pool_size';
+-------------------------+------------+
| Variable_name           | Value      |
+-------------------------+------------+
| innodb_buffer_pool_size | 6442450944 |
+-------------------------+------------+
```
采用 `set persist` 方式修改选项值的话，除了会立即修改之外，还会在 `datadir/mysqld-auto.cnf` 中记录本次修改，并在下一次重启时加载该选项值使之生效。当然了，前提是选项值 `persisted_globals_load = ON`（默认值也是 ON）。

这样就不担心只修改当前值而忘记修改 `my.cnf` 中的选项值了。

不过也可能DBA在排查问题时，只记得查看 `my.cnf` 文件，而忘记检查 `mysqld-auto.cnf` 文件，这个也要注意下。

### 2.2 只修改选项值，重启后生效

还可以只修改选项值，但不立即生效，数据库重启后才生效，可以有几种方式。

第一种是直接修改 `my.cnf` 文件，保存退出，数据库下次重启时就会生效了。

第二种是执行 `set persist_only` 修改，这时候只会将新的选项值记录到 `mysqld-auto.cnf` 中，并不会立即修改内存中的选项值。
```
mysql> show global variables like 'innodb_buffer_pool_size';
+-------------------------+------------+
| Variable_name           | Value      |
+-------------------------+------------+
| innodb_buffer_pool_size | 6442450944 |
+-------------------------+------------+
1 row in set (0.01 sec)

mysql> set persist_only innodb_buffer_pool_size = 4294967296;
Query OK, 0 rows affected (0.00 sec)

mysql> show global variables like 'innodb_buffer_pool_size';
+-------------------------+------------+
| Variable_name           | Value      |
+-------------------------+------------+
| innodb_buffer_pool_size | 6442450944 |
+-------------------------+------------+

$ grep innodb_buffer_pool_size /data/GreatSQL/mysqld-auto.cnf
...
"innodb_buffer_pool_size" : { "Value" : "4294967296" , "Metadata" : { "Timestamp" : 1658134448865009 , "User" : "root" , "Host" : "localhost" } } ,
...
```
可以看到，新的选项值已经写入 `mysqld-auto.cnf` 中，而当前运行状态的内存值还保持不变。

## 3. 其他管理

### 3.1 日志管理

数据库运行期间，会生成各种日志，包括请求日志（general log）、错误日志（error log）、慢查询日志（slow query log）、二进制日志（binary log）、中继日志（relay log）等。

默认情况下，只会启用error log、binary log、relay log，而general log、slow query log则默认不会启用。

此外，还有InnoDB存储引擎层的redo log（重做日志）和undo log（撤销日志）。

| 日志 | 简述 |
| --- | --- |
| binary log | 简称binlog，记录对数据库的各种变更操作，主要用于数据库复制和数据恢复 |
| error log | 记录MySQL启动，运行过程，停止中产生的各种错误信息，便于排查故障 |
| slow query log | 记录被认定为慢查询类型的SQL语句 |
| relay log | 主从复制过程中，从节点上的转储日志，用于从节点应用数据库变更操作，以保持和主节点的数据一致 |
| general log | 详细记录连接建立和执行的所有SQL语句，通常临时打开用于故障排查或SQL审计 |
| redo log | InnoDB引擎记录数据页修改的日志，遵循WAL原则，用于保障数据库的crash safe，同时也用于在线热备 |
| undo log | 记录数据变更前的信息，主要用于事务回滚，同时也用于多版本并发控制 |

### 3.2 清理binlog

数据库运行过程中，随着用户对数据库不断执行各种操作，binlog会不断增加，默认设置是30天（`binlog_expire_logs_seconds
= 2592000`）才会自动清理，因此当可用磁盘空间较为紧张时，就需要手动执行清理binlog操作。例如：
```
mysql> show binary logs;
show binary logs;
+---------------------+------------+
| Log_name            | File_size  |
+---------------------+------------+
| greatsql-bin.001425 | 1076686944 |
| greatsql-bin.001426 | 1075651098 |
...
| greatsql-bin.001465 | 1077719005 |
| greatsql-bin.001466 |  416814070 |
+---------------------+------------+
42 rows in set (0.00 sec)

# 可以看到共有42个binlog
# 举例现在只想保留最近2个，其余都清除
mysql> purge binary logs to 'greatsql-bin.001465';
Query OK, 0 rows affected (1.99 sec)

# 再次查看
# 当前对数据库正在做压测，所以又很快生成了很多binlog
mysql> show binary logs;
+---------------------+------------+
| Log_name            | File_size  |
+---------------------+------------+
| greatsql-bin.001465 | 1077719005 |
| greatsql-bin.001466 | 1074612115 |
...
| greatsql-bin.001480 | 1074615588 |
| greatsql-bin.001481 |  856380441 |
+---------------------+------------+
17 rows in set (0.00 sec)

# 重新设置binlog自动清理周期为7天
mysql> set persist binlog_expire_logs_seconds = 604800;
```
**提醒：** 清理binlog前，请务必记得做好备份，避免影响后续的数据库恢复需要。

### 3.3 清理slow query log

当启用记录slow query log时，可能会因为业务压力较大，或者因为`long_query_time`阈值设置太低，或者因为设置了`log_queries_not_using_indexes = ON`而记录大量无索引SQL请求，最终导致slow query log文件过大，也需要定期检查清理。

下面是适用于大多数业务场景的slow query log设置参考：
```
slow_query_log = 1
log_slow_extra = 1
log_slow_verbosity = FULL
slow_query_log_file = slow.log
long_query_time = 0.05
log_queries_not_using_indexes = 1
log_throttle_queries_not_using_indexes = 60
min_examined_row_limit = 0
log_slow_admin_statements = 1

#MySQL 8.0.26后改成log_slow_replica_statements
log_slow_slave_statements = 1
```

可以执行下面的命令清理slow query log，清理前也记得先做好备份：
```
$ cp slow.log slow.log-`date +%Y%m%d`
$ echo '' > slow.log

# 再进入GreatSQL，执行SQL命令
mysql> flush slow logs;
```
这样就可以清空slow query log了。

### 3.4 清理general log/error log

和清理slow query log差不多，也是先做好日志文件备份，然后执行SQL命令：
```
mysql> flush general logs;

mysql> flush error logs;
```

详情参考文档：[FLUSH Statement](https://dev.mysql.com/doc/refman/8.0/en/flush.html)。

### 3.5 数据安全维护建议

为了让GreatSQL数据库运行更安全，建议遵循以下几点规范：

- 在应用端，所有用户请求及输入数据都要做预处理，不能直接提交到数据库，避免被SQL注入。
- 定期扫描应用端用户请求日志，扫描异常请求并及时处理。
- 应用服务器端部署防火墙，阻断用户非法请求。
- 应用程序上线前，都需要进行必要安全扫描，避免常见SQL注入等风险。
- 数据库端定期扫描请求特征，判断是否有符合安全隐患的请求，及时阻断处理。
- 数据库端启用审计（AUDIT）、SQL防火墙等组件，及时发现并阻断非法请求。
- 数据库中存储的敏感数据，务必先进行单向加密，避免被破解、信息泄漏。
- 生产环境中的数据，导入开发测试环境前，要先进行转码脱敏操作，避免信息泄漏。
- 做好连接请求检测和监控，发现有异常频繁请求时，及时阻断处理。

### 3.6 例行维护表

通常来说，生产环境中的数据表是无需维护的，除非出现以下几种情况：

- 索引统计信息存在严重偏差，影响SQL执行计划。
- 数据表存在大量碎片/空洞，极可能导致该表物理I/O效率降低。

针对上述两种情况，我们可以定期对数据表进行必要的维护工作。

1. 更新索引统计信息

首先，执行下面的SQL，找到那些可能存在索引统计信息不准确的表：

>
> 工作方式
>
> 1、扫描所有索引统计信息
>
> 2、包含主键列的辅助索引统计值，对比主键索引列的统计值，得到一个百分比stat_pct
>
> 3、根据stat_pct排序，值越低说明辅助索引统计信息越不精确，越是需要关注
>

```
mysql> set @statdb = 'greatsql';
select 
a.database_name ,
a.table_name ,
a.index_name ,
a.stat_value SK,
b.stat_value PK, 
round((a.stat_value/b.stat_value)*100,2) stat_pct
from 
(
select 
b.database_name  ,
b.table_name  ,
b.index_name ,  
b.stat_value
from 
(
select database_name  ,
table_name  ,
index_name ,  
max(stat_name) stat_name 
from innodb_index_stats 
where   database_name = @statdb
and stat_name not in ( 'size' ,'n_leaf_pages' )
group by 
database_name  ,
table_name  ,
index_name   
) a join innodb_index_stats b on a.database_name=b.database_name
and a.table_name=b.table_name
and a.index_name=b.index_name
and a.stat_name=b.stat_name 
and b.index_name !='PRIMARY'
) a left join 
(
select 
b.database_name  ,
b.table_name  ,
b.index_name ,  
b.stat_value
from 
(
select database_name  ,
table_name  ,
index_name ,  
max(stat_name) stat_name 
from innodb_index_stats 
where   database_name = @statdb
and stat_name not in ( 'size' ,'n_leaf_pages' )
group by 
database_name  ,
table_name  ,
index_name   
) a join innodb_index_stats b 
on a.database_name=b.database_name
and a.table_name=b.table_name
and a.index_name=b.index_name
and a.stat_name=b.stat_name
and b.index_name ='PRIMARY'
) b 
on a.database_name=b.database_name
and a.table_name=b.table_name
where b.stat_value is not null 
and  a.stat_value >0
order by stat_pct;

+---------------+-------------------+--------------+--------+--------+----------+
| database_name | table_name        | index_name   | SK     | PK     | stat_pct |
+---------------+-------------------+--------------+--------+--------+----------+
| greatsql      | t_json_vs_vchar   | c1vc         |  37326 |  39825 |    93.73 |
| greatsql      | t_json_vs_vchar   | c2vc         |  37371 |  39825 |    93.84 |
| greatsql      | t1                | name         | 299815 | 299842 |    99.99 |
| greatsql      | t4                | c2           |      2 |      2 |   100.00 |
+---------------+-------------------+--------------+--------+--------+----------+
```

当然了，在检查分析业务SQL时，通常也会查看其执行计划，如果发现个别SQL执行计划不如预期，也可能是索引统计信息不准确导致，这时也可以人工确认下。

在业务负载低谷时段执行下面的命令更新索引统计信息：
```
mysql> analyze table t1;
+-------------+---------+----------+----------+
| Table       | Op      | Msg_type | Msg_text |
+-------------+---------+----------+----------+
| greatsql.t1 | analyze | status   | OK       |
+-------------+---------+----------+----------+
1 row in set (0.01 sec)
```

正常情况下，上述维护命令执行很快就能跑完。

不过当该表已被加上MDL锁，则会被阻塞，所以执行前最好检查下。

执行 `analyze table` 期间会对数据表加上只读锁，因为还需要将该表从 `table definition cache` 中移除，所以还需要加上 `flush` 锁。

MySQL 8.0.24之前，如果该表上有请求还未结束，这时候再执行 `analyze table`，那么之后对该表的其他请求也会被阻塞，这个情况在8.0.24之后得到解决。

另外，执行 `analyze table` 操作还会写入binlog，所以从节点也会跟着做一遍。如果不想让其写入binlog，可以加上 `NO_WRITE_TO_BINLOG` 关键字。

参考文档：

- [mysql-toolkit-sql](https://github.com/zhishutech/mysqldba/blob/master/mysql-tools/mysql-toolkit-sql.md)。
- [ANALYZE TABLE Statement](https://dev.mysql.com/doc/refman/8.0/en/analyze-table.html)。

2. 重整数据表消除碎片

线上生产环境中的数据表，可能因为表结构设计不合理，或者在经过长时间随机写请求后，产生大量碎片，极可能导致该表物理I/O效率降低。

如果碎片率特别高，而且对性能影响也的确特别严重的话，就需要重整表空间消除碎片了。

首先，执行下面的SQL命令查看哪些表碎片率可能较高：
```
mysql> SELECT TABLE_SCHEMA as `db`, TABLE_NAME as `tbl`, 
1-(TABLE_ROWS*AVG_ROW_LENGTH)/(DATA_LENGTH + INDEX_LENGTH + DATA_FREE) AS `fragment_pct`,
TABLE_ROWS
FROM information_schema.TABLES WHERE 
TABLE_SCHEMA = 'greatsql' AND TABLE_ROWS >= 10000 ORDER BY fragment_pct DESC, TABLE_ROWS DESC;
+----------+----------+--------------+------------+
| db       | tbl      | fragment_pct | TABLE_ROWS |
+----------+----------+--------------+------------+
| greatsql | sbtest1  |       0.5492 |      12578 |
| greatsql | sbtest2  |       0.5492 |      12450 |
| greatsql | sbtest10 |       0.4874 |      12780 |
| greatsql | sbtest6  |       0.4871 |      13034 |
...
```

查询结果以碎片率倒序排序，排在前面的碎片率更高。当然了，如果表的数据量很少，可能会导致这个统计不准确，也要识别下。

如果表数据量较小，或者表空间文件较小，则可以直接执行下面的SQL命令重整表空间消除碎片：
```
mysql> alter table sbtest1 engine = innodb;
```

如果表数据量较大，或者表空间文件较大，则**强烈建议**采用 `pt-online-schema-change` 工具重整表空间消除碎片，例如：
```
$ pt-online-schema-change --socket=/data/GreatSQL/mysql.sock --alter "ENGINE=InnoDB" D=greatsql,t=sbtest1
No slaves found.  See --recursion-method if host greatsql has slaves.
Not checking slave lag because no slaves were found and --check-slave-lag was not specified.
Operation, tries, wait:
  analyze_table, 10, 1
  copy_rows, 10, 0.25
  create_triggers, 10, 1
  drop_triggers, 10, 1
  swap_tables, 10, 1
  update_foreign_keys, 10, 1
Altering `greatsql`.`sbtest1`...
Creating new table...
Created new table greatsql._sbtest1_new OK.
Altering new table...
Altered `greatsql`.`_sbtest1_new` OK.
2022-07-19T15:24:07 Creating triggers...
2022-07-19T15:24:07 Created triggers OK.
2022-07-19T15:24:07 Copying approximately 12578 rows...
2022-07-19T15:24:07 Copied rows OK.
2022-07-19T15:24:07 Analyzing new table...
2022-07-19T15:24:07 Swapping tables...
2022-07-19T15:24:07 Swapped original and new tables OK.
2022-07-19T15:24:07 Dropping old table...
2022-07-19T15:24:07 Dropped old table `greatsql`.`_sbtest1_old` OK.
2022-07-19T15:24:07 Dropping triggers...
2022-07-19T15:24:07 Dropped triggers OK.
Successfully altered `greatsql`.`sbtest1`.
```
这就完成表空间重整，可以有效消除碎片。

**提醒：** 重整表空间时，注意系统剩余磁盘空间是否足够，因为重整期间可能会将整个表复制一遍，把磁盘空间撑爆。

数据库日常运行过程中，需要关注哪些事项，需要做哪些例行检查，可以参考下面几个资源：

- [mysql-toolkit-sql](https://github.com/zhishutech/mysqldba/blob/master/mysql-tools/mysql-toolkit-sql.md)
- [check_mysql.py](https://github.com/zhishutech/mysqldba/blob/master/mysql-tools/check_mysql.py)
- [MySQL巡检怎么做](https://github.com/zhishutech/mysqldba/blob/master/mysql-tools/MySQL%E5%B7%A1%E6%A3%80%E6%80%8E%E4%B9%88%E5%81%9A%EF%BC%9F.md)

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
