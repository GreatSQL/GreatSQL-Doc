# 在CentOS环境下编译GreatSQL src.rpm包，并再编译RPM包

本文介绍如何在CentOS环境下编译GreatSQL src.rpm源码包，以及如何用src.rpm源码包编译生成可安装的RPM包。

运行环境是docker中的CentOS 8 x86_64：
```
$ docker -v
Docker version 20.10.10, build b485636

$ docker run -itd --hostname c8 --name c8 centos bash
a0a2128591335ef41e6faf46b7e79953c097500e9f033733c3ab37f915b69439

$ docker exec -it c8 bash
```

## 1、准备工作
### 1.1、配置yum源
开始编译之前，需要先配置好yum源，方便安装一些辅助工具。

在这里采用阿里云的yum源：
```
[root@c8 /]# rm -f /etc/yum.repos.d/* && \
curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-vault-8.5.2111.repo && \
sed -i -e '/mirrors.cloud.aliyuncs.com/d' -e '/mirrors.aliyuncs.com/d' /etc/yum.repos.d/CentOS-Base.repo && \
yum clean all && yum makecache
```

### 1.2、安装编译所需要的软件包
安装 rmp-build、cmake、gcc 等编译环境必要的软件包
```
[root@c8 /]# dnf install -y  bison cmake cyrus-sasl-devel gcc-c++ gcc-toolset-11 gcc-toolset-11-annobin-plugin-gcc krb5-devel libaio-devel libcurl-devel libtirpc-devel m4 make ncurses-devel numactl-devel openldap-devel openssl openssl-devel pam-devel perl perl-Carp perl-Data-Dumper perl-Errno perl-Exporter perl-File-Temp perl-Getopt-Long perl-JSON perl-Memoize perl-Time-HiRes readline-devel rpm-build time zlib-devel
```

### 1.3 创建构建RPM包所需的目录

创建相应的目录
```
[root@c8 /]# mkdir -p /root/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
```

