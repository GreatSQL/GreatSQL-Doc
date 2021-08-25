# 在Linux下源码编译安装GreatSQL

## 0、提纲
[toc]

本次介绍如何利用Docker来将GreatSQL源码编译成二进制文件，以及制作二进制包、RPM包等。

本文介绍的运行环境是CentOS 7.9：
```
[root@greatsql ~]# cat /etc/redhat-release
CentOS Linux release 7.9.2009 (Core)

[root@greatsql ~]# uname -a
Linux greatsql 3.10.0-1160.11.1.el7.x86_64 #1 SMP Fri Dec 18 16:34:56 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
```

## 1、准备工作
### 1.1、配置yum源
开始编译之前，建议先配置好yum源，方便安装一些工具。

以阿里、腾讯两大云主机为例，可以这样配置（两个yum源自行二选一）：
```
[root@greatsql ~]# mv /etc/yum.repos.d/CentOS-Base.repo{,.orig}

#阿里云
[root@greatsql ~]# wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo

#腾讯云
[root@greatsql ~]# wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.cloud.tencent.com/repo/centos7_base.repo

#替换完后，更新缓存
[root@greatsql ~]# yum clean all
[root@greatsql ~]# yum makecache
```
### 1.2、安装docker
安装docker，并启动docker进程。
```
[root@greatsql]# yum install -y docker
[root@greatsql]# systemctl start docker
```

### 1.3、提前下载几个必要的安装包
分别下载几个编译过程中需要的依赖包：
- boost, https://boostorg.jfrog.io/artifactory/main/release/1.73.0/source/boost_1_73_0.tar.gz
- git, https://github.com/git/git/archive/v2.27.0.tar.gz, 下载后重命名为 git-v2.27.0.tar.gz
- patchelf, https://github.com/NixOS/patchelf/archive/refs/tags/0.12.tar.gz, 下载后重命名为 patchelf-0.12.tar.gz
- rpcsvc-proto, https://github.com/thkukuk/rpcsvc-proto/releases/download/v1.4/rpcsvc-proto-1.4.tar.gz

下载GreatSQL源码包：https://gitee.com/GreatSQL/GreatSQL/archive/greatsql-8.0.25-15.tar.gz

### 1.4、构建docker镜像
用下面这份Dockerfile构建镜像，这里以CentOS 7为例：
```
FROM centos:7
ENV LANG en_US.utf8

RUN yum install -y epel-release && \
curl -o /etc/yum.repos.d/CentOS-Base.repo http://mirrors.cloud.tencent.com/repo/centos7_base.repo && \
yum clean all && \
yum makecache
RUN yum install -y yum-utils && \
yum install -y wget diffutils net-tools vim git gcc gcc-c++ automake libtool cmake cmake3 \
make psmisc openssl-devel zlib-devel readline-devel bzip2-devel expat-devel gflags-devel \
bison bison-devel flex wget unzip libcurl-devel libevent-devel libffi-devel lz4-devel lz4-static \
file clang bzip2 snappy-devel libxml2-devel libtirpc libtirpc-devel numactl-devel numactl-libs \
numactl gtest-devel openldap-devel openldap-clients rpcgen pam-devel valgrind boost-devel rpm* tar \
centos-release-scl libzstd libzstd-static libzstd-devel perl-Env perl-JSON time libaio-devel \
ncurses-devel ncurses-libs pam python-devel redhat-lsb-core scl-utils-build pkg-config ccache

RUN yum install -y devtoolset-10-gcc*
RUN echo 'scl enable devtoolset-10 bash' >> /root/.bash_profile

# update git
COPY git-v2.27.0.tar.gz /tmp/
RUN cd /tmp/ && tar -xzvf git-v2.27.0.tar.gz && cd git-2.27.0 && make prefix=/opt/git/ all && make prefix=/opt/git/ install
RUN mv /usr/bin/git /usr/bin/git.bk && ln -s /opt/git/bin/git /usr/bin/git

# update patchelf 0.12
COPY patchelf-0.12.tar.gz /tmp/
RUN cd /tmp && tar -xzvf patchelf-0.12.tar.gz && cd patchelf && ./bootstrap.sh && ./configure && make && make install

COPY rpcsvc-proto-1.4.tar.gz /tmp/rpcsvc-proto-1.4.tar.gz
RUN tar zxvf /tmp/rpcsvc-proto-1.4.tar.gz -C /tmp && cd /tmp/rpcsvc-proto-1.4/ && ./configure && make && make install

RUN rm -fr /tmp/*

COPY boost_1_73_0.tar.gz /opt/

RUN ln -fs /usr/bin/cmake3 /usr/bin/cmake
```

