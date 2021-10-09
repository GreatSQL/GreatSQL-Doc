# Compile and install GreatSQL with source code under Linux

## 0、Outline
In this article we will introduce how to compile GreatSQL with source code, and make binary packages, RPM packages, etc.

We compile source code with CentOS 7.9:
```
[root@greatsql ~]# cat /etc/redhat-release
CentOS Linux release 7.9.2009 (Core)

[root@greatsql ~]# uname -a
Linux greatsql 3.10.0-1160.11.1.el7.x86_64 #1 SMP Fri Dec 18 16:34:56 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
```

## 1. Preparation
### 1.1, configure yum
It is recommended to configure the yum source first for the installation of some tools.

Take the two major cloud in China of Alibaba and Tencent as examples, you can configure it like this (choose one of the two yum sources):
```
[root@greatsql ~]# mv /etc/yum.repos.d/CentOS-Base.repo{,.orig}

#Alibaba Cloud
[root@greatsql ~]# wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo

# Tencent Cloud
[root@greatsql ~]# wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.cloud.tencent.com/repo/centos7_base.repo

#And then update yum cache
[root@greatsql ~]# yum clean all
[root@greatsql ~]# yum makecache
```
### 1.2, install docker
Install docker and start the docker server.
```
[root@greatsql]# yum install -y docker
[root@greatsql]# systemctl start docker
```

### 1.3, download a few necessary installation packages in advance
Download several dependency packages that are needed during the compilation process:
- boost, https://boostorg.jfrog.io/artifactory/main/release/1.73.0/source/boost_1_73_0.tar.gz
- git, https://github.com/git/git/archive/v2.27.0.tar.gz, renamed to git-v2.27.0.tar.gz after downloading
- patchelf, https://github.com/NixOS/patchelf/archive/refs/tags/0.12.tar.gz, renamed to patchelf-0.12.tar.gz after downloading
- rpcsvc-proto, https://github.com/thkukuk/rpcsvc-proto/releases/download/v1.4/rpcsvc-proto-1.4.tar.gz

Download the GreatSQL source code package:
```
git clone https://github.com/GreatSQL/GreatSQL.git
``` 

### 1.4, build docker image
Use the following Dockerfile to build an image, here is CentOS 7 as an example:
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
RUN echo'scl enable devtoolset-10 bash' >> /root/.bash_profile

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

Start to build the docker image, save it locally and import the local image after success:
```
[root@greatsql ~]# docker build -t centos7-greatsql.
... ...
[root@greatsql ~]# docker save -o centos7-greatsql.tar centos7-greatsql
[root@greatsql ~]# docker load -i centos7-greatsql.tar
```

Create a docker container and copy the GreatSQL source code package into it:
```
[root@greatsql ~]# docker run -itd --name greatsql --hostname=greatsql centos7-greatsql bash
[root@greatsql ~]# docker cp /opt/greatsql-8.0.25-15.tar.gz greatsql:/opt/
[root@greatsql ~]# docker exec -it greatsql bash
[root@greatsql /]# ls -l /opt/
-rw------- 1 root root 128699082 Jul 27 06:56 boost_1_73_0.tar.gz
drwxr-xr-x 5 root root 4096 Jul 28 06:38 git
-rw------- 1 1000 1000 526639994 Jul 27 05:59 greatsql-8.0.25-15.tar.gz
drwxr-xr-x 3 root root 4096 Jul 28 06:34 rh
```

## 2. Compile GreatSQL
After entering the container, decompress the GreatSQL and boost packages:
```
[root@greatsql /]# tar zxf /opt/greatsql-8.0.25-15.tar.gz -C /opt
[root@greatsql /]# tar zxf /opt/boost_1_73_0.tar.gz -C /opt/greatsql-8.0.25-15/
```

### 2.1, only compile binary files
If you just want to compile the binary file, without packaging or making RPM packages. Use the following command to compile:
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

If the cmake process does not report an error, it will output a result similar to the following:
```
... ...
- Build files have been written to: /opt/greatsql-8.0.25-15
```

Then you can start the compilation:
```
[root@greatsql ~]# make -j30 VERBOSE=1 && make install
```

The parameter *-j30* is set to the number of logical CPUs to be compiled in parallel. It can be specified as a bit less than the total number of logical CPUs. Don't run up all the CPUs.

After the compilation is complete, the binary files will be installed in the */usr/local/GreatSQL-8.0.25-15-Linux.x86_64* directory.

