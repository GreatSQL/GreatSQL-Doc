# 在CentOS环境下编译GreatSQL RPM包

本文介绍如何在CentOS环境下编译GreatSQL RPM包。

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
安装 `rmp-build` 包，它会附带安装其他必要的相关依赖包：
```
[root@c8 /]# dnf install -y rpm-build
```

### 1.3 创建构建RPM包所需的目录

创建相应的目录
```
[root@c8 /]# mkdir -p /root/rpmbuild/SOURCES
```

### 1.4 下载GreatSQL源码包
戳此链接 [https://gitee.com/GreatSQL/GreatSQL/releases/tag/GreatSQL-8.0.32-25](https://gitee.com/GreatSQL/GreatSQL/releases/tag/GreatSQL-8.0.32-25)，找到 `greatsql-8.0.32-25.tar.xz` 下载GreatSQL源码包，放在上面创建的 `/root/rpmbuild/SOURCES` 目录下，并解压缩。

### 1.5 下载greatsql.spec文件
戳此链接 [https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/build-gs/greatsql.spec](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/build-gs/greatsql.spec)，下载 `greatsql.spec` 文件，放在上面创建的 `/root/rpmbuild/` 目录下。

### 1.6 下载boost源码包
编译GreatSQL 8.0.32-25版本需要配套的boost版本是1.77，戳此链接下载 [https://boostorg.jfrog.io/artifactory/main/release/1.77.0/source/boost_1_77_0.tar.gz](https://boostorg.jfrog.io/artifactory/main/release/1.77.0/source/boost_1_77_0.tar.gz)，放在上面创建的 `/root/rpmbuild/SOURCES` 目录下。

### 1.7 下载rpcsvc-proto包并编译安装
编译GreatSQL需要配套`rpcsvc-proto`包，戳此链接下载 [https://github.com/thkukuk/rpcsvc-proto/releases/download/v1.4/rpcsvc-proto-1.4.tar.gz](https://github.com/thkukuk/rpcsvc-proto/releases/download/v1.4/rpcsvc-proto-1.4.tar.gz)，放在 `/tmp/` 目录下。


## 2、开始准备编译GreatSQL RPM包

从GreatSQL源码包中拷贝几个必要的文件
```
[root@c8 /]# cd /root/rpmbuild/SOURCES/greatsql-8.0.32-25/build-gs/rpm
[root@c8 rpm]# cp filter-*sh mysqld.cnf mysql-5.7-sharedlib-rename.patch mysql.init mysql_config.sh /root/rpmbuild/SOURCES/
```

修改 `greatsql.spec` 文件中的部分内容：
```
[root@c8 rpm]# vim /root/rpmbuild/greatsql.spec
...
%global greatsql_version 25
%global revision db07cc5cb73
...
SOURCE0:        greatsql-8.0.32-25.tar.xz
...
SOURCE10:       boost_1_77_0.tar.gz
...
%changelog
* Fri Dec 29 2023 GreatSQL <greatsql@greatdb.com> - 8.0.32-25.1
- Release GreatSQL-8.0.32-25.1

* Wed Jun  7 2023 GreatSQL <greatsql@greatdb.com> - 8.0.32-24.1
- Release GreatSQL-8.0.32-24.1
...
```

开始尝试编译RPM包
```
[root@c8 rpm]#  cd /root/rpmbuild
[root@c8 rpmbuild]# rpmbuild --nodebuginfo --define "_smp_mflags -j14" --define 'dist .el8' --define "_topdir /root/rpmbuild/" -bb ./greatsql.spec
```

在使用 `rpmbuild` 编译RPM包时，通常会选择加上 `-ba` 或 `-bb` 参数，下面是关于这两个参数的注释：
```
-ba    Build binary and source packages (after doing the %prep, %build, and %install stages).

-bb    Build a binary package (after doing the %prep, %build, and %install stages).
```
简单说，`-ba` 会编译出RPM包和SRPM包，而 `-bb` 只会编译出RPM包。

第一次运行时，大概率会提示N多依赖包缺失，先耐心地逐个安装上：
```
[root@c8 rpmbuild]# rpmbuild --nodebuginfo --define "_smp_mflags -j14" --define 'dist .el8' --define "_topdir /root/rpmbuild/" -bb ./greatsql.spec
...
warning: Macro expanded in comment on line 787: %{_mandir}/man1/mysql.server.1*

warning: Macro expanded in comment on line 956: %{_datadir}/mysql-*/audit_log_filter_linux_install.sql
...
warning: bogus date in %changelog: Wed Jun  6 2022 GreatSQL <greatsql@greatdb.com> - 8.0.25-16.1
error: Failed build dependencies:
        bison is needed by greatsql-8.0.32-25.1.el8.x86_64
        cmake >= 2.8.2 is needed by greatsql-8.0.32-25.1.el8.x86_64
        cmake >= 3.6.1 is needed by greatsql-8.0.32-25.1.el8.x86_64
...
        zlib-devel is needed by greatsql-8.0.32-25.1.el8.x86_64
        
```

这里贴一下我用上述干净docker环境中安装的一些依赖包：
```
[root@c8 rpmbuild]# dnf install -y  bison cmake cyrus-sasl-devel gcc-c++ gcc-toolset-11 gcc-toolset-11-annobin-plugin-gcc yum krb5-devel 1libaio-devel libcurl-devel libtirpc-devel m4 make ncurses-devel numactl-devel openldap-devel openssl openssl-devel pam-devel perl perl-Carp perl-Data-Dumper perl-Errno perl-Exporter perl-File-Temp perl-Getopt-Long perl-JSON perl-Memoize perl-Time-HiRes readline-devel time zlib-devel
```

由于安装了 `gcc-toolset-11` 包，需要执行下面的命令才能切换到 gcc11 版本环境中，并确认gcc、cmake的版本是否符合要求：
```
[root@c8 rpmbuild]# source /opt/rh/gcc-toolset-11/enable
[root@c8 rpmbuild]# gcc --version
gcc (GCC) 11.2.1 20210728 (Red Hat 11.2.1-1)
Copyright (C) 2021 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

[root@c8 rpmbuild]# cmake --version
cmake version 3.20.2

CMake suite maintained and supported by Kitware (kitware.com/cmake).
```

还需要编译安装`rpcsvc-proto`依赖包
```
[root@c8 rpmbuild]# cd /tmp/
[root@c8 tmp]# tar xf rpcsvc-proto-1.4.tar.gz
[root@c8 tmp]# cd rpcsvc-proto-1.4
[root@c8 rpcsvc-proto-1.4]# ./configure && make && make install
...
make[2]: Leaving directory '/tmp/rpcsvc-proto-1.4'
make[1]: Leaving directory '/tmp/rpcsvc-proto-1.4'
```

安装完这些依赖包后，再次开始尝试编译RPM包。
```
[root@c8 rpcsvc-proto-1.4]# cd /root/rpmbuild/
# 将编译过程输出到日志文件中，更方便观察的排查错误
[root@c8 rpmbuild]# rpmbuild --nodebuginfo --define "_smp_mflags -j14" --define 'dist .el8' --define "_topdir /root/rpmbuild/" -bb ./greatsql.spec > ./rpmbuild.log 2>&1
warning: Macro expanded in comment on line 787: %{_mandir}/man1/mysql.server.1*

warning: Macro expanded in comment on line 956: %{_datadir}/mysql-*/audit_log_filter_linux_install.sql
...
warning: bogus date in %changelog: Wed Jun  6 2022 GreatSQL <greatsql@greatdb.com> - 8.0.25-16.1
Executing(%prep): /bin/sh -e /var/tmp/rpm-tmp.jOIUMM
+ umask 022
+ cd /root/rpmbuild//BUILD
+ cd /root/rpmbuild/BUILD
+ rm -rf greatsql-8.0.32-25
...
```

如果编译失败了，会有类似这样的结果：
```
    bogus date in %changelog: Wed Jun  6 2022 GreatSQL <greatsql@greatdb.com> - 8.0.25-16.1
    Bad exit status from /var/tmp/rpm-tmp.k8RLOL (%build)
```

只需打开 `/root/rpmbuild/rpmbuild.log` 文件，搜索 `error/fail` 等关键字（不区分大小写）应该就能分析出错误原因了。

解决完错误原因，再一次重试编译，这次应该顺利了，耐心等着吧。在这过程中，我们还可以通过观察 `/root/rpmbuild/rpmbuild.log` 文件了解编译的进度情况，例如下面这样，可见进度大约到了91%，胜利在望 ~
```
...
[ 91%] Building CXX object sql/CMakeFiles/binlog.dir/changestreams/misc/column_filters/column_filter_outbound_func_indexes.cc.o
...
```

编译GreatSQL RPM包的过程中要做两遍，一次编译出release包，一次编译出debug包，所以会有一点点费时，正好泡杯好茶安心喝着就是了。

最后，查看编译结果，会有类似下面的日志：
```
[root@c8 rpmbuild]# tail rpmbuild.log
Wrote: /root/rpmbuild/RPMS/x86_64/greatsql-client-debuginfo-8.0.32-25.1.el8.x86_64.rpm
Wrote: /root/rpmbuild/RPMS/x86_64/greatsql-test-debuginfo-8.0.32-25.1.el8.x86_64.rpm
Wrote: /root/rpmbuild/RPMS/x86_64/greatsql-shared-debuginfo-8.0.32-25.1.el8.x86_64.rpm
Wrote: /root/rpmbuild/RPMS/x86_64/greatsql-mysql-router-debuginfo-8.0.32-25.1.el8.x86_64.rpm
Executing(%clean): /bin/sh -e /var/tmp/rpm-tmp.Z174QT
+ umask 022
+ cd /root/rpmbuild//BUILD
+ cd greatsql-8.0.32-25
+ /usr/bin/rm -rf /root/rpmbuild/BUILDROOT/greatsql-8.0.32-25.1.el8.x86_64
+ exit 0
```

再看下编译生成的RPM文件包：
```
[root@c8 rpmbuild]# du -sch *
45G     BUILD        #编译工作目录，产生大量编译文件，所以特别大，可以清空
0       BUILDROOT
976M    RPMS        #编译产生的RPM包
1.8G    SOURCES
0       SPECS
0       SRPMS
37M     rpmbuild.log
64K     greatsql.spec
47G     total

[root@c8 rpmbuild]# cd /root/rpmbuild/RPMS/x86_64
[root@c8 x86_64]# ls -la
total 998740
drwxr-xr-x 2 root root      4096 Dec 29 10:27 .
drwxr-xr-x 3 root root        20 Dec 29 10:21 ..
-rw-r--r-- 1 root root  19061972 Dec 29 10:22 greatsql-client-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root  36091240 Dec 29 10:27 greatsql-client-debuginfo-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root   4591912 Dec 29 10:25 greatsql-debuginfo-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root  26174384 Dec 29 10:25 greatsql-debugsource-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root   2241908 Dec 29 10:24 greatsql-devel-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root   2145368 Dec 29 10:24 greatsql-icu-data-files-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root      8100 Dec 29 10:24 greatsql-mysql-config-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root   5259796 Dec 29 10:24 greatsql-mysql-router-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root  37427440 Dec 29 10:28 greatsql-mysql-router-debuginfo-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root  78317640 Dec 29 10:22 greatsql-server-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root 379119548 Dec 29 10:27 greatsql-server-debuginfo-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root   1502984 Dec 29 10:24 greatsql-shared-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root   2805716 Dec 29 10:27 greatsql-shared-debuginfo-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root 409911420 Dec 29 10:24 greatsql-test-8.0.32-25.1.el8.x86_64.rpm
-rw-r--r-- 1 root root  18017572 Dec 29 10:27 greatsql-test-debuginfo-8.0.32-25.1.el8.x86_64.rpm
```

大功告成。

## 3、安装GreatSQL

将编译产生的RPM包文件拷贝到另外一个全新的docker CentOS 8环境下，测试安装是否顺利。下面略过拷贝文件以及新docker镜像环境初始化过程，直接开始安装：
```
[root@cc8 cc8]# rpm -ivh *rpm
Verifying...                          ################################# [100%]
Preparing...                          ################################# [100%]
Updating / installing...
   1:greatsql-shared-8.0.32-25.1.el8  ################################# [ 13%]
   2:greatsql-client-8.0.32-25.1.el8  ################################# [ 25%]
   3:greatsql-icu-data-files-8.0.32-25################################# [ 38%]
   4:greatsql-server-8.0.32-25.1.el8  ################################# [ 50%]
   5:greatsql-test-8.0.32-25.1.el8    ################################# [ 63%]
   6:greatsql-mysql-router-8.0.32-25.1################################# [ 75%]
   7:greatsql-mysql-config-8.0.32-25.1################################# [ 88%]
   8:greatsql-devel-8.0.32-25.1.el8   ################################# [100%]
```

看起来一切都很顺利，成功搞定。



## 延伸阅读
- [玩转MySQL 8.0源码编译](https://mp.weixin.qq.com/s/Lrx-YYYWtHHaxLfY_UZ8GQ)
- [将GreatSQL添加到系统systemd服务](https://mp.weixin.qq.com/s/tSA-DrWT13GN45Csq2tQoA)
- [利用GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/gLaLybt46PqXlV4qWFfyng)
- [InnoDB Cluster+GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/1QUt-rK_5L_UnaLClyve1w)
- [在Docker中部署GreatSQL并构建MGR集群](https://mp.weixin.qq.com/s/CfrYEQD54EXD9mLJJPGs-A)

全文完。

Enjoy GreatSQL :)