开始构建docker镜像，成功后再保存到本地并导入本地镜像：
```
[root@greatsql ~]# docker build -t centos7-greatsql .
... ...
[root@greatsql ~]# docker save -o centos7-greatsql.tar centos7-greatsql
[root@greatsql ~]# docker load -i centos7-greatsql.tar
```

创建一个docker容器，并将GreatSQL源码包copy进去：
```
[root@greatsql ~]# docker run -itd --name greatsql --hostname=greatsql centos7-greatsql bash
[root@greatsql ~]# docker cp /opt/greatsql-8.0.25-15.tar.gz greatsql:/opt/
[root@greatsql ~]# docker exec -it greatsql bash
[root@greatsql /]# ls -l /opt/
-rw------- 1 root root 128699082 Jul 27 06:56 boost_1_73_0.tar.gz
drwxr-xr-x 5 root root      4096 Jul 28 06:38 git
-rw------- 1 1000 1000 526639994 Jul 27 05:59 greatsql-8.0.25-15.tar.gz
drwxr-xr-x 3 root root      4096 Jul 28 06:34 rh
```

## 2、编译GreatSQL
进入容器后，解压GreatSQL和boost缩源码包：
```
[root@greatsql /]# tar zxf /opt/greatsql-8.0.25-15.tar.gz -C /opt
[root@greatsql /]# tar zxf /opt/boost_1_73_0.tar.gz -C /opt/greatsql-8.0.25-15/
```

### 2.1、只编译二进制文件
如果只是想在本机使用，则可以只编译出二进制文件即可，无需打包或制作RPM包。用下面的命令进行编译：
```
[root@greatsql /]# cmake3 /opt/greatsql-8.0.25-15 \
-DBUILD_TESTING=OFF -DUSE_GTAGS=OFF -DUSE_CTAGS=OFF \
-DUSE_ETAGS=OFF \-DUSE_CSCOPE=OFF -DWITH_TOKUDB=OFF \
-DBUILD_CONFIG=mysql_release -DCMAKE_BUILD_TYPE=RelWithDebInfo \
-DFEATURE_SET=community \
-DCMAKE_INSTALL_PREFIX=/usr/local/GreatSQL-8.0.25-15-Linux \
-DMYSQL_DATADIR=/usr/local/GreatSQL-8.0.25-15-Linux/data \
-DROUTER_INSTALL_LIBDIR=/usr/local/GreatSQL-8.0.25-15-Linux/lib/mysqlrouter/private \
-DROUTER_INSTALL_PLUGINDIR=/usr/local/GreatSQL-8.0.25-15-Linux/lib/mysqlrouter/plugin \
-DCOMPILATION_COMMENT='GreatSQL (GPL), Release 15, Revision e36e91b7242' \
-DWITH_PAM=ON -DWITH_ROCKSDB=ON -DROCKSDB_DISABLE_AVX2=1 -DROCKSDB_DISABLE_MARCH_NATIVE=1 \
-DWITH_INNODB_MEMCACHED=ON -DWITH_ZLIB=bundled -DWITH_NUMA=ON -DWITH_LDAP=system \
-DFORCE_INSOURCE_BUILD=1 -DWITH_LIBEVENT=bundled -DWITH_ZSTD=bundled \
-DWITH_BOOST=/opt/greatsql-8.0.25-15/boost_1_73_0
```
cmake过程如果没报错，就会输出类似下面的结果：
```
... ...
-- Build files have been written to: /opt/greatsql-8.0.25-15
```
接下来可以开始正式编译了：
```
[root@greatsql ~]# make -j30 VERBOSE=1 && make install
```
参数 *-j30* 设定为并行编译的逻辑CPU数量，可以指定为比逻辑CPU总数少一点，不要把所有CPU都跑满。

编译完成后，就会将二进制文件安装到 */usr/local/GreatSQL-8.0.25-15-Linux.x86_64* 目录下。