### 2.2. Compile and package into a binary tarball or RPM package
If you want to copy to other servers after compilation, you can also generate a binary package or RPM package, you can use the following command to compile:
```
[root@greatsql ~]# cd /opt/greatsql-8.0.25-15/build-gs/
[root@greatsql ~]# export your_processors=30 # Same as above, modify the number of parallel CPUs
[root@greatsql ~]# export TAR_PROCESSORS=-T$your_processors
[root@greatsql ~]# export MAKE_JFLAG=-j$your_processors
[root@greatsql ~]# mkdir -p workdir
[root@greatsql ~]# cp /opt/boost_1_73_0.tar.gz /opt/greatsql-8.0.25-15/build-gs/
[root@greatsql ~]# cp /opt/greatsql-8.0.25-15.tar.gz /opt/greatsql-8.0.25-15/build-gs/workdir/

# Option 1: Compile and package into a binary package
[root@greatsql ~]# bash -xe ./percona-server-8.0_builder.sh --builddir=`pwd`/workdir --get_sources=0 --install_deps=0 --with_ssl=1 --build_tarball=1- -build_src_rpm=0 --build_rpm=0 --no_git_info=1 --local_boost=1

# Option 2: Compile and package into RPM package
[root@greatsql ~]# bash -xe ./percona-server-8.0_builder.sh --builddir=`pwd`/workdir --get_sources=0 --install_deps=0 --with_ssl=1 --build_tarball=0- -build_src_rpm=1 --build_rpm=1 --no_git_info=1 --local_boost=1
```

During the compilation process, if you encounter a patchelf error similar to the following:
```
+ patchelf --replace-needed libreadline.so.7 libreadline.so bin/mysql
patchelf: cannot normalize PT_NOTE segment: non-contiguous SHT_NOTE sections
```

