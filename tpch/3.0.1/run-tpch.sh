#!/bin/bash
workdir=/data/tpch
tpchdb="tpch"
host="172.16.16.10"
port="3306"
user="tpch"
passwd="tpch"
logdir="log"

cd ${workdir}
mkdir -p ${logdir}
MYSQL_CLI="mysql -h"${host}" -P"${port}" -u"${user}" -p"${passwd}" -f ${tpchdb}"

# 第一遍执行，先预热数据
for i in $(seq 1 22)
do
 $MYSQL_CLI < ./queries/tpch_queries_$i.sql > /dev/null 2>&1
 echo "tpch_queries_$i.sql warmup ended"
done
sleep 30
echo "sleeping for 30 seconds"

# 正式测试，每个查询SQL执行3遍
for i in $(seq 1 22)
do
 for j in $(seq 1 3)
 do

   time_1=`date +%s%N`
	 echo `date  '+[%Y-%m-%d %H:%M:%S]'` "BEGIN RUN TPC-H Q${i} ${j} times" >> ./${logdir}/run-tpch-queries.log 2>&1

	 echo "RUN TPC-H Q${i} ${j} times"
	 $MYSQL_CLI < ./queries/tpch_queries_$i.sql >> ./${logdir}/tpch_queries_$i.res 2>&1

	 time_2=`date +%s%N`
	 durtime=`echo $time_2 $time_1 | awk '{printf "%0.3f\n", ($1 - $2) / 1000000000}'`
	 echo `date  '+[%Y-%m-%d %H:%M:%S]'` "TPC-H Q${i} END, COST: ${durtime}s" >> ./${logdir}/run-tpch-queries.log 2>&1
	 echo "" >> ./${logdir}/run-tpch-queries.log 2>&1
	 echo "" >> ./${logdir}/run-tpch-queries.log 2>&1
 done
done