### 1.4 下载GreatSQL源码包
戳此链接 [https://gitee.com/GreatSQL/GreatSQL/releases/tag/GreatSQL-8.0.32-25](https://gitee.com/GreatSQL/GreatSQL/releases/tag/GreatSQL-8.0.32-25)，找到 `greatsql-8.0.32-25.tar.xz` 下载GreatSQL源码包，放在上面创建的 `/root/rpmbuild/SOURCES` 目录下，并解压缩。

### 1.5 下载greatsql.spec文件
戳此链接 [https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/build-gs/greatsql.spec](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/build-gs/greatsql.spec)，下载 `greatsql.spec` 文件，放在上面创建的 `/root/rpmbuild/` 目录下。

### 1.6 下载boost源码包
编译GreatSQL 8.0.32-25版本需要配套的boost版本是1.77，戳此链接下载 [https://boostorg.jfrog.io/artifactory/main/release/1.77.0/source/boost_1_77_0.tar.gz](https://boostorg.jfrog.io/artifactory/main/release/1.77.0/source/boost_1_77_0.tar.gz)，放在上面创建的 `/root/rpmbuild/SOURCES` 目录下。

### 1.7 下载rpcsvc-proto包并编译安装
编译GreatSQL需要配套`rpcsvc-proto`包，戳此链接下载 [https://github.com/thkukuk/rpcsvc-proto/releases/download/v1.4/rpcsvc-proto-1.4.tar.gz](https://github.com/thkukuk/rpcsvc-proto/releases/download/v1.4/rpcsvc-proto-1.4.tar.gz)，放在 `/tmp/` 目录下。

然后编译安装`rpcsvc-proto`包：
```
[root@c8 ~]# cd /tmp/
[root@c8 tmp]# tar xf rpcsvc-proto-1.4.tar.gz
[root@c8 tmp]# cd rpcsvc-proto-1.4
[root@c8 rpcsvc-proto-1.4]# ./configure && make && make install
[root@c8 rpcsvc-proto-1.4]# rpcgen --version
rpcgen (rpcsvc-proto) 1.4
```
确认编译安装好`rpcgen`即可。

## 2、开始准备编译GreatSQL src.rpm包

从GreatSQL源码包中拷贝几个必要的文件
```
[root@c8 /]# cd /root/rpmbuild/SOURCES/greatsql-8.0.32-25/build-gs/rpm
[root@c8 rpm]# cp filter-*sh mysqld.cnf mysql-5.7-sharedlib-rename.patch mysql.init mysql_config.sh /root/rpmbuild/SOURCES/
```

检查 `greatsql.spec` 文件中类似下面的几部分内容是否要调整（注意文件名，路径名是否能对应上）：
```
[root@c8 rpm]# vim /root/rpmbuild/greatsql.spec
...
%global greatsql_version 25
%global revision db07cc5cb73
...
SOURCE0:        greatsql-8.0.32-25.tar.xz
...
SOURCE10:       boost_1_77_0.tar.xz
...
BuildRequires:  rpcgen
...
%changelog
* Fri Dec 29 2023 GreatSQL <greatsql@greatdb.com> - 8.0.32-25.1
- Release GreatSQL-8.0.32-25.1
...
```
**注意**：在CentOS等部分系统中，可能无法通过yum/dnf安装rpcgen，则在上述 `greatsql.spec` 文件中，注释掉 `BuildRequires:  rpcgen` 这行内容，但需要确保前面提到的 "**1.7 下载rpcsvc-proto包并编译安装**" 这步工作要先完成。在openEuler系统中，是可以直接通过yum/dnf安装`rpcgen`的。

开始尝试编译 src.rpm 包
```
[root@c8 rpm]#  cd /root/rpmbuild
[root@c8 rpmbuild]# time rpmbuild --nodebuginfo --define "_smp_mflags -j10" --define 'dist .el8' --define "_topdir /root/rpmbuild/" -bs ./greatsql.spec > ./rpmbuild.log 2>&1 && tail rpmbuild.log
...
warning: bogus date in %changelog: Wed Jun  6 2022 GreatSQL <greatsql@greatdb.com> - 8.0.25-16.1


Wrote: /root/rpmbuild/SRPMS/greatsql-8.0.32-25.1.el8.src.rpm
```
可以看到打包过程很顺利，没有报错。

最后打包产生的 src.rpm 源码包是 `/root/rpmbuild/SRPMS/greatsql-8.0.32-25.1.el8.src.rpm`，后面我们就可以拿着这个 src.rpm 源码包在其他同为CentOS 8 x86_64的环境下编译成RPM包了。
```
[root@c8 rpmbuild]# ls -la /root/rpmbuild/SRPMS/greatsql-8.0.32-25.1.el8.src.rpm
-rw-r--r-- 1 root root 494584827 Jan 16 15:01 /root/rpmbuild/SRPMS/greatsql-8.0.32-25.1.el8.src.rpm
```

在本文中，我们仍用当前的环境编译RPM包。因为编译环境所需要的软件包在前面都已经安装过了，接下来只需一条命令即可完成编译：
```
[root@c8 rpmbuild]# time rpmbuild --nodebuginfo --define "_smp_mflags -j10" --define 'dist .el8' --define "_topdir /root/rpmbuild/" --rebuild ./SRPMS/greatsql-8.0.32-25.1.el8.src.rpm > ./rpmbuild.log 2>&1 && tail rpmbuild.log
...
+ umask 022
+ cd /root/rpmbuild//BUILD
+ cd greatsql-8.0.32-25
+ /usr/bin/rm -rf /root/rpmbuild/BUILDROOT/greatsql-8.0.32-25.1.el8.x86_64
+ exit 0
```
可以看到已经顺利完成编译工作。

再看下编译生成的RPM文件包：
```
[root@c8 rpmbuild]# du -sch *
0       BUILD
0       BUILDROOT
64K     greatsql.spec
37M     rpmbuild.log
511M    RPMS
12K     SOURCES
0       SPECS
472M    SRPMS
1019M   total

[root@c8 rpmbuild]# cd /root/rpmbuild/RPMS/x86_64
[root@c8 x86_64]# ls -la
total 998740
drwxr-xr-x 2 root root      4096 Dec 29 10:27 .
drwxr-xr-x 3 root root        20 Dec 29 10:21 ..
-rw-r--r-- 1 root root  19061972 Dec 29 10:22 greatsql-client-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root   2241908 Dec 29 10:24 greatsql-devel-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root   2145368 Dec 29 10:24 greatsql-icu-data-files-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root      8100 Dec 29 10:24 greatsql-mysql-config-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root   5259796 Dec 29 10:24 greatsql-mysql-router-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root  78317640 Dec 29 10:22 greatsql-server-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root   1502984 Dec 29 10:24 greatsql-shared-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root 409911420 Dec 29 10:24 greatsql-test-8.0.32-25.1.el8.x86_64.rpm
```

大功告成，其他内容略过，不再赘述。

## 延伸阅读
- [在CentOS环境下编译GreatSQL RPM包](https://mp.weixin.qq.com/s/IBliENob9nJ594PuAamL9A)
- [在openEuler环境下快速编译GreatSQL RPM包](https://mp.weixin.qq.com/s/rA62l7n18vCJdAvl16EoKQ)
- [玩转MySQL 8.0源码编译](https://mp.weixin.qq.com/s/Lrx-YYYWtHHaxLfY_UZ8GQ)
- [将GreatSQL添加到系统systemd服务](https://mp.weixin.qq.com/s/tSA-DrWT13GN45Csq2tQoA)
- [利用GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/gLaLybt46PqXlV4qWFfyng)
- [InnoDB Cluster+GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/1QUt-rK_5L_UnaLClyve1w)
- [在Docker中部署GreatSQL并构建MGR集群](https://mp.weixin.qq.com/s/CfrYEQD54EXD9mLJJPGs-A)

全文完。

Enjoy GreatSQL :)