You can refer to this patch: [patchelf: Fix alignment issues with contiguous note sections #275](https://github.com/NixOS/patchelf/pull/275/files), modify the source code, and recompile patchelf manually in the container.

After compilation, the corresponding binary package and RPM package will be generated in the */opt/greatsql-8.0.25-15/build-gs/workdir/* directory:
```
[root@greatsql build-gs]# du -sh workdir/TARGET/
40M workdir/TARGET/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal.tar.xz
500M workdir/TARGET/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64.tar.xz

[root@greatsql build-gs]# du -sh workdir/rpm/greatsql-*
14M workdir/rpm/greatsql-client-8.0.25-15.1.el8.x86_64.rpm
30M workdir/rpm/greatsql-client-debuginfo-8.0.25-15.1.el8.x86_64.rpm
3.4M workdir/rpm/greatsql-debuginfo-8.0.25-15.1.el8.x86_64.rpm
23M workdir/rpm/greatsql-debugsource-8.0.25-15.1.el8.x86_64.rpm
2.1M workdir/rpm/greatsql-devel-8.0.25-15.1.el8.x86_64.rpm
4.6M workdir/rpm/greatsql-mysql-router-8.0.25-15.1.el8.x86_64.rpm
27M workdir/rpm/greatsql-mysql-router-debuginfo-8.0.25-15.1.el8.x86_64.rpm
13M workdir/rpm/greatsql-rocksdb-8.0.25-15.1.el8.x86_64.rpm
204M workdir/rpm/greatsql-rocksdb-debuginfo-8.0.25-15.1.el8.x86_64.rpm
60M workdir/rpm/greatsql-server-8.0.25-15.1.el8.x86_64.rpm
343M workdir/rpm/greatsql-server-debuginfo-8.0.25-15.1.el8.x86_64.rpm
1.4M workdir/rpm/greatsql-shared-8.0.25-15.1.el8.x86_64.rpm
2.5M workdir/rpm/greatsql-shared-debuginfo-8.0.25-15.1.el8.x86_64.rpm
440M workdir/rpm/greatsql-test-8.0.25-15.1.el8.x86_64.rpm
18M workdir/rpm/greatsql-test-debuginfo-8.0.25-15.1.el8.x86_64.rpm
```
This can be used to copy to other servers for installation and use.

## 3. Initialize GreatSQL
We planned to deploy the MGR cluster on the following three servers:

| node | ip | datadir | port |role|
| --- | --- | --- | --- | --- |
| nodeA| 172.16.16.10 | /data/GreatSQL/ | 3306 | PRIMARY |
| nodeB| 172.16.16.11 | /data/GreatSQL/ | 3306 | SECONDARY |
| nodeC| 172.16.16.12 | /data/GreatSQL/ | 3306 | SECONDARY |

Perform the following initialization work on the nodeA server firstly, and do the same work for the other two servers.

First edit the `/etc/my.cnf` configuration file, you can refer to the following configuration variables:

```
#my.cnf
[mysqld]
user = mysql
port = 3306
#Master-slave replication or MGR cluster, remember to be different server_id
#In addition, auto.cnf will be generated when the instance is started, and the value of server_uuid inside will also be different
The value of #server_uuid can also be manually specified by yourself, as long as it meets the format standard of uuid.
server_id = 3306
basedir=/usr/local/GreatSQL-8.0.25-15-Linux.x86_64
datadir = /data/GreatSQL
socket = /data/GreatSQL/mysql.sock
pid-file = mysql.pid
character-set-server = UTF8MB4
skip_name_resolve = 1
#If your MySQL database is mainly running overseas, please be sure to adjust this parameter according to the actual situation
default_time_zone = "+8:00"

#performance setttings
lock_wait_timeout = 3600
open_files_limit = 65535
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
#MySQL Before 8.0.22, if you want to enable MGR, you need to set binlog_checksum=NONE
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
#Can be set to 2 times the number of logical CPUs
slave_parallel_workers = 64
binlog_transaction_dependency_tracking = WRITESET
slave_preserve_commit_order = 1
slave_checkpoint_period = 2

#mgr settings
loose-plugin_load_add ='mysql_clone.so'
loose-plugin_load_add ='group_replication.so'
loose-group_replication_group_name = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"
#MGR Local node IP:PORT, please replace by yourself
loose-group_replication_local_address = "172.16.16.10:33061"
#MGR All nodes in the cluster IP:PORT, please replace by yourself
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
# Adjust appropriately according to your server IOPS capability
# Generally equipped with ordinary SSD disk, it can be adjusted to 10000-20000
# If you configure a high-end PCIe SSD card, it can be adjusted higher, such as 50000-80000
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
#Note: After opening innodb_status_output & innodb_status_output_locks, it may cause the log_error file to grow faster
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
#performance_schema_instrument ='%memory%=on'
performance_schema_instrument ='%lock%=on'
```

Execute the following command to initialize:
```
[root@greatsql ~]# /usr/local/GreatSQL-8.0.25-15-Linux.x86_64/bin/mysqld --defaults-file=/etc/my.cnf --initialize-insecure
```

There are two options for initialization: `--initialize` and `--initialize-insecure`. The former will generate a random password for the root account, while the latter will not. We choose the latter. but **In the production environment, please be sure to set a secure password for the root user**.

Then you can start the mysqld process:
```
[root@greatsql ~]# /usr/local/GreatSQL-8.0.25-15-Linux.x86_64/bin/mysqld --defaults-file=/etc/my.cnf &
```

GreatSQL is a branch of Percona Server. The jemalloc library is required by default. If an error similar to the following is reported during startup, you need to install jemalloc or libaio and other related software packages:
```
/usr/local/GreatSQL-8.0.23-14/bin/mysqld: error while loading shared libraries: libjemalloc.so.1: cannot open shared object file: No such file or directory
```

Simply install the libjemalloc library:
```
[root@greatsql ~]# yum install -y jemalloc jemalloc-devel
```

If you want to stop the mysqld process, execute the following command:
```
# Assuming that root is still an empty password at this time
[root@greatsql ~]# /usr/local/GreatSQL-8.0.25-15-Linux.x86_64/bin/mysql -uroot -S/data/GreatSQL/mysql.sock shutdown
```

Check version number:
```
root@GreatSQL [(none)]> \s
...
Server version: 8.0.25-15 GreatSQL, Release 15, Revision 80bbf22abbd
...
```

In the same way, complete the initialization and startup of GreatSQL on the other two servers, and then start to build the MGR cluster.

In addition, you can also refer to this guide "[Add GreatSQL to the system systemd service](https://mp.weixin.qq.com/s/tSA-DrWT13GN45Csq2tQoA)" to add GreatSQL to the system systemd service.

## 4. Build MGR cluster

The deployment of the MGR cluster can be done manually step by step, or it can be quickly completed through MySQL Shell. Refer to the following documents respectively:
- [Deploy MGR cluster using GreatSQL](https://mp.weixin.qq.com/s/gLaLybt46PqXlV4qWFfyng)
- [InnoDB Cluster+GreatSQL deployment MGR cluster](https://mp.weixin.qq.com/s/1QUt-rK_5L_UnaLClyve1w)
- [ansible one-click installation of GreatSQL and build MGR cluster](https://mp.weixin.qq.com/s/8hbpus0RxrVnmCdVDHVg2Q)
- [​Deploy GreatSQL in Docker and build MGR cluster](https://mp.weixin.qq.com/s/CfrYEQD54EXD9mLJJPGs-A)

## Further reading
- [Fun with MySQL 8.0 source code compilation](https://mp.weixin.qq.com/s/Lrx-YYYWtHHaxLfY_UZ8GQ)
- [Add GreatSQL to the system systemd service](https://mp.weixin.qq.com/s/tSA-DrWT13GN45Csq2tQoA)
- [Deploy MGR cluster using GreatSQL](https://mp.weixin.qq.com/s/gLaLybt46PqXlV4qWFfyng)
- [InnoDB Cluster+GreatSQL deployment MGR cluster](https://mp.weixin.qq.com/s/1QUt-rK_5L_UnaLClyve1w)
- [​Deploy GreatSQL in Docker and build MGR cluster](https://mp.weixin.qq.com/s/CfrYEQD54EXD9mLJJPGs-A)

Enjoy GreatSQL :)
