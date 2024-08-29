#!/bin/sh
#
# 对 BenchmarkSQL 和 GreatSQL 分别绑定CPU
# 假定总共 176 Cores，BenchmarkSQL 并发 64 客户端为例
#
export PATH=$PATH:/usr/local/GreatSQL-8.0.32-26-Linux-glibc2.17-x86_64/bin/
ps -ef|grep -v grep|grep java
bmsql_pid=`ps -ef|grep -v grep|grep java|awk '{print $2}'`
taskset -pc 111-175 ${bmsql_pid} && taskset -pc ${bmsql_pid}

ps -ef|grep -v grep|grep mysqld
mysqld_pid=`ps -ef|grep -v grep|grep mysqld|awk '{print $2}'`
taskset -pc 0-110 ${mysqld_pid} && taskset -pc ${mysqld_pid}