### 2.2、编译并打包成二进制文件包或RPM包
如果是想要在编译完后也能拷贝到其他服务器上使用，也可以直接编译生成二进制包或RPM包，可以用下面的命令编译：
```
[root@greatsql ~]# cd /opt/greatsql-8.0.25-15/build-gs/
[root@greatsql ~]# export your_processors=30   #同上，修改并行CPU数量
[root@greatsql ~]# export TAR_PROCESSORS=-T$your_processors
[root@greatsql ~]# export MAKE_JFLAG=-j$your_processors
[root@greatsql ~]# mkdir -p workdir
[root@greatsql ~]# cp /opt/boost_1_73_0.tar.gz /opt/greatsql-8.0.25-15/build-gs/
[root@greatsql ~]# cp /opt/greatsql-8.0.25-15.tar.gz /opt/greatsql-8.0.25-15/build-gs/workdir/

# 选择1：编译并打包成二进制包
[root@greatsql ~]# bash -xe ./percona-server-8.0_builder.sh --builddir=`pwd`/workdir --get_sources=0 --install_deps=0 --with_ssl=1 --build_tarball=1 --build_src_rpm=0 --build_rpm=0 --no_git_info=1 --local_boost=1

# 选择2：编译并打包成RPM包
[root@greatsql ~]# bash -xe ./percona-server-8.0_builder.sh --builddir=`pwd`/workdir --get_sources=0 --install_deps=0 --with_ssl=1 --build_tarball=0 --build_src_rpm=1 --build_rpm=1 --no_git_info=1 --local_boost=1
```

