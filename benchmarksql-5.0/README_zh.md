# BenchmarkSQL 性能测试

## 快速开始

以 CentOS 8.x 为例，执行下面的操作后即可快速开始：

- 安装 java 环境

```shell
$ yum install -y java-1.8.0-openjdk ant
```

- 配置 Apache-Ant 的环境变量

```shell
$ echo 'export APACH_HOME=/usr/share/doc/ant-1.9.4' >> ~/.bash_profile
$ echo 'export PATH=${ANT_HOME}/bin:$PATH' >> ~/.bash_profile
$ source ~/.bash_profile
```

- 检查 Java 运行环境是否可用

```shell
$ java -version
$ ant -version
```

- 下载 BenchmarkSQL，并将 benchmarksql-5.0 移动到 /usr/local 目录下

```shell
$ cd /opt
$ git clone https://gitee.com/GreatSQL/GreatSQL-Doc.git
$ mv benchmarksql-5.0 /usr/local
```

- 重新编译 benchmarksql-5.0

```shell
$ cd /usr/local/benchmarksql-5.0
$ ant
Buildfile: /usr/local/benchmarksql-5.0/build.xml

init:

compile:
    [javac] Compiling 11 source files to /usr/local/benchmarksql-5.0/build

dist:
      [jar] Building jar: /usr/local/benchmarksql-5.0/dist/BenchmarkSQL-5.0.jar

BUILD SUCCESSFUL
Total time: 0 seconds
```

- 编辑配置文件 run/props.greatsql，配置 GreatSQL 数据库的连接信息，例如数据库地址、端口、用户名和密码等

```shell
$ vim /usr/local/benchmarksql-5.0/run/props.greatsql

db=mysql
driver=com.mysql.jdbc.Driver
conn=jdbc:mysql://localhost:3306/bmsql?allowPublicKeyRetrieval=true&useSSL=false&serverTimezone=GMT&useLocalSessionState=true&maintainTimeStats=false&useUnicode=true&characterEncoding=utf8&allowMultiQueries=true&rewriteBatchedStatements=true&cacheResultSetMetadata=true&metadataCacheSize=1024
user=tpcc
password=tpcc
...
```

- 创建数据库及相应的账号

```sql
greatsql> CREATE DATABASE bmsql;
greatsql> CREATE USER tpcc IDENTIFIED BY 'tpcc';
greatsql> GRANT ALL ON bmsql.* TO tpcc;
greatsql> SHOW GRANTS FOR tpcc;
+--------------------------------------------------+
| Grants for tpcc@%                                |
+--------------------------------------------------+
| GRANT USAGE ON *.* TO `tpcc`@`%`                 |
| GRANT ALL PRIVILEGES ON `bmsql`.* TO `tpcc`@`%`  |
+--------------------------------------------------+
```

- 运行 `run/runDatabaseBuild.sh`，创建测试数据表并填充数据。

```shell
$ cd /usr/local/benchmarksql-5.0/run
$ ./runDatabaseBuild.sh ./props.greatsql
...
# ------------------------------------------------------------
# Loading SQL file ./sql.mysql/tableCreates.sql
# ------------------------------------------------------------
Loading class `com.mysql.jdbc.Driver'. This is deprecated. The new driver class is `com.mysql.cj.jdbc.Driver'. The driver is automatically registered via the SPI and manual loading of the driver class is generally unnecessary.
...
Loading class `com.mysql.jdbc.Driver'. This is deprecated. The new driver class is `com.mysql.cj.jdbc.Driver'. The driver is automatically registered via the SPI and manual loading of the driver class is generally unnecessary.
-- ----
-- Extra commands to run after the tables are created, loaded,
-- indexes built and extra's created.
-- ----
```

- 开始测试

```shell
$ cd /usr/local/benchmarksql-5.0/run
$ ./runBenchmark.sh ./props.greatsql
[main] INFO   jTPCC : Term-00,
...
```

- 清理数据库

```shell
$ cd /usr/local/benchmarksql-5.0/run
$ ./runDatabaseDestroy.sh ./props.greatsql
# ------------------------------------------------------------
# Loading SQL file ./sql.mysql/tableDrops.sql
# ------------------------------------------------------------
Loading class `com.mysql.jdbc.Driver'. This is deprecated. The new driver class is `com.mysql.cj.jdbc.Driver'. The driver is automatically registered via the SPI and manual loading of the driver class is generally unnecessary.
drop table bmsql_config;
drop table bmsql_new_order;
drop table bmsql_order_line;
drop table bmsql_oorder;
drop table bmsql_history;
drop table bmsql_customer;
drop table bmsql_stock;
drop table bmsql_item;
drop table bmsql_district;
drop table bmsql_warehouse;
drop sequence bmsql_hist_id_seq;
```

## 其他
本仓库相比原生 BenchmarkSQL 代码新增了以下几个文件：
- my-greatsql-example.cnf，运行 GreatSQL/MySQL 的 my.cnf 模板
- run/bmsql-run.sh，自动多次执行 BenchmarkSQL 测试脚本
- run/bmsql-taskset.sh，对 BenchmarkSQL 和 GreatSQL 分别绑定不同 CPU，避免相互影响
- run/sql.mysql，适用于 GreatSQL/MySQL 的库表创建 DDL 文件
- lib/mysql/，MySQL Connector/J 8.0.33 连接驱动

## 参考

更详细参考文档链接：[BenchmarkSQL 性能测试](https://greatsql.cn/docs/8.0.32-26/10-optimize/3-5-benchmark-greatsql-vs-mysql-tpcc-report.html)
