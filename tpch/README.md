# tpch

适用于GreatSQL AP引擎的TPC-H测试套件。

试用版本：TPC-H 3.0.1。

相关文件介绍：
- load-data-parallel.sh，用于执行并行LOAD DATA加载TPC-H测试数据到GreatSQL中的脚本。MySQL、Percona及其他分支不支持并行LOAD DATA特性，但也可以使用该脚本，不会产生报错。
- queries，该目录下包含了22个TPC-H测试的SQL脚本，已经都默认加上适用于GreatSQL AP引擎的HINT语法。
- run-tpch.sh，实现自动化运行TPC-H测试SQL语句的脚本。
- tpch-create-table.sql，适用于GreatSQL AP引擎的建表DDL脚本。
- greatsql-ap-test.sql，适用于GreatSQL AP引擎的测试脚本，可以在完成GreatSQL初始化后运行，测试验证对AP引擎的支持结果。

自动化测试脚本 `run-tpch.sh` 的工作方式大致如下：

1. 每条SQL共运行5次，前2次为预热作用，只会记录后3次的运行时间，结果类似下面这样：
```
[2024-01-03 07:51:41] BEGIN RUN TPC-H Q1 3 times
[2024-01-03 07:51:42] TPC-H Q1 END, COST: 1.374s


[2024-01-03 07:51:42] BEGIN RUN TPC-H Q1 4 times
[2024-01-03 07:51:43] TPC-H Q1 END, COST: 1.267s


[2024-01-03 07:51:43] BEGIN RUN TPC-H Q1 5 times
[2024-01-03 07:51:44] TPC-H Q1 END, COST: 1.228s
```
即同一条SQL语句共运行5次，只记录最后3次的耗时。

2. 每次运行SQL语句结束后都会休眠N秒钟，默认为5秒钟，可自定义参数 `sleeptime` 进行调整。

3. 可自定义运行时产生的log文件目录，调整参数 `logdir` 即可。

4. 每条SQL运行耗时结果记录在文件 `${logdir}/run-tpch-queries.log` 中。

5. 每条SQL运行返回的结果记录在文件 `./${logdir}/tpch_queries_$i.res` 中。

6. 要自行修改适用于自己环境的参数，包括 `workdir`、`tpchdb`、`host`、`port`、`user`、`passwd`等。

7. 最后可以用下面的命令获取测试结果：
```
$ cat run-tpch-queries.log | grep COST| awk '{if(NR%3==0){print $7"\n"}else{print $7}}'|sed 's/s//ig'
...
1.378
1.160
1.002

0.229
0.251
0.237
...
```
相邻的3条记录，表示每条SQL最后3次的执行耗时。