编译过程中如果遇到类似下面的patchelf报错：
```
+ patchelf --replace-needed libreadline.so.7 libreadline.so bin/mysql
patchelf: cannot normalize PT_NOTE segment: non-contiguous SHT_NOTE sections
```
可以参考这个patch：[patchelf: Fix alignment issues with contiguous note sections #275](https://github.com/NixOS/patchelf/pull/275/files)，修改下源码，在容器里重新手动编译patchelf。

编译结束后，就会在 */opt/greatsql-8.0.25-15/build-gs/workdir/* 目录下生成相应的二进制包、RPM包：
```
[root@greatsql build-gs]# du -sh workdir/TARGET/
40M     workdir/TARGET/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal.tar.xz
500M    workdir/TARGET/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64.tar.xz

[root@greatsql build-gs]# du -sh workdir/rpm/greatsql-*
14M     workdir/rpm/greatsql-client-8.0.25-15.1.el8.x86_64.rpm
30M     workdir/rpm/greatsql-client-debuginfo-8.0.25-15.1.el8.x86_64.rpm
3.4M    workdir/rpm/greatsql-debuginfo-8.0.25-15.1.el8.x86_64.rpm
23M     workdir/rpm/greatsql-debugsource-8.0.25-15.1.el8.x86_64.rpm
2.1M    workdir/rpm/greatsql-devel-8.0.25-15.1.el8.x86_64.rpm
4.6M    workdir/rpm/greatsql-mysql-router-8.0.25-15.1.el8.x86_64.rpm
27M     workdir/rpm/greatsql-mysql-router-debuginfo-8.0.25-15.1.el8.x86_64.rpm
13M     workdir/rpm/greatsql-rocksdb-8.0.25-15.1.el8.x86_64.rpm
204M    workdir/rpm/greatsql-rocksdb-debuginfo-8.0.25-15.1.el8.x86_64.rpm
60M     workdir/rpm/greatsql-server-8.0.25-15.1.el8.x86_64.rpm
343M    workdir/rpm/greatsql-server-debuginfo-8.0.25-15.1.el8.x86_64.rpm
1.4M    workdir/rpm/greatsql-shared-8.0.25-15.1.el8.x86_64.rpm
2.5M    workdir/rpm/greatsql-shared-debuginfo-8.0.25-15.1.el8.x86_64.rpm
440M    workdir/rpm/greatsql-test-8.0.25-15.1.el8.x86_64.rpm
18M     workdir/rpm/greatsql-test-debuginfo-8.0.25-15.1.el8.x86_64.rpm
```
这就可以用在copy到其他服务器上安装使用了。

## 3、初始化GreatSQL
本次计划在下面3台服务器上部署MGR集群：

| node | ip | datadir | port |role|
| --- | --- | --- | --- | --- |
| nodeA| 172.16.16.10 | /data/GreatSQL/ | 3306 | PRIMARY |
| nodeB| 172.16.16.11 | /data/GreatSQL/ | 3306 | SECONDARY |
| nodeC| 172.16.16.12 | /data/GreatSQL/ | 3306 | SECONDARY |

先在nodeA服务器上执行下面的初始化工作，另外两个服务器也照做一遍即可。

首先编辑 `/etc/my.cnf` 配置文件，可参考采用下面的配置参数：

```
#my.cnf
[mysqld]
user	= mysql
port	= 3306
#主从复制或MGR集群中，server_id记得要不同
#另外，实例启动时会生成 auto.cnf，里面的 server_uuid 值也要不同
#server_uuid的值还可以自己手动指定，只要符合uuid的格式标准就可以
server_id = 3306
basedir=/usr/local/GreatSQL-8.0.25-15-Linux.x86_64
datadir	= /data/GreatSQL
socket	= /data/GreatSQL/mysql.sock
pid-file = mysql.pid
character-set-server = UTF8MB4
skip_name_resolve = 1
#若你的MySQL数据库主要运行在境外，请务必根据实际情况调整本参数
default_time_zone = "+8:00"

#performance setttings
lock_wait_timeout = 3600
open_files_limit    = 65535
back_log = 1024
max_connections = 512
max_connect_errors = 1000000
table_open_cache = 1024
table_definition_cache = 1024
thread_stack = 512K
sort_buffer_size = 4M
join_buffer_size = 4M
read_buffer_size = 8M
read_rnd_buffer_size = 4M
bulk_insert_buffer_size = 64M
thread_cache_size = 768
interactive_timeout = 600
wait_timeout = 600
tmp_table_size = 32M
max_heap_table_size = 32M

#log settings
log_timestamps = SYSTEM
log_error = /data/GreatSQL/error.log
log_error_verbosity = 3
slow_query_log = 1
log_slow_extra = 1
slow_query_log_file = /data/GreatSQL/slow.log
long_query_time = 0.1
log_queries_not_using_indexes = 1
log_throttle_queries_not_using_indexes = 60
min_examined_row_limit = 100
log_slow_admin_statements = 1
log_slow_slave_statements = 1
log_bin = /data/GreatSQL/binlog
binlog_format = ROW
sync_binlog = 1
binlog_cache_size = 4M
max_binlog_cache_size = 2G
max_binlog_size = 1G
binlog_rows_query_log_events = 1
binlog_expire_logs_seconds = 604800
#MySQL 8.0.22前，想启用MGR的话，需要设置binlog_checksum=NONE才行
binlog_checksum = CRC32
gtid_mode = ON
enforce_gtid_consistency = TRUE

#myisam settings
key_buffer_size = 32M
myisam_sort_buffer_size = 128M

#replication settings
master_info_repository = TABLE
relay_log_info_repository = TABLE
relay_log_recovery = 1
slave_parallel_type = LOGICAL_CLOCK
#可以设置为逻辑CPU数量的2倍
slave_parallel_workers = 64
binlog_transaction_dependency_tracking = WRITESET
slave_preserve_commit_order = 1
slave_checkpoint_period = 2

#mgr settings
loose-plugin_load_add = 'mysql_clone.so'
loose-plugin_load_add = 'group_replication.so'
loose-group_replication_group_name = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"
#MGR本地节点IP:PORT，请自行替换
loose-group_replication_local_address = "172.16.16.10:33061"
#MGR集群所有节点IP:PORT，请自行替换
loose-group_replication_group_seeds = "172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061"
loose-group_replication_start_on_boot = OFF
loose-group_replication_bootstrap_group = OFF
loose-group_replication_exit_state_action = READ_ONLY
loose-group_replication_flow_control_mode = "DISABLED"
loose-group_replication_single_primary_mode = ON
loose-group_replication_communication_max_message_size = 10M

#innodb settings
transaction_isolation = REPEATABLE-READ
innodb_buffer_pool_size = 64G
innodb_buffer_pool_instances = 8
innodb_data_file_path = ibdata1:12M:autoextend
innodb_flush_log_at_trx_commit = 1
innodb_log_buffer_size = 32M
innodb_log_file_size = 2G
innodb_log_files_in_group = 3
innodb_max_undo_log_size = 4G
# 根据您的服务器IOPS能力适当调整
# 一般配普通SSD盘的话，可以调整到 10000 - 20000
# 配置高端PCIe SSD卡的话，则可以调整的更高，比如 50000 - 80000
innodb_io_capacity = 4000
innodb_io_capacity_max = 8000
innodb_open_files = 65535
innodb_flush_method = O_DIRECT
innodb_lru_scan_depth = 4000
innodb_lock_wait_timeout = 10
innodb_rollback_on_timeout = 1
innodb_print_all_deadlocks = 1
innodb_online_alter_log_max_size = 4G
innodb_print_ddl_logs = 1
innodb_status_file = 1
#注意: 开启 innodb_status_output & innodb_status_output_locks 后, 可能会导致log_error文件增长较快
innodb_status_output = 0
innodb_status_output_locks = 1
innodb_sort_buffer_size = 67108864

#innodb monitor settings
innodb_monitor_enable = "module_innodb"
innodb_monitor_enable = "module_server"
innodb_monitor_enable = "module_dml"
innodb_monitor_enable = "module_ddl"
innodb_monitor_enable = "module_trx"
innodb_monitor_enable = "module_os"
innodb_monitor_enable = "module_purge"
innodb_monitor_enable = "module_log"
innodb_monitor_enable = "module_lock"
innodb_monitor_enable = "module_buffer"
innodb_monitor_enable = "module_index"
innodb_monitor_enable = "module_ibuf_system"
innodb_monitor_enable = "module_buffer_page"
innodb_monitor_enable = "module_adaptive_hash"

#innodb parallel query
force_parallel_execute = ON
parallel_default_dop = 8
parallel_max_threads = 96
temptable_max_ram = 8G

#pfs settings
performance_schema = 1
#performance_schema_instrument = '%memory%=on'
performance_schema_instrument = '%lock%=on'
```

执行下面的命令进行初始化：
```
[root@greatsql ~]# /usr/local/GreatSQL-8.0.25-15-Linux.x86_64/bin/mysqld --defaults-file=/etc/my.cnf --initialize-insecure
```
初始化时可选项有 `--initialize` 和 ` --initialize-insecure` 两种，前者会为root账号生成一个随机密码，后者不会。在这里为了省事，选用后者，**生产环境里请务必要为root用户设置安全密码**。

之后就可以启动mysqld进程了：
```
[root@greatsql ~]# /usr/local/GreatSQL-8.0.25-15-Linux.x86_64/bin/mysqld --defaults-file=/etc/my.cnf &
```

GreatSQL是基于Percona Server的分支版本，默认情况下需要用到jemalloc这个库，如果启动过程中报告类似下面的错误，只需要再安装jemalloc或者libaio等相关的软件包即可：
```
/usr/local/GreatSQL-8.0.23-14/bin/mysqld: error while loading shared libraries: libjemalloc.so.1: cannot open shared object file: No such file or directory
```

补充安装libjemalloc库即可：
```
[root@greatsql ~]# yum install -y jemalloc jemalloc-devel
```

如果想要关闭mysqld进程，执行下面的命令即可：
```
# 假设此时root还是空密码
[root@greatsql ~]# /usr/local/GreatSQL-8.0.25-15-Linux.x86_64/bin/mysql -uroot -S/data/GreatSQL/mysql.sock shutdown
```

查看版本号：
```
root@GreatSQL [(none)]> \s
...
Server version:		8.0.25-15 GreatSQL, Release 15, Revision 80bbf22abbd
...
```
这就启动GreatSQL服务了，接下来同样的方法，完成另外两个服务器上的GreatSQL初始化并启动，然后开始构建MGR集群。

另外，也可以参考这篇指南"[将GreatSQL添加到系统systemd服务](https://mp.weixin.qq.com/s/tSA-DrWT13GN45Csq2tQoA)"，把GreatSQL加入系统systemd服务中。

## 4、搭建MGR集群

MGR集群的部署可以自己手动一步步操作，也可通过MySQL Shell快速完成，分别参考下面的文档即可：
- [利用GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/gLaLybt46PqXlV4qWFfyng)
- [InnoDB Cluster+GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/1QUt-rK_5L_UnaLClyve1w)
- [ansible一键安装GreatSQL并构建MGR集群](https://mp.weixin.qq.com/s/8hbpus0RxrVnmCdVDHVg2Q)
- [​在Docker中部署GreatSQL并构建MGR集群](https://mp.weixin.qq.com/s/CfrYEQD54EXD9mLJJPGs-A)

## 延伸阅读
- [玩转MySQL 8.0源码编译](https://mp.weixin.qq.com/s/Lrx-YYYWtHHaxLfY_UZ8GQ)
- [将GreatSQL添加到系统systemd服务](https://mp.weixin.qq.com/s/tSA-DrWT13GN45Csq2tQoA)
- [利用GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/gLaLybt46PqXlV4qWFfyng)
- [InnoDB Cluster+GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/1QUt-rK_5L_UnaLClyve1w)
- [​在Docker中部署GreatSQL并构建MGR集群](https://mp.weixin.qq.com/s/CfrYEQD54EXD9mLJJPGs-A)

全文完。

Enjoy GreatSQL :)
