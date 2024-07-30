#!/bin/bash
workdir=/data/tpch
tpchdb="tpch"
host="172.16.16.10"
port="3306"
user="tpch"
passwd="tpch"
logdir="tpch-runlog-`date +%Y%m%d`"
sleeptime=5

cd ${workdir}
mkdir -p ${logdir}
MYSQL_CLI="mysql -h"${host}" -P"${port}" -u"${user}" -p"${passwd}" -f ${tpchdb}"

# 每个查询SQL执行5遍，其中前2遍是预热
for i in $(seq 1 22)
do
 for j in $(seq 1 5)
 do
   if [ ${j} -le 2 ] ; then
     time_1=`date +%s%N`

     $MYSQL_CLI < ./queries/tpch_queries_$i.sql > /dev/null 2>&1

     time_2=`date +%s%N`
     durtime=`echo $time_2 $time_1 | awk '{printf "%0.3f\n", ($1 - $2) / 1000000000}'`

     echo "tpch_queries_$i.sql warmup ${j} times END, COST: ${durtime}s"
   else
     time_1=`date +%s%N`
     echo `date  '+[%Y-%m-%d %H:%M:%S]'` "BEGIN RUN TPC-H Q${i} ${j} times" >> ./${logdir}/run-tpch-queries.log 2>&1

     $MYSQL_CLI < ./queries/tpch_queries_$i.sql >> ./${logdir}/tpch_queries_${i}_${j}.res 2>&1

     time_2=`date +%s%N`
     durtime=`echo $time_2 $time_1 | awk '{printf "%0.3f\n", ($1 - $2) / 1000000000}'`
     echo `date  '+[%Y-%m-%d %H:%M:%S]'` "TPC-H Q${i} END, COST: ${durtime}s" >> ./${logdir}/run-tpch-queries.log 2>&1
     echo "RUN TPC-H Q${i} ${j} times END, COST: ${durtime}s"
     echo "" >> ./${logdir}/run-tpch-queries.log 2>&1
     echo "" >> ./${logdir}/run-tpch-queries.log 2>&1
   fi

   echo "sleeping for ${sleeptime} seconds"
   sleep ${sleeptime}
 done
done
