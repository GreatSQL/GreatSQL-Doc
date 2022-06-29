# 麒麟OS+龙芯环境编译GreatSQL

[toc]

本次介绍如何在麒麟OS + 龙芯CPU的环境下将GreatSQL源码编译成二进制文件及RPM包等。

本文介绍的运行环境是Kylin Linux V10：
```
[root@ky10 ~]# cat /etc/system-release
Kylin Linux Advanced Server release V10 (Tercel)

[root@ky10 ~]# uname -a
Linux ky10 4.19.90-23.19.v2101.a.ky10.loongarch64 #1 SMP Mon Sep 13 22:33:20 CST 2021 loongarch64 loongarch64 loongarch64 GNU/Linux
```

## 1、准备工作
### 1.1、配置yum源
开始编译之前，建议先配置好yum源，方便安装一些工具。本环节是龙芯的同学提供的，已经事先配置过了，忽略。

### 1.2、安装一波编译环境所需要的软件包
参考这份Dockerfile，安装相应的软件包，如果发现个别软件包在麒麟OS环境里没有的话，直接去掉即可：
```
dnf install -y automake bison bison-devel boost-devel bzip2 bzip2-devel clang \
cmake cmake3 diffutils expat-devel file flex gcc gcc-c++ git jemalloc jemalloc-devel \
graphviz libaio-devel libarchive libcurl-devel libevent-devel libffi-devel libicu-devel libssh \
libtirpc libtirpc-devel libtool libxml2-devel libzstd libzstd-devel lz4-devel \
lz4-static make ncurses-devel ncurses-libs net-tools numactl numactl-devel numactl-libs openldap-clients \
openldap-devel openssl openssl-devel pam pam-devel perl perl-Env perl-JSON perl-Memoize \
perl-Time-HiRes pkg-config psmisc re2-devel readline-devel \
snappy-devel tar time unzip vim wget zlib-devel
```
Dockerfile参考：https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/build-gs/Dockerfile/Dockerfile-centos8-x86

### 1.3、再下载安装几个必要的软件包
分别下载几个编译过程中需要的依赖包：
- boost, https://boostorg.jfrog.io/artifactory/main/release/1.73.0/source/boost_1_73_0.tar.gz
- patchelf, https://github.com/NixOS/patchelf/archive/refs/tags/0.14.tar.gz, 下载后重命名为 patchelf-0.14.tar.gz
- rpcsvc-proto, https://github.com/thkukuk/rpcsvc-proto/releases/download/v1.4/rpcsvc-proto-1.4.tar.gz

下载GreatSQL源码包：https://product.greatdb.com/GreatSQL-8.0.25-16/greatsql-8.0.25-16.tar.gz

将所有的软件包都放在 /opt 目录下。

编译安装patchelf：
```
[root@ky10 ~]# cd /opt && tar zxvf patchelf-0.14.tar.gz && cd patchelf-0.14 && ./bootstrap.sh && ./configure && make && make install
```

编译安装rpcsvc-proto：
```
[root@ky10 ~]# cd /opt && tar zxvf rpcsvc-proto-1.4.tar.gz && cd rpcsvc-proto-1.4/ && ./configure && make && make install
```

## 2、编译GreatSQL
解压GreatSQL和boost缩源码包：
```
[root@ky10 ~]# cd /opt
[root@ky10 ~]# tar zxf /opt/greatsql-8.0.25-16.tar.gz -C /opt
[root@ky10 ~]# tar zxf /opt/boost_1_73_0.tar.gz -C /opt
```

在开始编译前，需要修改GreatSQL源码以适配龙芯架构平台：
```
[root@ky10 ~]# cd /opt/greatsql-8.0.25-16

#大概要修改106行附近的内容
[root@ky10 ~]# vim extra/icu/source/i18n/double-conversion-utils.h +106

#修改这行内容，增加对龙芯架构平台的支持
    defined(__mips__) || \
=>
    defined(__mips__) || defined(__loongarch__) || \
```
保存退出，再将代码重新打包压缩，之后就可以进行编译安装了。
```
[root@ky10 ~]# tar zcf greatsql-8.0.25-16.tar.gz greatsql-8.0.25-16
```

