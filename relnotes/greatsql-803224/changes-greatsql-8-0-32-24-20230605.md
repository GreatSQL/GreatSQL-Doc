# Changes in GreatSQL 8.0.32-24 (2023-6-5)

[toc]

> GreatSQL 8.0.32-24版本发布，增加并行load data、（逻辑 & CLONE）备份加密、MGR读写节点可绑定动态VIP、Oracle兼容扩展、审计日志增强等重磅特性。

## 1.新增特性
### 1.1 SQL兼容性
在GreatSQL 8.0.32-24中，实现了多项SQL兼容性功能，包括数据类型扩展、SQL语法等超过20个兼容特性。

#### 1.1.1 数据类型扩展
- CLOB
- VARCHAR2

#### 1.1.2 SQL语法
- [DATETIME 运算](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-syntax-datetime-arithmetic.md)
- [ROWNUM](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-syntax-rownum.md)
- [子查询无别名](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-syntax-subquery-without-alias.md)
- [EXPLAIN PLAN FOR](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-syntax-explain-plan-for.md)

#### 1.1.3 函数
- [ADD_MONTHS()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-addmonths.md)
- [CAST()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-cast.md)
- [DECODE()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-decode.md)
- [INSTR()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-instr.md)
- [LENGTH()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-length.md)
- [LENGTHB()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-lengthb.md)
- [MONTHS_BETWEEN()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-monthsbetween.md)
- [NVL()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-nvl.md)
- [SUBSTRB()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-substrb.md)
- [SYSDATE()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-sysdate.md)
- [TO_CHAR()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-tochar.md)
- [TO_DATE()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-todate.md)
- [TO_NUMBER()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-tonumber.md)
- [TO_TIMESTAMP()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-totimestamp.md)
- [TRANSLATE()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-translate.md)
- [TRUNC()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-trunc.md)
- [SYS_GUID()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-sysguid.md)


更多信息详见文档：[GreatSQL中的SQL兼容性](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat.md)。

### 1.2 MGR

#### 1.2.1 MGR内置动态VIP
在GreatSQL 8.0.32-24中，新增MGR读写节点支持绑定VIP（虚拟IP）特性。利用该特性，使得MGR在单主模式下运行时，能自动识别读写节点并绑定VIP，支持应用端即可通过VIP对数据库发起读写请求，当读写节点角色发生变化时，VIP也会随之自动漂移并重新绑定，应用端无需修改VIP配置。

更多信息详见文档：[GreatSQL中MGR支持内置vip特性](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/mgr-vip.md)。

#### 1.2.2 新增applier queue批处理机制
新增相应选项 `group_replication_applier_batch_size_threshold`。当MGR中的并发事务太大，或者个别Secondary节点（磁盘I/O）性能较差时，可能会导致applier queue堆积越来越大，一直无法及时跟上Primary节点。

这时候有效的办法就是让applier queue落地时采用批量的方式，提高落盘效率。默认地，applier queue里的event是逐个落盘的，这种方式效率很低。当applier queue超过 `group_replication_applier_batch_size_threshold` 设定的阈值时，就会触发批量落盘模式，每100个event批量落盘，就能大大提高落盘效率。

在生产环境中，选项 `group_replication_applier_batch_size_threshold` 值不要设置太小，建议不低于10000。默认值 5000000，最小值10（仅用于开发、测试环境），最大值100000000（基本上等于禁用）。一个大事务会包含很多个event，当该选项设置太低时，可能会导致一个事务中的event没办法及时落盘，会造成relay log不完整，节点crash时，就需要从Primary节点重新读取binlog进行恢复。

| System Variable Name    | group_replication_applier_batch_size_threshold |
| --- | --- | 
| Variable Scope    | Global |
| Dynamic Variable    | YES |
| Permitted Values |    [10 ~ 100000000] |
| Default    | 5000000 |
| Description    |当applier queue超过 `group_replication_applier_batch_size_threshold` 设定的阈值时，就会触发批量落盘模式，每100个event批量落盘，提高落盘效率。|

