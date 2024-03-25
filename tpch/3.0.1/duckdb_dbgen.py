#!/usr/bin/python3
#
# 2024.03.25更新
#
# 暂不推荐使用
# 由于duckdb中将几个表的数据类型设置为int32，在构造SF>=357的情况下会出现int值溢出生成负数值问题
# 建议改用本仓库中的 pdbgen.sh 脚本
#
import duckdb
import pathlib
import sys

if sys.argv[1]:
    sf = int(sys.argv[1])
else:
    sf = 1

if sys.argv[2]:
    slice = int(sys.argv[2])
else:
    slice = 1

x = 0
while (x <= slice):
    con=duckdb.connect()
    con.sql('PRAGMA disable_progress_bar;SET preserve_insertion_order=false')
    con.sql(f"CALL dbgen(sf={sf} , children ={slice}, step = {x})")
    for tbl in ['nation','region','customer','supplier','lineitem','orders','partsupp','part'] :
        num=con.query(f"select count(*) from {tbl}").fetchone()[0]
        if num > 0:
            pathlib.Path(f'./tpch_{sf}').mkdir(parents=True, exist_ok=True)
            con.sql(f"COPY (SELECT * FROM {tbl}) TO './tpch_{sf}/{tbl}_{x}.csv' (DELIMITER '|', HEADER false, FORMAT 'csv');")
    print ("slice %d/%d done" % (x, slice))
    x += 1
    con.close()
# 
# 使用说明
#
# 功能：利用duckdb来快速生成TPC-H测试数据
# 致谢：本脚本基于 https://github.com/wubx/databend-workshop/blob/main/databend_tpch/gen_data.py 进行改造
#
# 使用方法：
# 1. 下载安装duckdb
# 下载duckdb二进制压缩包 wget -c https://github.com/duckdb/duckdb/releases/download/v0.10.0/duckdb_cli-linux-amd64.zip
# 解压缩后，直接运行 duckdb 程序即可
# ./duckdb &
# 
# 2. 安装Python duckdb及相关模块
# Python版本要求是3.x及以上
# pip3 install --user duckdb
#
# 3. 生成测试数据
# python3.8 ./duckdb_dbgen.py 1 10
# 第一个参数用于指定TPC-H仓库数，即 SF=n；要求是正整数
# 第二个参数用于指定生成测试数据并发度，即每个表拆分成多少个分片/分区，便于后续并发导入，提升导入速度；要求是正整数
#
# 4. 导入测试数据
# 执行类似下面的SQL导入测试数据
# LOAD DATA INFILE 'path/tpch_1/nation_0.csv' INTO TABLE nation FIELDS TERMINATED BY '|';
#
# GreatSQL支持并行导入，还可以用类似下面的方法
# LOAD /*+ SET_VAR(gdb_parallel_load=ON) SET_VAR(gdb_parallel_load_workers=16)*/ DATA INFILE 'path/tpch_1/nation_0.csv' INTO TABLE nation FIELDS TERMINATED BY '|';