### 2.1、编译生成二进制文件包
用下面的命令进行编译：
```
[root@ky10 ~]# cd /opt/greatsql-8.0.25-16 && \
rm -fr bld && \
mkdir bld && \
cd bld && \
cmake .. -DBOOST_INCLUDE_DIR=/opt/boost_1_73_0 \
-DLOCAL_BOOST_DIR=/opt/boost_1_73_0 \
-DCMAKE_INSTALL_PREFIX=/usr/local/GreatSQL-8.0.25-16 \
-DWITH_ZLIB=bundled \
-DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_CONFIG=mysql_release \
-DWITH_TOKUDB=OFF \
-DWITH_ROCKSDB=OFF \
-DCOMPILATION_COMMENT="GreatSQL (GPL), Release 16, Revision 8bb0e5af297" \
-DMAJOR_VERSION=8 \
-DMINOR_VERSION=0 \
-DPATCH_VERSION=25 \
-DWITH_UNIT_TESTS=OFF \
-DWITH_NDBCLUSTER=OFF \
-DWITH_SSL=system \
-DWITH_SYSTEMD=ON \
-DWITH_AUTHENTICATION_LDAP=OFF \
&& make -j16 VERBOSE=1 && make install
```
参数 *-j16* 设定为并行编译的逻辑CPU数量，可以指定为比逻辑CPU总数少一点，不要把所有CPU都跑满。

编译完成后，就会将二进制文件安装到 */usr/local/GreatSQL-8.0.25-16* 目录下。

### 2.2、编译生成RPM文件包
由于GreatSQL自带的编译脚本还不能适配龙芯环境，所以需要手动编译生成RPM文件包。

可参考[这份 greatsql.spec 文件](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/build-gs/greatsql.spec)，复制到本地保存成 greatsql.spc 文件，然后用下面的命令进行编译：
```
[root@ky10 ~]# mkdir -p /root/rpmbuild/SOURCES/
#将源码包和boost包复制过来
[root@ky10 ~]# cp greatsql-8.0.25-16.tar.gz boost_1_73_0.tar.gz /root/rpmbuild/SOURCES/
[root@ky10 ~]# cd /opt/greatsql-8.0.25-16/build-gs
[root@ky10 ~]# rpmbuild -bb greatsql.spec
```

就会开始编译工作，顺利的话就会生成相应的RPM文件包了。

这就可以用在copy到其他服务器上直接安装使用了。

## 3、安装GreatSQL
执行下面的命令安装GreatSQL
```
$ rpm -ivh greatsql*rpm
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

### 3.1 my.cnf参考

RPM方式安装后的GreatSQL默认配置不是太合理，建议参考下面这份my.cnf文档：

- [my.cnf for GreatSQL 8.0.25-16](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example-greatsql-8.0.25-16)

调整文档中关于`datadir`目录配置等相关选项，默认 `datadir=/var/lib/mysql` 通常都会改掉，例如替换成 `datadir=/data/GreatSQL`，修改完后保存退出，
替换原来的 `/etc/my.cnf`，然后重启GreatSQL，会重新进行初始化。
```
# 新建 /data/GreatSQL 空目录，并修改目录所有者
$ mkdir -p /data/GreatSQL
$ chown -R mysql:mysql /data/GreatSQL

# 重启mysqld服务，即自行完成重新初始化
$ systemctl restart mysqld
```

### 3.2 登入GreatSQL
首次登入GreatSQL前，需要先找到初始化时随机生成的root密码：
```
$ grep root /data/GreatSQL/error.log
[Note] [MY-010454] [Server] A temporary password is generated for root@localhost: dt_)MtExl594
```

其中的 **dt_)MtExl594** 就是初始化时随机生成的密码，在登入GreatSQL时输入该密码：
```
$ mysql -uroot -p'dt_)MtExl594'
mysql: [Warning] Using a password on the command line interface can be insecure.
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 8
Server version: 8.0.25-16

Copyright (c) 2021-2021 GreatDB Software Co., Ltd
Copyright (c) 2009-2021 Percona LLC and/or its affiliates
Copyright (c) 2000, 2021, Oracle and/or its affiliates.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> \s
ERROR 1820 (HY000): You must reset your password using ALTER USER statement before executing this statement.
mysql>
```

首次登入立刻提醒该密码已过期，需要修改，执行类似下面的命令修改即可：
```
mysql> ALTER USER USER() IDENTIFIED BY 'GreatSQL-8025~%';
Query OK, 0 rows affected (0.02 sec)
```
之后就可以用这个新密码再次登入GreatSQL了。

### 3.3 创建新用户、测试库&表，及写入数据
修改完root密码后，应尽快创建普通用户，用于数据库的日常使用，减少超级用户root的使用频率，避免误操作意外删除重要数据。
```
#创建一个新用户GreatSQL，只允许从192.168.0.0/16网络连入，密码是 GreatSQL-2022
mysql> CREATE USER GreatSQL@'192.168.0.0/16' IDENTIFIED BY 'GreatSQL-2022';
Query OK, 0 rows affected (0.06 sec)

