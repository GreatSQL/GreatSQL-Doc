# GreatSQL 更新说明 8.0.22(2021-4-1)
---

### 1.稳定性提升
- 提升大事务稳定性
- 优化MGR队列garbage collect机制、改进流控算法，以及减少每次发送数据量，避免性能抖动
- 解决了AFTER模式下，存在节点加入集群时容易出错的问题
- 在AFTER模式下，强一致性采用多数派原则，以适应网络分区的场景
- 当MGR节点崩溃时，能更快发现节点异常状态，有效减少切主和异常节点的等待时间
- 优化MGR DEBUG日志输出格式

### 2.bug修复
- 修复了节点异常时导致MGR大范围性能抖动问题
- 修复了传输大数据可能导致逻辑判断死循环问题
- 修复了启动过程中低效等待问题
- 修复了磁盘满导致吞吐量异常问题
- 修复了多写模式下可能丢数据的问题/单主模式下切主丢数据的问题
- 修复了TCP self-connect问题

### 5.使用注意事项
- 选项```slave_parallel_workers```建议设置为逻辑CPU数的2倍，提高从库回放时的并发效率
- 在MGR节点正式拉起之前，务必设置```super_read_only=ON```（或者确保此时不会有人修改数据）
- 选项```group_replication_unreachable_majority_timeout```建议不要设置，否则网络分区的时候，给用户返回错误，但其它分区多数派已经提交了事务
- 出于问题诊断需要，建议设置```log_error_verbosity=3```
- 运行GreatSQL需要依赖jemalloc库，因此请先先安装上
```
yum -y install jemalloc jemalloc-devel
```
也可以把自行安装的lib库so文件路径加到系统配置文件中，例如：
```
[root@greatdb]# cat /etc/ld.so.conf
/usr/local/lib64/
```
而后执行下面的操作加载libjemalloc库，并确认是否已存在
```
[root@greatdb]# ldconfig

[root@greatdb]# ldconfig -p | grep libjemalloc
        libjemalloc.so.1 (libc6,x86-64) => /usr/local/lib64/libjemalloc.so.1
        libjemalloc.so (libc6,x86-64) => /usr/local/lib64/libjemalloc.so
```
就可以正常启动GreatSQL服务了。
