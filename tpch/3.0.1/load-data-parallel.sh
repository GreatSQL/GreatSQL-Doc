#!/bin/bash
workdir=/data/tpch
tpchdb="tpch"
host="172.16.16.10"
port="3306"
user="tpch"
passwd="tpch"

cd ${workdir}
MYSQL_CLI="mysql -h$host -P$port -u$user -p'$passwd' -f ${tpchdb}"

# 利用GreatSQL的parallel load data特性并行导入TPC-H测试数据
# 需要先修改GreatSQL选项`secure_file_priv`设置，指向上述 workdir 所在目录，重启GreatSQL使之生效
# 可通过修改下面SQL命令中的参数`gdb_parallel_load_workers=16`调整导入的并发线程数

$MYSQL_CLI -f -e "load /*+ SET_VAR(gdb_parallel_load=ON) SET_VAR(gdb_parallel_load_workers=16)*/ data infile '${workdir}/region.tbl' into table region FIELDS TERMINATED BY '|'; " ${tpchdb} &
$MYSQL_CLI -f -e "load /*+ SET_VAR(gdb_parallel_load=ON) SET_VAR(gdb_parallel_load_workers=16)*/ data infile '${workdir}/nation.tbl' into table nation FIELDS TERMINATED BY '|'; " ${tpchdb} &
$MYSQL_CLI -f -e "load /*+ SET_VAR(gdb_parallel_load=ON) SET_VAR(gdb_parallel_load_workers=16)*/ data infile '${workdir}/supplier.tbl' into table supplier FIELDS TERMINATED BY '|'; " ${tpchdb} &
$MYSQL_CLI -f -e "load /*+ SET_VAR(gdb_parallel_load=ON) SET_VAR(gdb_parallel_load_workers=16)*/ data infile '${workdir}/part.tbl' into table part FIELDS TERMINATED BY '|'; " ${tpchdb} &
$MYSQL_CLI -f -e "load /*+ SET_VAR(gdb_parallel_load=ON) SET_VAR(gdb_parallel_load_workers=16)*/ data infile '${workdir}/customer.tbl' into table customer FIELDS TERMINATED BY '|'; " ${tpchdb} &
$MYSQL_CLI -f -e "load /*+ SET_VAR(gdb_parallel_load=ON) SET_VAR(gdb_parallel_load_workers=16)*/ data infile '${workdir}/partsupp.tbl' into table partsupp FIELDS TERMINATED BY '|'; " ${tpchdb} &
$MYSQL_CLI -f -e "load /*+ SET_VAR(gdb_parallel_load=ON) SET_VAR(gdb_parallel_load_workers=16)*/ data infile '${workdir}/orders.tbl' into table orders FIELDS TERMINATED BY '|'; " ${tpchdb} &
$MYSQL_CLI -f -e "load /*+ SET_VAR(gdb_parallel_load=ON) SET_VAR(gdb_parallel_load_workers=16)*/ data infile '${workdir}/lineitem.tbl' into table lineitem FIELDS TERMINATED BY '|'; " ${tpchdb} &
