# 关于 GreatSQL
--- 

GreatSQL开源数据库专注于提升MGR可靠性及性能，支持InnoDB并行查询等特性，是适用于金融级应用的国内自主MySQL版本；可以作为MySQL或Percona Server的可选替换，用于线上生产环境；且完全免费并兼容MySQL或Percona Server。

# 下载GreatSQL
---

## GreatSQL 8.0
- [GreatSQL 8.0.25-16](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-16)
- [GreatSQL 8.0.25-15](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-15)

## GreatSQL 5.7
- [GreatSQL 5.7.36](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-5.7.36-39)


# 版本特性
---
GreatSQL除了提升MGR性能及可靠性，还引入InnoDB事务锁优化及并行查询优化等特性，以及众多BUG修复。
选用GreatSQl主要有以下几点优势：

- 专注于提升MGR可靠性及性能，支持InnoDB并行查询特性
- 是适用于金融级应用的MySQL分支版本
- 地理标签，提升多机房架构数据可靠性
- 仲裁节点，用更低的服务器成本实现更高可用
- 单主模式下更快，选主机制更完善
- InnoDB表也支持并行查询，让CPU资源不再浪费
- 全新流控机制，让MGR运行更流畅不频繁抖动
- 相对官方社区版，MGR运行更稳定、可靠
- 其他...

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

# 安装GreatSQL
推荐安装GreatSQL RPM包。
[戳此链接下载GreatSQL RPM包](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-16)。

执行下面的命令安装GreatSQL：
```
#首先，查找GreatSQL是否已安装
$ yum search greatsql
...
No matches found.

#然后安装
$ rpm -ivh greatsql-client-8.0.25-16.1.el8.x86_64.rpm greatsql-devel-8.0.25-16.1.el8.x86_64.rpm greatsql-mysql-router-8.0.25-16.1.el8.x86_64.rpm greatsql-server-8.0.25-16.1.el8.x86_64.rpm greatsql-shared-8.0.25-16.1.el8.x86_64.rpm
```

安装完成后，GreatSQL会自行完成初始化，可以再检查是否已加入系统服务或已启动：
```
$ systemctl status mysqld
● mysqld.service - MySQL Server
   Loaded: loaded (/usr/lib/systemd/system/mysqld.service; enabled; vendor preset: disabled)
...
     Docs: man:mysqld(8)
           http://dev.mysql.com/doc/refman/en/using-systemd.html
  Process: 1137698 ExecStartPre=/usr/bin/mysqld_pre_systemd (code=exited, status=0/SUCCESS)
 Main PID: 1137732 (mysqld)
   Status: "Server is operational"
    Tasks: 39 (limit: 149064)
   Memory: 336.7M
   CGroup: /system.slice/mysqld.service
           └─1137732 /usr/sbin/mysqld
...
```

# my.cnf参考

- [my.cnf for GreatSQL 8.0.25-16](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example-greatsql-8.0.25-16)
- [my.cnf for GreatSQL 8.0.25-15](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example-greatsql-8.0.25-15)
- [my.cnf for GreatSQL 5.7.36](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example-greatsql-5.7.36)

就可以正常启动GreatSQL服务了。


# 版本历史
---
## GreatSQL 8.0
- [GreatSQL 更新说明 8.0.25-16(2022-5-16)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-16-20220516.md)
- [GreatSQL 更新说明 8.0.25-15(2021-8-26)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-20210820.md)

## GreatSQL 5.7
- [GreatSQL 更新说明 5.7.36(2022-4-7)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-5-7-36-20220407.md)


# 使用文档
---
- [GreatSQL MGR FAQ](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/GreatSQL-FAQ.md)
- [在Linux下源码编译安装GreatSQL](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/build-greatsql-with-source.md)
- [ansible一键安装GreatSQL 8.0.25并构建MGR集群](https://gitee.com/GreatSQL/GreatSQL-Ansible/wikis/ansible%E4%B8%80%E9%94%AE%E5%AE%89%E8%A3%85GreatSQL%208.0.25%E5%B9%B6%E6%9E%84%E5%BB%BAMGR%E9%9B%86%E7%BE%A4)
- [在Docker中部署GreatSQL并构建MGR集群](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/install-greatsql-with-docker.md)
- [MGR优化配置参考](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/mgr-best-options-ref.md)
- [InnoDB并行查询优化参考](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/innodb-parallel-execute.md)
- [利用GreatSQL部署MGR集群](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/using-greatsql-to-build-mgr-and-node-manage.md)
- [MySQL InnoDB Cluster+GreatSQL部署MGR集群](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/mysql-innodb-cluster-with-greatsql.md)
- [利用systemd管理MySQL单机多实例](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/build-multi-instance-with-systemd.md)
- [麒麟OS+龙芯环境编译GreatSQL](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/build-greatsql-with-source-under-kylin-and-loongson.md)

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
