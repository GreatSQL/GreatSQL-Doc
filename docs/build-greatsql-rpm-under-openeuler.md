# 在openEuler环境下快速编译GreatSQL RPM包

在上一篇中，已经介绍了在[CentOS环境下编译GreatSQL RPM包的过程](https://mp.weixin.qq.com/s/IBliENob9nJ594PuAamL9A)，本文再介绍如何在openEuler环境下快速编译GreatSQL RPM包。

运行环境是docker中的openEuler 22.03 x86_64：
```
$ docker -v
Docker version 20.10.10, build b485636

$ docker run -itd --hostname oe --name oe openeuler/openeuler bash
1d2839ec30c28c7b20bbd6f469964b0b68ddf6485a0c4136b030c14812f8dec3

$ docker exec -it oe bash
```

## 1、准备工作
### 1.1、配置yum源
用默认的yum源即可，无需额外添加。

### 1.2、安装编译所需要的软件包
安装 `rmp-build` 包，它会附带安装其他必要的相关依赖包，并同步安装其他必要的软件包，如cmake、gcc等：
```
[root@oe /]# dnf install -y automake bison bison-devel bzip2 bzip2-devel clang cmake cmake3 diffutils expat-devel file flex \
gcc gcc-c++ gcc-toolset-12-cpp gcc-toolset-12-gcc graphviz jemalloc jemalloc-devel libaio-devel \
libarchive libcurl-devel libevent-devel libffi-devel libicu-devel libssh libtirpc libtirpc-devel \
libtool libxml2-devel libzstd libzstd-devel lz4-devel lz4-static make ncurses-devel ncurses-libs \
net-tools numactl numactl-devel numactl-libs openldap-clients openldap-devel openssl openssl-devel \
pam pam-devel perl perl-Env perl-JSON perl-Memoize perl-Time-HiRes pkg-config psmisc re2-devel \
readline-devel rpcgen rpm-build rpm-build snappy-devel tar time unzip vim wget zlib-devel
```

### 1.3 创建构建RPM包所需的目录

创建相应的目录
```
[root@oe /]# mkdir -p /root/rpmbuild/SOURCES
```

### 1.4 下载GreatSQL源码包
戳此链接 [https://gitee.com/GreatSQL/GreatSQL/releases/tag/GreatSQL-8.0.32-25](https://gitee.com/GreatSQL/GreatSQL/releases/tag/GreatSQL-8.0.32-25)，找到 `greatsql-8.0.32-25.tar.xz` 下载GreatSQL源码包，放在上面创建的 `/root/rpmbuild/SOURCES` 目录下，并解压缩。

### 1.5 下载greatsql.spec文件
戳此链接 [https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/build-gs/greatsql.spec](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/build-gs/greatsql.spec)，下载 `greatsql.spec` 文件，放在上面创建的 `/root/rpmbuild/` 目录下。

### 1.6 下载boost源码包
编译GreatSQL 8.0.32-25版本需要配套的boost版本是1.77，戳此链接下载 [https://boostorg.jfrog.io/artifactory/main/release/1.77.0/source/boost_1_77_0.tar.gz](https://boostorg.jfrog.io/artifactory/main/release/1.77.0/source/boost_1_77_0.tar.gz)，放在上面创建的 `/root/rpmbuild/SOURCES` 目录下。

## 2、开始准备编译GreatSQL RPM包

从GreatSQL源码包中拷贝几个必要的文件
```
[root@oe /]# cd /root/rpmbuild/SOURCES/greatsql-8.0.32-25/build-gs/rpm
[root@oe rpm]# cp filter-*sh mysqld.cnf mysql-5.7-sharedlib-rename.patch mysql.init mysql_config.sh /root/rpmbuild/SOURCES/
```

在gitee上的 `greatsql.spec` 文件我已更新，无需再修改内容，除非你自己有需要调整。

直接开始尝试编译RPM包
```
[root@oe rpm]#  cd /root/rpmbuild
[root@oe rpmbuild]# time rpmbuild --nodebuginfo --define "_smp_mflags -j14" --define 'dist .oe20' --define "_topdir /root/rpmbuild/" -bb ./greatsql.spec > rpmbuild.log 2>&1
```

在已经安装完上述必要的软件包、依赖包之后，正常应该能顺利完成RPM包编译了。

最后，查看编译结果，会有类似下面的日志：
```
[root@oe rpmbuild]# tail rpmbuild.log
Wrote: /root/rpmbuild/RPMS/x86_64/greatsql-test-8.0.32-25.1.x86_64.rpm
Wrote: /root/rpmbuild/RPMS/x86_64/greatsql-debuginfo-8.0.32-25.1.x86_64.rpm
Executing(%clean): /bin/sh -e /var/tmp/rpm-tmp.tQ4Ggn
+ umask 022
+ cd /root/rpmbuild//BUILD
+ cd greatsql-8.0.32-25
+ /usr/bin/rm -rf /root/rpmbuild/BUILDROOT/greatsql-8.0.32-25.1.x86_64
+ RPM_EC=0
++ jobs -p
+ exit 0
```

再看下编译生成的RPM文件包：
```
[root@oe rpmbuild]# du -sch *
43G    BUILD
0    BUILDROOT
64K    greatsql.spec
36M    rpmbuild.log
492M    RPMS
472M    SOURCES
472M    SRPMS
45G    total

[root@oe rpmbuild]# cd /root/rpmbuild/RPMS/x86_64
[root@oe x86_64]# ls -la
total 503312
-rw-r--r-- 1 root root  18774049 Jan  5 07:35 greatsql-client-8.0.32-25.1.oe20.x86_64.rpm
-rw-r--r-- 1 root root   1926953 Jan  5 07:35 greatsql-devel-8.0.32-25.1.oe20.x86_64.rpm
-rw-r--r-- 1 root root   2145445 Jan  5 07:35 greatsql-icu-data-files-8.0.32-25.1.oe20.x86_64.rpm
-rw-r--r-- 1 root root      8173 Jan  5 07:35 greatsql-mysql-config-8.0.32-25.1.oe20.x86_64.rpm
-rw-r--r-- 1 root root   5104617 Jan  5 07:35 greatsql-mysql-router-8.0.32-25.1.oe20.x86_64.rpm
-rw-r--r-- 1 root root  76307101 Jan  5 07:36 greatsql-server-8.0.32-25.1.oe20.x86_64.rpm
-rw-r--r-- 1 root root   1485673 Jan  5 07:35 greatsql-shared-8.0.32-25.1.oe20.x86_64.rpm
-rw-r--r-- 1 root root 409626153 Jan  5 07:38 greatsql-test-8.0.32-25.1.oe20.x86_64.rpm
```

大功告成，其他内容略过，不再赘述。

## 延伸阅读
- [在CentOS环境下编译GreatSQL RPM包](https://mp.weixin.qq.com/s/IBliENob9nJ594PuAamL9A)
- [玩转MySQL 8.0源码编译](https://mp.weixin.qq.com/s/Lrx-YYYWtHHaxLfY_UZ8GQ)
- [将GreatSQL添加到系统systemd服务](https://mp.weixin.qq.com/s/tSA-DrWT13GN45Csq2tQoA)
- [利用GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/gLaLybt46PqXlV4qWFfyng)
- [InnoDB Cluster+GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/1QUt-rK_5L_UnaLClyve1w)
- [在Docker中部署GreatSQL并构建MGR集群](https://mp.weixin.qq.com/s/CfrYEQD54EXD9mLJJPGs-A)

全文完。

Enjoy GreatSQL :)

