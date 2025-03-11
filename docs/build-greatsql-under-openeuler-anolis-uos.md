# openEuler、龙蜥Anolis、统信UOS系统下编译GreatSQL二进制包

[toc]

## 1. 背景介绍
为了能更好地支持更多操作系统及相关生态，我们决定发布openEuler、龙蜥Anolis、统信UOS三个操作系统下的GreatSQL二进制包。相应的二进制包可以访问gitee.com上的[GreatSQL项目](https://gitee.com/GreatSQL/GreatSQL/releases/tag/GreatSQL-8.0.25-17)下载。

本文简要记录在这三个操作系统下编译GreatSQL二进制包的过程。

## 2. 编译环境

本次编译都是采用鲲鹏916这个型号的CPU（泰山2280服务器系列）：
```
$ lscpu
Architecture:          aarch64
Byte Order:            Little Endian
CPU(s):                64
On-line CPU(s) list:   0-63
Thread(s) per core:    1
Core(s) per socket:    32
Socket(s):             2
NUMA node(s):          4
Model:                 2
BogoMIPS:              100.00
L1d cache:             32K
L1i cache:             48K
L2 cache:              1024K
L3 cache:              16384K
NUMA node0 CPU(s):     0-15
NUMA node1 CPU(s):     16-31
NUMA node2 CPU(s):     32-47
NUMA node3 CPU(s):     48-63
Flags:                 fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid
```
上述 `lscpu` 是在物理机上执行的，实际编译环境则是在这个物理机上运行的虚机中，分配了8个CPU、16G内存。

查看操作系统发行版本

**openEuler**
```
$ cat /etc/os-release

NAME="openEuler"
VERSION="22.03 LTS"
ID="openEuler"
VERSION_ID="22.03"
PRETTY_NAME="openEuler 22.03 LTS"
ANSI_COLOR="0;31"
```
**龙蜥Anolis**
```
$ cat /etc/os-release
NAME="Anolis OS"
VERSION="8.6"
ID="anolis"
ID_LIKE="rhel fedora centos"
VERSION_ID="8.6"
PLATFORM_ID="platform:an8"
PRETTY_NAME="Anolis OS 8.6"
ANSI_COLOR="0;31"
HOME_URL="https://openanolis.cn/"
```

**统信UOS**
```
$ cat /etc/os-release
PRETTY_NAME="UnionTech OS Server 20"
NAME="UnionTech OS Server 20"
VERSION_ID="20"
VERSION="20"
ID="uos"
HOME_URL="https://www.chinauos.com/"
BUG_REPORT_URL="https://bbs.chinauos.com/"
VERSION_CODENAME="kongzi"
PLATFORM_ID="platform:uelc20"
[root@yejr-uos-aarch64 ~]#
[root@yejr-uos-aarch64 ~]#
$ cat /etc/uos-release
UnionTech OS Server release 20 (kongzi)
```

并且都采用OS中预设的默认YUM源

```
$ cat openEuler.repo
#generic-repos is licensed under the Mulan PSL v2.
#You can use this software according to the terms and conditions of the Mulan PSL v2.
#You may obtain a copy of Mulan PSL v2 at:
#    http://license.coscl.org.cn/MulanPSL2
#THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
#PURPOSE.
#See the Mulan PSL v2 for more details.

[OS]
name=OS
baseurl=http://repo.openeuler.org/openEuler-22.03-LTS/OS/$basearch/
enabled=1
gpgcheck=1
gpgkey=http://repo.openeuler.org/openEuler-22.03-LTS/OS/$basearch/RPM-GPG-KEY-openEuler

[everything]
name=everything
baseurl=http://repo.openeuler.org/openEuler-22.03-LTS/everything/$basearch/
enabled=1
gpgcheck=1
gpgkey=http://repo.openeuler.org/openEuler-22.03-LTS/everything/$basearch/RPM-GPG-KEY-openEuler
...
```

**龙蜥Anolis**
```
$ cat AnolisOS-AppStream.repo
[AppStream]
name=AnolisOS-$releasever - AppStream
baseurl=http://mirrors.openanolis.cn/anolis/$releasever/AppStream/$basearch/os
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-ANOLIS
gpgcheck=1
```

**统信UOS**
```
$ cat UniontechOS.repo
[UniontechOS-$releasever-AppStream]
name = UniontechOS $releasever AppStream
baseurl = https://enterprise-c-packages.chinauos.com/server-enterprise-c/kongzi/1050/AppStream/$basearch
enabled = 1
username=$auth_u
password=$auth_p
gpgkey = file:///etc/pki/rpm-gpg/RPM-GPG-KEY-uos-release
gpgcheck = 0
skip_if_unavailable = 1

[UniontechOS-$releasever-BaseOS]
name = UniontechOS $releasever BaseOS
baseurl = https://enterprise-c-packages.chinauos.com/server-enterprise-c/kongzi/1050/BaseOS/$basearch
enabled = 1
username=$auth_u
password=$auth_p
gpgkey = file:///etc/pki/rpm-gpg/RPM-GPG-KEY-uos-release
gpgcheck = 0
skip_if_unavailable = 1
...
```

## 3. 编译前准备工作
参考文档 [麒麟OS+龙芯环境编译GreatSQL](xx)，提前安装必要的一些基础包
```
$ dnf makecache
$ dnf install --skip-broken -y automake bison bison-devel boost-devel bzip2 bzip2-devel clang \
cmake cmake3 diffutils expat-devel file flex gcc gcc-c++ git jemalloc jemalloc-devel \
graphviz libaio-devel libarchive libcurl-devel libevent libevent-devel libverto-libevent libevent-doc libffi-devel libicu-devel libssh \
libtirpc libtirpc-devel libtool libxml2-devel libzstd libzstd-devel lz4-devel \
lz4-static make ncurses-devel ncurses-libs net-tools numactl numactl-devel numactl-libs openldap-clients \
openldap-devel openssl openssl-devel pam pam-devel perl perl-Env perl-JSON perl-Memoize \
perl-Time-HiRes pkg-config psmisc re2-devel readline-devel \
snappy-devel tar time unzip vim vim-common wget zlib-devel
```

openEuler下就可以安装文档 [https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/build-greatsql-with-source-under-kylin-and-loongson.md](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/build-greatsql-with-source-under-kylin-and-loongson.md) 中列出的所有包，包括 jemalloc 包。

下载安装jemalloc rpm包（rpm包依赖glibc版本，可能无法直接使用，可以自行下载源码包编译）
- https://fedora.pkgs.org/36/fedora-aarch64/jemalloc-5.2.1-7.fc36.aarch64.rpm.html
- https://fedora.pkgs.org/36/fedora-aarch64/jemalloc-devel-5.2.1-7.fc36.aarch64.rpm.html
- 源码包 https://sourceforge.net/projects/jemalloc.mirror/files/

当然了，jemalloc并库不是必须的，用它的好处是可以优化内存管理性能等。有条件的话尽量启用，实在搞定就放弃（非必须）。

如果是ARM环境下，可以不必安装配置 jemalloc 依赖。

如果需要手动编译安装jemalloc，参考下面的方法即可：
```
$ tar zxf jemalloc-5.2.1.tar.gz
$ mv jemalloc-jemalloc-886e40b/
$ ./autogen.sh
$ ./configure --prefix=/usr && make && make install
```

分别下载几个编译过程中需要的依赖包：
- boost, https://boostorg.jfrog.io/artifactory/main/release/1.73.0/source/boost_1_73_0.tar.gz
- patchelf, https://github.com/NixOS/patchelf/archive/refs/tags/0.14.tar.gz, 下载后重命名为 patchelf-0.14.tar.gz
- rpcsvc-proto, https://github.com/thkukuk/rpcsvc-proto/releases/download/v1.4/rpcsvc-proto-1.4.tar.gz

下载GreatSQL源码包：`https://product.greatdb.com/GreatSQL-8.0.25-17/greatsql-8.0.25-17.tar.gz`

将所有的源码包都放在 /opt 目录下。

编译安装patchelf：
```
$ cd /opt && tar zxvf patchelf-0.14.tar.gz && cd patchelf-0.14 && ./bootstrap.sh && ./configure && make && make install
```

编译安装rpcsvc-proto：
```
$ cd /opt && tar zxvf rpcsvc-proto-1.4.tar.gz && cd rpcsvc-proto-1.4/ && ./configure && make && make install
```

解压boost依赖包：
```
$ cd /opt && tar zxvf boost_1_73_0.tar.gz
```

确认glibc版本：
```
$ ldd --version

ldd (GNU libc) 2.28
Copyright (C) 2018 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
Written by Roland McGrath and Ulrich Drepper.
```

在本次编译过程中，openEuler 2203的glibc版本是2.34。

确认gcc版本：
```
$ gcc --version
```
建议gcc版本在8.3以上，否则可能安装失败。

## 4. 编译GreatSQL
接下来编译GreatSQL二进制包
```
$ cat /opt/greatsql-build-tarball.sh

#!/bin/bash
MAJOR_VERSION=8
MINOR_VERSION=0
PATCH_VERSION=25
RELEASE=17
REVISION="4733775f703"
GLIBC=`ldd --version | grep ldd | tail -n 1 | awk '{print $NF}'`
ARCH=aarch64
OS=openEuler
PKG_NAME=GreatSQL-${MAJOR_VERSION}.${MINOR_VERSION}.${PATCH_VERSION}-${RELEASE}-${OS}-glibc${GLIBC}-${ARCH}BASE_DIR=/usr/local/${PKG_NAME}
SRC_DIR=/opt
BOOST_SOURCE_DIR=boost_1_73_0
GREATSQL_SOURCE_DIR=greatsql-8.0.25-17
JOBS=`nproc`

# 如果你的OS环境下已安装jemalloc，建议也启用jemalloc编译选项
# 如果没有安装jemalloc，则将本行参数注释掉
# 如果是ARM环境下，可以不必安装配置 jemalloc 依赖
if [ ${ARCH} = "x86_64" ] ; then
  CMAKE_EXE_LINKER_FLAGS=" -ljemalloc "
fi

cd ${SRC_DIR}/${GREATSQL_SOURCE_DIR} && \
rm -fr bld && \
mkdir bld && \
cd bld && \
cmake .. -DBOOST_INCLUDE_DIR=${SRC_DIR}/${BOOST_SOURCE_DIR} \
-DLOCAL_BOOST_DIR=${SRC_DIR}/${BOOST_SOURCE_DIR} \
-DCMAKE_INSTALL_PREFIX=${BASE_DIR} -DWITH_ZLIB=bundled \
-DWITH_NUMA=ON -DCMAKE_EXE_LINKER_FLAGS="${CMAKE_EXE_LINKER_FLAGS}" \
-DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_CONFIG=mysql_release \
-DWITH_TOKUDB=OFF -DWITH_ROCKSDB=OFF \
-DCOMPILATION_COMMENT="GreatSQL (GPL), Release ${RELEASE}, Revision ${REVISION}" \
-DMAJOR_VERSION=${MAJOR_VERSION} -DMINOR_VERSION=${MINOR_VERSION} -DPATCH_VERSION=${PATCH_VERSION} \
-DWITH_UNIT_TESTS=OFF -DWITH_NDBCLUSTER=OFF -DWITH_SSL=system -DWITH_SYSTEMD=ON \
-DWITH_LIBEVENT=system \
&& make -j${JOBS} && make -j${JOBS} install
```

不出意外的话，就可以编译生成二进制文件了。

## 5. 初始化并启动GreatSQL数据库
GreatSQL初始化（[my.cnf可以参考这份模板](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example-greatsql-8.0.25-17)）
```
$ groupadd mysql && useradd -g mysql mysql -s /sbin/nologin -d /dev/null

$ echo '/usr/local/GreatSQL-8.0.25-17-openEuler-glibc2.34-aarch64/lib/' > /etc/ld.so.conf.d/greatsql.conf

$ ldconfig -p | grep -i percona
    libperconaserverclient.so.21 (libc6,AArch64) => /usr/local/GreatSQL-8.0.25-17-openEuler-glibc2.34-aarch64/lib/libperconaserverclient.so.21
    libperconaserverclient.so (libc6,AArch64) => /usr/local/GreatSQL-8.0.25-17-openEuler-glibc2.34-aarch64/lib/libperconaserverclient.so
    
    
# 确保没有找不到的动态库
$ ldd /usr/local/GreatSQL-8.0.25-17-openEuler-glibc2.34-aarch64/bin/mysqld | grep -i not

$ ./bin/mysqld --defaults-file=/etc/my.cnf --initialize-insecure

$ ./bin/mysqld --defaults-file=/etc/my.cnf &

$ lsof -p `pidof mysqld` | grep -i jemalloc
mysqld  85204 mysql  mem       REG                8,3     471696   3329101 /usr/lib64/libjemalloc.so.2
```

## 6. 运行sysbench测试
准备跑一轮sysbench测试
```
#先设置PATH
$ export PATH=$PATH:/usr/local/GreatSQL-8.0.25-17-openEuler-glibc2.34-aarch64/bin

$ mysqladmin create sbtest

$ cd /usr/local/share/sysbench/
$ sysbench /usr/local/share/sysbench/oltp_read_write.lua --mysql-host=localhost --mysql-user=root --mysql-password="" --mysql-socket=/usr/local/GreatSQL-8.0.25-17-openEuler-glibc2.34-aarch64/data/mysql.sock --mysql-db=sbtest --db-driver=mysql --tables=10 --table_size=10000 prepare

$ for i in $(seq 1 3);do sysbench /usr/local/share/sysbench/oltp_read_write.lua --mysql-host=localhost --mysql-user=root --mysql-password="" --mysql-socket=/usr/local/GreatSQL-8.0.25-17-openEuler-glibc2.34-aarch64/data/mysql.sock --mysql-db=sbtest --db-driver=mysql --tables=10 --table_size=10000 --report-interval=1 --threads=8 --rand-type=uniform --db-ps-mode=disable  --time=900 run > greatsql-802517-$i.log; sleep 300; done
```

## 附录：编译sysbench
```
#先做个动态库软链接
$ cd /usr/local/GreatSQL-8.0.25-17-openEuler-glibc2.34-aarch64/lib/
$ ln -s libperconaserverclient.so libmysqlclient.so
$ cd /tmp/sysbench/
$ ./autogen.sh
$ ./configure --with-mysql-includes=/usr/local/GreatSQL-8.0.25-17-openEuler-glibc2.34-aarch64/include/ --with-mysql-libs=/usr/local/GreatSQL-8.0.25-17-openEuler-glibc2.34-aarch64/lib/ && make && make install
```

全文完。