#创建一个新的用户库，并对GreatSQL用户授予读写权限
mysql> CREATE DATABASE GreatSQL;
Query OK, 1 row affected (0.03 sec)

mysql> GRANT ALL ON GreatSQL.* TO GreatSQL@'192.168.0.0/16';
Query OK, 0 rows affected (0.03 sec)
```

切换到普通用户GreatSQL登入，创建测试表，写入数据：
```
$ mysql -h192.168.1.10 -uGreatSQL -p'GreatSQL-2022'
...
# 切换到GreatSQL数据库下
mysql> use GreatSQL;
Database changed

# 创建新表
mysql> CREATE TABLE t1(id INT PRIMARY KEY);
Query OK, 0 rows affected (0.07 sec)

# 写入测试数据
mysql> INSERT INTO t1 SELECT RAND()*1024;
Query OK, 1 row affected (0.05 sec)
Records: 1  Duplicates: 0  Warnings: 0

# 查询数据
mysql> SELECT * FROM t1;
+-----+
| id  |
+-----+
| 203 |
+-----+
1 row in set (0.00 sec)
```
成功。

## 4、搭建MGR集群

MGR集群的部署可以自己手动一步步操作，也可通过MySQL Shell快速完成，分别参考下面的文档即可：
- [利用GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/gLaLybt46PqXlV4qWFfyng)
- [InnoDB Cluster+GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/1QUt-rK_5L_UnaLClyve1w)
- [ansible一键安装GreatSQL并构建MGR集群](https://mp.weixin.qq.com/s/8hbpus0RxrVnmCdVDHVg2Q)
- [在Docker中部署GreatSQL并构建MGR集群](https://mp.weixin.qq.com/s/CfrYEQD54EXD9mLJJPGs-A)

## 延伸阅读
- [玩转MySQL 8.0源码编译](https://mp.weixin.qq.com/s/Lrx-YYYWtHHaxLfY_UZ8GQ)
- [将GreatSQL添加到系统systemd服务](https://mp.weixin.qq.com/s/tSA-DrWT13GN45Csq2tQoA)
- [利用GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/gLaLybt46PqXlV4qWFfyng)
- [InnoDB Cluster+GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/1QUt-rK_5L_UnaLClyve1w)
- [在Docker中部署GreatSQL并构建MGR集群](https://mp.weixin.qq.com/s/CfrYEQD54EXD9mLJJPGs-A)

## 5、下载龙芯平台GreatSQL二进制包
GreatSQL for 龙芯平台的二进制包也已发布，下载链接：[https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-16](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-16)，找到 “**4. 龙芯/Loongson - Generic**” 标签下载即可。

## 6、补充： 编译sysbench
在龙芯平台下编译sysbench时，如果用默认参数可能会遇到luajit编译报错，例如：
```
make[2]: Entering directory '/opt/sysbench-1.0.20/third_party/luajit/luajit'
make -C src clean
make[3]: Entering directory '/opt/sysbench-1.0.20/third_party/luajit/luajit/src'
lj_arch.h:59:2: error: #error "No support for this architecture (yet)"
 #error "No support for this architecture (yet)"
  ^~~~~
lj_arch.h:357:2: error: #error "No target architecture defined"
 #error "No target architecture defined"
  ^~~~~
```
这时修改编译参数，改成用操作系统自带的luajit库即可：
```
$ ./configure --with-system-luajit
```

修改前后，执行 `./configure` 的区别是这样的：
```
# 修改前
LuaJIT             : bundled
LUAJIT_CFLAGS      : -I$(abs_top_builddir)/third_party/luajit/inc

# 修改后
LuaJIT             : system
LUAJIT_CFLAGS      : -I/usr/include/luajit-2.1
```

全文完。

Enjoy GreatSQL :)
