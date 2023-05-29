# 并行load data

[toc]

## 1. MySQL原生load data局限

MySQL原生的load data采用单线程读取本地文件（或收取client传来的网络数据包），逐行获取内容并调用数据库write_row()接口插入数据。当导入的单个文件很大时，单线程处理模式无法充分利用数据库的资源，导致执行时间很长。又由于load data导入的数据在一个事务内，当binlog事务超过2G时，无法使用binlog在MGR集群间同步。

## 2. GreatSQL parallel load data

为解决上述两个问题，GreatSQL新增parallel load data并行导入特性。开启并行导入特性后，GreatSQL会自动将导入的文件切分文件成多个小块（块大小可配置），然后启动多个worker线程（数量可配置）导入文件块。

并行导入与存储引擎无关，理论上可以支持所有的储引擎。

## 3. 相关变量

| 变量名| 含义| 取值范围及单位 | 默认值 |
| --- | --- | ---- | --- |
| greatsql_parallel_load| 是否开启并行导入(session only) |ON/OFF|OFF|
|greatsql_parallel_load_chunk_size | 并行导入时，文件切割的大小|64k-128M，字节|1M|
| greatsql_parallel_load_workers| 并行导入最大worker线程数       | 1-32| 8|

## 4. 启用并行load data

可采用两种方式启用并行load data：

1. **设置session级变量启用**

连接数据库，执行 `SET SESSION greatsql_parallel_load=ON`。

如需调整文件块大小或线程数，执行 `SET SESSION greatsql_parallel_load_chunk_size=65536` 或 `SET SESSION greatsql_parallel_load_workers=16`。

然后执行load data语句导入文件。
```
LOAD DATA INFILE '/tmp/load.txt' INTO TABLE t1;
```

2. **load语句增加hint启用**

```sql

LOAD /*+ SET_VAR(greatsql_parallel_load=ON) SET_VAR(greatsql_parallel_load_chunk_size=65536) SET_VAR(greatsql_parallel_load_workers=16) */
DATA INFILE '/tmp/load.txt' INTO TABLE t1;
```

## 5. 检查并行导入进度

worker线程会创建新的session导入文件块，可通过执行 `show processlist` 看到worker线程正在执行的语句。

语句的格式为：
```sql
LOAD /*parallel load worker(chunk_no:xxx)*/ DATA INFILE 'session_id:worker_no' INTO ...
```

其中 `chunk_no` 代表文件块的编号，每新产生一个文件块时 `chunk_no` 增加1，可通过文件原始大小除以 `gdb_parallel_load_chunk_size`，得到 `chunk_no` 并大致判断出导入进度。

`session_id` 表示初始执行 `load data` 语句的那个 session_id，即 `master_session_id`。而`worker_no` 表示启动的worker线程编号。

## 6. 特殊限制

**1. 非原子性：**  启动并行导入后，若中途失败，已执行导入的文件块无法回滚。因此请不要用于在线业务系统的数据表，而是先导入到某个临时表，完全导入成功后，再将数据加载到正式业务表中。

**2. session变量支持受限：** 若导入语句使用了类似 `connection_id()` 这类会话相关的变量或函数时，worker session无法正确导入。

**3. 不支持replace into：** 不支持replace into方式插入。

## 7. 并行导入提升测试

受限于master session的文件分割速度，并行导入速度可能区别较大。经过测试，在磁盘IO和CPU核心资源都充足的前提下启动32个worker，最大的加速比大概为20倍。

=======以下测试结果无需发布到外部=====

下面是我用普通测试机运行测试的结果：
- 表数据量：2165600行（Avg_row_length: 141）。
- 加载文件大小：206657411字节。
- 生成的binlog大小：190M（开启并行与否，binlog文件总大小都差不多）。
- **导入效率提升：113.39%**（开启并行导入后，耗时只有原来的46.86%，不到一半）。
- **表空间大小膨胀率：17.46%**。

相关几个指标数据如下：

| 指标 | 未开启并行 | 开启并行 | 
| --- | --- | --- | 
| binlog文件大小 | 198243540 | 198376947 |
| 事务数 | 1 | 200 |
| 耗时（秒）| 11.62 | 5.45 |
|表空间大小(字节)|264241152|310378496|




load data infile '/tmp/tt.csv' into table tt;
Query OK, 2165600 rows affected (11.68 sec)
Query OK, 2165600 rows affected (11.48 sec)
Query OK, 2165600 rows affected (11.71 sec)

vs并行
case1:
| gdb_parallel_load_chunk_size | 1048576 |
| gdb_parallel_load_workers    | 8       |
Query OK, 2165600 rows affected (6.10 sec)
Query OK, 2165600 rows affected (5.74 sec)
Query OK, 2165600 rows affected (5.96 sec)
Query OK, 2165600 rows affected (5.84 sec)

case2:
| gdb_parallel_load_chunk_size | 1048576 |
| gdb_parallel_load_workers    | 14      |
Query OK, 2165600 rows affected (5.60 sec)
Query OK, 2165600 rows affected (5.51 sec)
Query OK, 2165600 rows affected (5.32 sec)
Query OK, 2165600 rows affected (5.36 sec)

case3:
| gdb_parallel_load_chunk_size | 4194304 |
| gdb_parallel_load_workers    | 8       |
Query OK, 2165600 rows affected (6.38 sec)
Query OK, 2165600 rows affected (5.69 sec)
Query OK, 2165600 rows affected (6.34 sec)
Query OK, 2165600 rows affected (6.11 sec)

case4:
| gdb_parallel_load_chunk_size | 524288 |
| gdb_parallel_load_workers    | 14     |
Query OK, 2165600 rows affected (5.57 sec)
Query OK, 2165600 rows affected (5.39 sec)
Query OK, 2165600 rows affected (5.56 sec)
Query OK, 2165600 rows affected (5.17 sec)

case5:
| gdb_parallel_load_chunk_size | 524288 |
| gdb_parallel_load_workers    | 32     |
Query OK, 2165600 rows affected (7.92 sec)
Query OK, 2165600 rows affected (6.87 sec)

case6:
| gdb_parallel_load_chunk_size | 2097152 |
| gdb_parallel_load_workers    | 14      |
Query OK, 2165600 rows affected (5.81 sec)
Query OK, 2165600 rows affected (6.59 sec)
Query OK, 2165600 rows affected (5.68 sec)
Query OK, 2165600 rows affected (5.41 sec)
Query OK, 2165600 rows affected (5.36 sec)
