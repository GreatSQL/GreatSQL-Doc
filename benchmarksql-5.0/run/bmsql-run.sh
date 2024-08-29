#!/bin/sh

db=greatsql
basedir=/usr/local/benchmarksql-5.0/run

for ibp in 128 256
do
echo "set ibp=${ibp}g"
mysql -e "set global innodb_buffer_pool_size = ${ibp}*1024*1024*1024;"
mysqladmin var|grep innodb_buffer_pool_size
sleep 30
for i in $(seq 1 8)
do
 logdir=${basedir}/bmsql-${db}/${ibp}g
 resdir=./bmsql-${db}/${ibp}g
 logfile=${db}-ibp${ibp}g-$i.log
 mkdir -p ${resdir}
 resdir=./bmsql-${db}/${ibp}g/res_`date +'%Y%m%d'`_${i}

 sed -i "/resultDirectory.*/d" ./props.${db}
 echo "resultDirectory=${resdir}" >> ./props.${db}

 echo "seq:${db}, ${i}"
 # 一般没必要每次重新初始化整个数据库，否则太慢了
 #echo "./runDatabaseBuild.sh ./props.${db} > ${logdir}/${logfile}"
 #./runDatabaseBuild.sh ./props.${db} > /dev/null 2>&1
 #sleep 120
 #echo
 #echo

 sleep 120
 echo "./runBenchmark.sh ./props.${db} >> ${logdir}/${logfile}"
 ./runBenchmark.sh ./props.${db} >> ${logdir}/${logfile} 2>&1
 echo
 echo

 # 一般没必要每次清空整个数据库
 #echo "./runDatabaseDestroy.sh ./props.${db} >> ${logdir}/${logfile}"
 #./runDatabaseDestroy.sh ./props.${db} > /dev/null 2>&1
 echo
 echo
done
done
