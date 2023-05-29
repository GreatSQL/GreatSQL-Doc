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


=======以下内容无需发布到外部=====

### 7. 使用并行导入初始化benchmarksql数据

使用benchmarksql导入数据时，每生成一次数据都和数据库交互一次，效率低下且耗时较久，若中间出错需要重新导入。因此建议使用benchmarksql产生csv文件并通过并行load data导入的方式能够将数据导入流程解耦，加快导入速度。

操作步骤分为
```
1. 生成csv文件
2. 创建目标表结构
3. 执行数据导入
4. 创建索引
```

### 7.2 生成csv文件

生成csv文件前，需要修改benchmarksql的配（props.my）文件，并且保证JDBC连接串指向的数据库能够正常连接且存在目标数据库。

修改需要的仓库数。

设置loadworers线程数。一般为cpu逻辑核心数减去1-2个即可。

```
# benchmarksql根目录"run/props.my"
conn=jdbc:mysql://localhost:3336/benchmarksql?useSSL=false
warehouses=1000
loadWorkers=15
```

建立存放文件的数据目录，并在/tmp目录创建软连接

```
mkdir -p /bs_files/
chmod 777 /bs_files/
ln -s /bs_files /tmp/csv
```

进入benchmark的run目录，执行以下语句。**需要注意创建的软链接后需要加斜杠**

```
./runLoader.sh ./props.my filelocation /tmp/csv/
```

### 7.3 创建数据表

进入benchmarksql的run目录，执行下列语句创建表（如果测试集群，需要修改建表语句按warehouse_id分区）。

```
./runSQL.sh ./props.my ./sql.mysql/tableCreates.sql
```

若中途失败，可通过以下语句删除重建

```
./runSQL.sh ./props.my ./sql.common/tableDrops.sql
```



### 7.4 执行数据导入

load data按数据文件所在位置有两种方式。一种是数据文件存在client端，通过client传输数据给server；另一种是将数据文件传到server所在机器或直接在server机器上生成csv。详情参考MySQL官方手册：https://dev.mysql.com/doc/refman/8.0/en/load-data.html。以下内容以数据文件存放在server为前提。

benchmarksql根目录的run目录下默认没有mysql的load data语句，因此需要在“run/sql.mysql”目录下创建文件`tableCopies.sql`，内容如下：

```sql
set session gdb_parallel_load=on;
set session gdb_parallel_load_chunk_size=16777216;
set session gdb_parallel_load_workers=16;

LOAD DATA INFILE '/tmp/csv/config.csv' INTO TABLE bmsql_config
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'
(cfg_name, cfg_value);

LOAD DATA INFILE '/tmp/csv/warehouse.csv' INTO TABLE bmsql_warehouse
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'
(w_id, w_ytd, w_tax, w_name, w_street_1, w_street_2, w_city, w_state, w_zip);

LOAD DATA INFILE '/tmp/csv/item.csv' INTO TABLE bmsql_item
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'
(i_id, i_name, i_price, i_data, i_im_id);

LOAD DATA INFILE '/tmp/csv/stock.csv' INTO TABLE bmsql_stock
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'
(s_i_id, s_w_id, s_quantity, s_ytd, s_order_cnt, s_remote_cnt, s_data,
s_dist_01, s_dist_02, s_dist_03, s_dist_04, s_dist_05,
s_dist_06, s_dist_07, s_dist_08, s_dist_09, s_dist_10);

LOAD DATA INFILE '/tmp/csv/district.csv' INTO TABLE bmsql_district
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'
(d_id, d_w_id, d_ytd, d_tax, d_next_o_id, d_name, d_street_1,
d_street_2, d_city, d_state, d_zip);

LOAD DATA INFILE '/tmp/csv/customer.csv' INTO TABLE bmsql_customer
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'
(c_id, c_d_id, c_w_id, c_discount, c_credit, c_last, c_first, c_credit_lim,
c_balance, c_ytd_payment, c_payment_cnt, c_delivery_cnt, c_street_1,
c_street_2, c_city, c_state, c_zip, c_phone, c_since, c_middle, c_data);

LOAD DATA INFILE '/tmp/csv/cust-hist.csv' INTO TABLE bmsql_history
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'
(hist_id, h_c_id, h_c_d_id, h_c_w_id, h_d_id, h_w_id, h_date, h_amount, h_data);

LOAD DATA INFILE '/tmp/csv/order.csv' INTO TABLE bmsql_oorder
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'
(o_id, o_w_id, o_d_id, o_c_id, @var_o_carrier_id, o_ol_cnt, o_all_local, o_entry_d)
SET o_carrier_id = NULLIF(@var_o_carrier_id, 'NULL');

LOAD DATA INFILE '/tmp/csv/order-line.csv' INTO TABLE bmsql_order_line
FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'
(ol_w_id, ol_d_id, ol_o_id, ol_number, ol_i_id, @var_ol_delivery_d,
ol_amount, ol_supply_w_id, ol_quantity, ol_dist_info)
SET ol_delivery_d = NULLIF(@var_ol_delivery_d, 'NULL');
```

在run目录下执行以下语句导入数据：

```
./runSQL.sh ./props.my ./sql.mysql/tableCopies.sql
```

若server的cpu核心数较多（如公司测试用的dell服务器），也可手工登陆server创建多个session窗口（注意执行load前需要先设置parallel load的参数），每个session窗口执行部分上述load data语句，增大并行度。



### 7.5 创建索引

所有数据导入完毕后执行以下语句创建索引

```
./runSQL.sh ./props.my ./sql.mysql/indexCreates.sql
```
