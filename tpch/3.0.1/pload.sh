#!/bin/bash
#
# 使用说明
#
# 功能：将pdbgen.sh并行构造TPC-H测试数据集文件并行load到数据库中
#
# 使用方法：
# 1. 修改workdir, MYSQL_CLI, maxthd, sleep等相关设定
# 2. 运行脚本
# ./pload.sh > ./pload.log 2>&1
#

workdir=/data/tpch
tpchdb="tpch"
host="172.16.16.10"
port=3306
user="tpch"
passwd="tpch"
MYSQL_CLI="mysql -h$host -P$port -u$user -p"$passwd" -f ${tpchdb}"

cd ${workdir}

#最大并发数，默认设置为可用逻辑CPU数-2，可自行调整
maxthd=`lscpu | grep '^CPU(s)'|awk '{print $NF}'`
maxthd=`expr ${maxthd} - 2`

#当达到最大并发数时轮询等待时长
sleep=1

tbls="region nation supplier customer part partsupp orders lineitem"

for tbl in ${tbls}
do
  #扫描计算各表分片文件数
  fn=`ls ${tbl}.tbl*|wc -l`

  #如果没有多分片文件，直接导入
  if [ ${fn} -eq 1 ] ; then
    f=${tbl}.tbl
    $MYSQL_CLI -f -e "load data /*+ SET_VAR(gdb_parallel_load=ON) SET_VAR(gdb_parallel_load_workers=16)*/ infile '${workdir}/${f}' into table ${tbl} FIELDS TERMINATED BY '|'; " &
    echo "LOAD $f"
  else
    for i in $(seq 1 ${fn})
    do
      f=${tbl}.tbl.${i}

      while [ `mysqladmin pr|wc -l` -gt ${maxthd} ]
      do
        echo "SLEEP ${sleep}, ${f}"
	sleep ${sleep}
      done

      echo "LOAD $i - $f"
      #echo "`head -n 1 ${f}`"
      #echo "`tail -n 1 ${f}`"
      $MYSQL_CLI -f -e "load data /*+ SET_VAR(gdb_parallel_load=ON) SET_VAR(gdb_parallel_load_workers=16)*/ infile '${workdir}/${f}' into table ${tbl} FIELDS TERMINATED BY '|'; " &
   done
 fi
done