#### 1.2.3 Xcom cache分配静态化
在MySQL 5.7里，Xcom cache size最大值1G，且不可动态调整。从MySQL 8.0开始，可对其动态调整。在 <= MySQL 8.0.20的版本中，最小值1G。在>= MySQL 8.0.21的版本中，最小值128M。

在MySQL中，是动态按需分配Xcom cache的，如果太多有空闲，就释放；如果不够用，再动态分配更多内存，一次分配大概250000个cache item，很容易造成约150ms的响应延迟。也就是说，会随着事务多少的变化而可能频繁产生响应延迟。

在GreatSQL中，对Xcom cache采用了静态化分配机制，即一开始就预分配约1GB内存用于xcom cache，这可以避免前面提到的响应延迟抖动风险，不过“副作用”是mysqld进程所占用的内存会比原来多，在内存特别紧张的服务器上不太适合。

新增相应选项 `group_replication_xcom_cache_mode` 用于设置Xcom cache静态化初始大小：

| System Variable Name    | group_replication_xcom_cache_mode |
| --- | --- | 
| Variable Scope    | Global |
| Dynamic Variable    | YES |
| Permitted Values |    [0 ~ 4|
| Default    | 2 |
| Description    |设置Xcom cache静态化初始大小，对应关系如下：<br/>0：约能缓存50万个Xcom条目，相应内存消耗约200MB；<br/>1：约能缓存100万个Xcom条目，相应内存消耗约500MB；<br/>2：约能缓存200万个Xcom条目，相应内存消耗约1GB；<br/>3：约能缓存400万个Xcom条目，相应内存消耗约2GB；<br/>4：约能缓存800万个Xcom条目，相应内存消耗约4GB；|

#### 1.2.4 其他优化
- 优化了孟子算法，使得无论是单主模式还是多主模式下，均有不同程度的性能提升。
- 消除了杀节点进程场景下的性能抖动。
- 优化了加入节点时可能导致性能剧烈抖动的问题。
- 优化手工选主机制，解决了长事务造成无法选主的问题。
- 完善MGR中的外键约束机制，降低或避免从节点报错退出MGR的风险。
- 提升了Secondary节点上大事务并发应用回放的速度。
- 增加xcom cache条目，提升了在网络延迟较大或事务应用较慢场景下的性能。
- 新增参数选项：`group_replication_broadcast_gtid_executed_period` 用于设置节点之间各自广播节点的gtid值的频率，单位为毫秒，默认为1000，最小200，最大60 000，配合新的事务认证队列清理算法，进行认证数据库的清理操作。收到所有节点的gtid后，就可以清理都执行完毕的gtid的认证信息了。
- 新增参数选项：`group_replication_flow_control_max_wait_time`，用于设置每次触发流控时，流控等待的最大时长，默认为3600s，最大为86400s（1天）。

### 1.3 性能优化

#### 1.3.1 并行load data
MySQL原生的load data采用单线程读取本地文件（或收取client传来的网络数据包），逐行获取内容后再插入数据。

当导入的单个文件很大时，单线程处理模式无法充分利用数据库的资源，导致执行时间很长。又由于load data导入的数据在一个事务内，当binlog事务超过2G时，可能会导致无法使用binlog在MGR集群间同步。

为解决上述两个问题，GreatSQL支持了load data并行导入。开启并行导入后，会自动切分文件成小块（可配置），然后启动多个worker线程（数量可配置）导入文件块。并行导入与engine无关，理论上支持任何存储引擎。

更多信息详见文档：[GreatSQL中的并行load data特性](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/parallel_load_data.md)。

#### 1.3.2 优化器优化
- 优化了执行计划，使得benchmark tpcc测试吞吐量更高，也更加稳定。

### 1.4 安全
#### 1.4.1 mysqldump备份加密
GreatSQL 8.0.32-24支持在mysqldump进行逻辑备份时产生加密备份文件，并且也支持对加密后的备份文件解密导入。

更多信息详见文档：[GreatSQL中的逻辑备份加密特性](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/mysqldump-encrypt.md)。

#### 1.4.2 审计日志入表
GreatSQL支持将审计日志写入数据表中，并且设置审计日志入表规则，以便达到不同的审计需求。

审计内容将包括操作账户、客户端ip、被操作的数据库对象、操作的完整语句、操作结果。

更多信息详见文档：[GreatSQL中的审计日志入表特性](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/audit-log-in-table.md)。

#### 1.4.3 表空间国密加密

在开源MySQL原有keyring架构，通过国密算法，增强开源MySQL keyring架构的安全性。 MySQL的表空间加密keyring架构包含2层加密，master key 和 tablespace key。master key用于加密tablespace key，加密后的结果存储在tablespace的header中。tablespace key用于加密数据，当用户想访问加密的表时，innoDB会先用master key对之前存储在header中的加密信息进行解密，得到tablespace key。再用tablespace key解密数据信息。tablespace key是不会被改变的，而master key可以随时改变。 开源MySQL的master key采用keyring_file插件，key file直接存储在磁盘上。 本功能点通过基于国密算法sm4，增加了数据库的安全性。

创建国密算法加密表
```
CREATE TABLE test.t1(c1 INT, c2 INT) ENGINE = InnoDB ENCRYPTION = 'Y';
```

更多信息详见文档：[GreatSQL中的表空间加密国密支持](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/innodb-tablespace-encrypt.md)。

#### 1.4.4 CLONE备份加密
GreatSQL支持在利用CLONE备份时同步进行加密操作，提升备份文件安全性，避免备份文件被盗或泄漏时造成损失。

更多信息详见文档：[CLONE备份加密](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/clone-encrypt.md)。

## 2.稳定性提升
## 3.其他调整
## 4.bug修复
## 5. GreatSQL VS MySQL

| 特性 | GreatSQL 8.0.32-24 | MySQL 8.0.32 |
| --- | --- | --- |
| 开源 | ✅| ✅|
|ACID完整性|✅|✅|
|MVCC特性|✅    |✅|
|支持行锁|✅|✅|
|Crash自动修复|✅|✅|
|表分区(Partitioning)|✅|✅|
|视图(Views)    |✅|✅|
|子查询(Subqueries)|✅|✅|
|触发器(Triggers)|✅|✅|
|存储过程(Stored Procedures)|✅|✅|
|外键(Foreign Keys)|✅|✅|
|窗口函数(Window Functions)|✅|✅|
|通用表表达式CTE|✅|✅|
|地理信息(GIS)|✅|✅|
|基于GTID的复制|✅|✅|
|组复制(MGR)|✅|✅|
|MyRocks引擎|✅|❎|
|SQL兼容扩展|1.数据类型扩展<br/>2.SQL语法扩展<br/>共超过20个扩展新特性| ❎ |
|MGR提升|1.地理标签<br/>2.仲裁节点<br/>3.读写节点绑定VIP<br/>4.快速单主模式<br/>5.智能选主机制<br/>6.全新流控算法|❎|
|性能提升|1.InnoDB并行查询<br/>2.并行load data|❎|
|安全提升|1.国密支持<br/>2.备份加密<br/>3.审计日志入库|❎|

此外，GreatSQL 8.0.32-24基于Percona Server for MySQL 8.0.32-24版本，它在MySQL 8.0.32基础上做了大量的改进和提升以及众多新特性，详情请见：[**Percona Server for MySQL feature comparison**](https://docs.percona.com/percona-server/8.0/feature_comparison.html#percona-server-for-mysql-feature-comparison)，这其中包括线程池、审计、数据脱敏等MySQL企业版才有的特性，以及PFS提升、IFS提升、性能和可扩展性提升、用户统计增强、processlist增强、slow log增强等大量改进和提升，这里不一一重复列出。


## 6. GreatSQL Release Notes
- [Changes in MySQL 8.0.25-17 (2023-3-13)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-17-20230313.md)
- [Changes in MySQL 8.0.25-16 (2022-5-16)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-16-20220516.md)
- [Changes in MySQL 8.0.25-15 (2021-8-26)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-20210820.md)
- [Changes in MySQL 5.7.36-39 (2022-4-7)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-5-7-36-20220407.md)
