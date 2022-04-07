# 关于 GreatSQL
--- 

GreatSQL是由万里数据库维护的MySQL分支，专注于提升MGR可靠性及性能，支持InnoDB并行查询特性，是适用于金融级应用的MySQL分支版本。

GreatSQL可以作为MySQL或Percona Server的可选替代方案，用于线上生产环境。

GreatSQL完全免费并兼容MySQL或Percona Server。


# 下载GreatSQL
---

## GreatSQL 8.0
- [GreatSQL 8.0.25](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-15)

## GreatSQL 5.7
- [GreatSQL 5.7.36](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-5.7.36-39)


# 版本特性
---
GreatSQL除了提升MGR性能及可靠性，还引入InnoDB事务锁优化及并行查询优化等特性，以及众多BUG修复。
选用GreatSQl主要有以下几点优势：

- 提升MGR模式下的大事务并发性能及稳定性
- 改进MGR的GC及流控算法，以及减少每次发送数据量，避免性能抖动
- 在MGR集群AFTER模式下，解决了节点加入集群时容易出错的问题
- 在MGR集群AFTER模式下，强一致性采用多数派原则，以适应网络分区的场景
- 当MGR节点崩溃时，能更快发现节点异常状态，有效减少切主和异常节点的等待时间
- 优化InnoDB事务锁机制，在高并发场景中有效提升事务并发性能至少10%以上
- 实现InnoDB并行查询机制，极大提升聚合查询效率，TPC-H测试中，最高可提升40多倍，平均提升15倍。特别适用于周期性数据汇总报表之类的SAP、财务统计等业务
- 修复了MGR模式下可能导致数据丢失、性能抖动、节点加入恢复极慢等多个缺陷或BUG

# 注意事项
---
运行GreatSQL可能需要依赖jemalloc库（推荐5.2.1+版本），因此请先先安装上
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
jemalloc下载地址：https://centos.pkgs.org/8/epel-x86_64/jemalloc-5.2.1-2.el8.x86_64.rpm.html

# my.cnf参考

- [my.cnf for GreatSQL 8.0.25](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example)
- [my.cnf for GreatSQL 5.7.36](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example-greatsql-5.7.36)

就可以正常启动GreatSQL服务了。


# 版本历史
---
## GreatSQL 8.0
- [GreatSQL 更新说明 8.0.25(2021-8-26)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-20210820.md)

## GreatSQL 5.7
- [GreatSQL 更新说明 5.7.36(2022-4-7)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-5-7-36-20220407.md)


# 使用文档
---
- [GreatSQL MGR FAQ](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/GreatSQL-FAQ.md)
- [在Linux下源码编译安装GreatSQL](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/build-greatsql-with-source.md)
- [利用Ansible安装GreatSQL并构建MGR集群](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/install-greatsql-with-ansible.md)
- [在Docker中部署GreatSQL并构建MGR集群](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/install-greatsql-with-docker.md)
- [MGR优化配置参考](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/mgr-best-options-ref.md)
- [InnoDB并行查询优化参考](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/innodb-parallel-execute.md)
- [利用GreatSQL部署MGR集群](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/using-greatsql-to-build-mgr-and-node-manage.md)
- [MySQL InnoDB Cluster+GreatSQL部署MGR集群](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/mysql-innodb-cluster-with-greatsql.md)
- [利用systemd管理MySQL单机多实例](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/build-multi-instance-with-systemd.md)

# 专栏文章
- [深入浅出MGR专栏文章](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr)，深入浅出MGR相关知识点、运维管理实操，配合「实战MGR」视频内容食用更佳。

# 相关资源
- [GreatSQL-Docker](https://gitee.com/GreatSQL/GreatSQL-Docker)，在Docker中运行GreatSQL。
- [GreatSQL-Ansible](https://gitee.com/GreatSQL/GreatSQL-Ansible)，利用ansible一键安装GreatSQL并完成MGR集群部署。

# 问题反馈
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


# 联系我们
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
