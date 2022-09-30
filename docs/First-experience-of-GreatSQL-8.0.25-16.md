# First experience of GreatSQL 8.0.25-16

> Experience the new features of greatsql 8.0.25-16.

In the newly released greatsql 8.0.25-16, there are four new features:

- New arbitration node (voting node) role
- New fast single mode
- New Mgr network overhead threshold
- Custom selection mode

In this article, we will experience these new features.

## 1. Preparation
This paper uses CentOS 8.4 environment to demonstrate.
```
[root@c8 ~] # cat /etc/redhat-release
 CentOS Linux release 8.4.2105

 [root@c8 ~] # uname -a
 Linux c8 4.18.0-305.19.1.el8_4.x86_64  #1 SMP Wed Sep 15 15:39:39 UTC 2021 x86_ 64 x86_ 64 x86_ 64 GNU/Linux
```

### 1.1 Download RPM package
It is recommended to install greatsql in RPM mode, which is simple and convenient.

Open link https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-16 Download the greatsql 8.0.25-16 package because it is CentOS 8.4 x86_ 64, so download el8 * x86_ Several PRM packages with 64 characters:

```
greatsql-client-8.0.25-16.1.el8.x86_ 64.rpm
greatsql-devel-8.0.25-16.1.el8.x86_ 64.rpm
greatsql-server-8.0.25-16.1.el8.x86_ 64.rpm
greatsql-shared-8.0.25-16.1.el8.x86_ 64.rpm
```

### 1.2 prepare Yum source

Before installation, it is recommended to configure the yum source to facilitate the installation of some tools. Take Alibaba cloud's Yum source as an example:
```
[root@c8 ~] # cd /etc/yum.repos.d
[root@c8 ~] # rm -f CentOS-Base.repo CentOS-Linux-AppStream.repo CentOS-Linux-BaseOS.repo
[root@c8 ~] # curl -o /etc/yum.repos.d/CentOS-Base.repo  https://mirrors.aliyun.com/repo/Centos-vault-8.5.2111.repo
[root@c8 ~] # sed -i -e '/mirrors.cloud.aliyuncs.com/d' -e '/mirrors.aliyuncs.com/d' /etc/yum.repos.d/CentOS-Base.repo
[root@c8 ~] # yum clean all ;  yum makecache
```

## 2. Initialization installation

The Mgr cluster is planned to be deployed on the following three servers:
```
node	ip	datadir	port	role
mgr1	172.16.16.10	/data/GreatSQL/	three thousand three hundred and six	PRIMARY
mgr2	172.16.16.11	/data/GreatSQL/	three thousand three hundred and six	SECONDARY
mgr3	172.16.16.12	/data/GreatSQL/	three thousand three hundred and six	ARBITRATOR
```

2.1 install RPM package on each node

Install the RPM package on the three nodes respectively. The first installation may report some dependency failures:
```
[root@c8 ~] # rpm -ivh greatsql-*rpm
 error: Failed dependencies:
         /usr/bin/pkg-config is needed by greatsql-devel-8.0.25-16.1.el8.x86_sixty-four
         pkgconfig(openssl) is needed by greatsql-devel-8.0.25-16.1.el8.x86_sixty-four
         /usr/bin/perl is needed by greatsql-server-8.0.25-16.1.el8.x86_sixty-four
         libaio.so.1()(64bit) is needed by greatsql-server-8.0.25-16.1.el8.x86_sixty-four
         libaio.so.1(LIBAIO_0.1)(64bit) is needed by greatsql-server-8.0.25-16.1.el8.x86_sixty-four
         libaio.so.1(LIBAIO_0.4)(64bit) is needed by greatsql-server-8.0.25-16.1.el8.x86_sixty-four
         libnuma.so.1()(64bit) is needed by greatsql-server-8.0.25-16.1.el8.x86_sixty-four
         libnuma.so.1(libnuma_1.1)(64bit) is needed by greatsql-server-8.0.25-16.1.el8.x86_sixty-four
         libnuma.so.1(libnuma_1.2)(64bit) is needed by greatsql-server-8.0.25-16.1.el8.x86_sixty-four
         net-tools is needed by greatsql-server-8.0.25-16.1.el8.x86_sixty-four
         openssl is needed by greatsql-server-8.0.25-16.1.el8.x86_sixty-four
```

According to the prompt, just install the corresponding dependency package with yum

```
[root@c8 ~] # yum install -y openssl-libs libaio numactl-libs net-tools perl openssl openssl-devel pkgconf-pkg-config pkgconfig
```

In addition, it is recommended to manually download and install the jemalloc 5.2.1 + installation package. Download address: https://centos.pkgs.org/8/epel-x86_64/jemalloc-5.2.1-2.el8.x86_64.rpm.html 。
```
[root@c8 ~] # rpm -ivh jemalloc-5.2.1-2.el8.x86_ 64.rpm
```

After these dependency packages are installed, try to install the greatsql RPM package again:
```
[root@c8 ~] # rpm -ivh greatsql-*rpm
 Verifying...                           ################################# [100%]
 Preparing...                           ################################# [100%]
 Updating / installing...
    1:greatsql-shared-8.0.25-16.1.el8   ################################# [ 25%]
    2:greatsql-client-8.0.25-16.1.el8   ################################# [ 50%]
    3:greatsql-server-8.0.25-16.1.el8   ################################# [ 75%]
    4:greatsql-devel-8.0.25-16.1.el8    ################################# [100%]
```
This completes the installation.

Because it is installed in RPM mode, there is no need to create the user & group MySQL: MySQL.

### 2.2 initializing the primary node
First, the initialization is performed on the mgr1 server, which acts as the primary node, and some configurations need to be distinguished from other nodes.

Edit global profile /etc/my.cnf Please refer to my In addition to the following options, you only need to change the template values from the SQL for primary to cnoff.16
```
# loose-group_ replication_ bootstrap_ group = OFF
loose-group_replication_bootstrap_group = ON   #This is the primary node
``` 

New database main directory /data/GreatSQL (refer to the dataDir option value setting in / etc / my.cnf), and modify the user owner:
```
[root@c8 ~] # mkdir -p /data/GreatSQL
[root@c8 ~] # chown -R mysql:mysql /data/GreatSQL/
```

Execute the following command again:
```
[root@c8 ~] # cd /data/GreatSQL
 [root@c8 ~] # systemctl start mysqld
 [root@c8 ~] # ls
  auto.cnf        ca.pem            '#ib_ 16384_ 0.dblwr'   ib_logfile1             mysql             performance_schema   slow.log
  binlog.000001   client-cert.pem   '#ib_ 16384_ 1.dblwr'   ib_logfile2             mysql.ibd         private_key.pem      sys
  binlog.000002   client-key.pem    ib_buffer_pool       ibtmp1                  mysql.pid         public_key.pem       undo_001
  binlog.index    error.log         ibdata1              innodb_status.1322376   mysql.sock        server-cert.pem      undo_002
  ca-key.pem      GCS_DEBUG_TRACE   ib_logfile0          '#innodb_ temp'           mysql.sock.lock   server-key.pem
```
This completes the installation and instance initialization.

When the MySQL account is initialized, the MySQL account will be automatically generated for the first time
```
[root@c8 GreatSQL] # grep 'password.*root' error.log
 [Note] [MY-010454] [Server] A temporary password is generated  for root@localhost: AvBv.ftg2,T&
Copy the last password string to log in to MySQL

[root@c8 ~] # mysql -uroot -p
 Paste the above password here
 Welcome to the MySQL monitor.  Commands end with ; or \g.
 Your MySQL connection id is 8
 Server version: 8.0.25-16

 Copyright (c) 2021-2021 GreatDB Software Co., Ltd
 Copyright (c) 2009-2021 Percona LLC and/or its affiliates
 Copyright (c) 2000, 2021, Oracle and/or its affiliates.

 Oracle is a registered trademark of Oracle Corporation and/or its
 affiliates. Other names may be trademarks of their respective
 owners.

 Type  'help;' or  '\h'  for  help. Type  '\c' to clear the current input statement.

 #After the first login, you will be reminded to change your password
 [root@GreatSQL][(none)]>\s
 ERROR 1820 (HY000): You must reset your password using ALTER USER statement before executing this statement.

 #Change password
 [root@GreatSQL][(none)]> ALTER USER USER() IDENTIFIED BY  'GreatSQL-3306';

 #View version number
 [root@GreatSQL][(none)]> \s
 ...
 Server version:  8.0.25-16 GreatSQL (GPL), Release 16, Revision 8bb0e5af297
 ...
``` 
This starts the greatsql service on the primary node and completes the initialization of the database instance.

### 2.3 initializing secondary and arbitrator nodes

Reference resources 2.2 initializing the primary node Method, continue to initialize the secondary and arbitrator nodes.

For the secondary node, edit the global configuration file /etc/my.cnf Basically, you can refer to my directly cnf for GreatSQL 8.0.25-16( https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example-greatsql-8.0.25-16 ）Configure the document template, modify the file directory and memory related options, and do not need to adjust the rest.

The same is true for the arbitrator node. In addition to modifying the file directory and memory related options, you only need to modify the following line of option values:
```
 # loose-group_ replication_ arbitrator = 0
 loose-group_replication_This node is set to < 1
``` 
The revision is complete /etc/my.cnf After that, the same will be done systemctl start mysqld To complete the initialization of the greatsql instance.

## 3. Build Mgr cluster
It is strongly recommended to use MySQL shell to build and deploy Mgr cluster.

Due to the addition of the arbitrator role in greatsql 8.0.25-16, the official MySQL shell cannot identify the support, so we need to use the MySQL shell version we provide. Download link https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-16 In the context of this article greatsql-shell-8.0.25-16-Linux-glibc2.28-x86_ 64.tar.xz Download this package.

To run MySQL shell 8.0.25-16, you need to rely on the development package of Python version 3.8. Therefore, you must first install:
```
[root@c8 ~] # yum install -y python38-devel
Then follow the xx You can build the Mgr cluster according to the steps in, which will not be discussed here.

After the construction is completed, you can see the status of each node in the MySQL shell, for example:

 MySQL  172.16.16.10:33060+ ssl  Py > c.status()

          "primary":  "172.16.16.10:3306",
          "ssl":  "REQUIRED",
          "status":  "OK",
          "statusText":  "Cluster is ONLINE and can tolerate up to ONE failure.",
          "topology": {
              "172.16.16.10:3306": {
                  "address":  "172.16.16.10:3306",
                  "memberRole":  "PRIMARY",
                  "mode":  "R/W",
                  "readReplicas": {},
                  "replicationLag": null,
                  "role":  "HA",
                  "status":  "ONLINE",
                  "version":  "8.0.25"
             },
              "172.16.16.11:3306": {
                  "address":  "172.16.16.11:3306",
                  "memberRole":  "SECONDARY",
                  "mode":  "R/O",
                  "readReplicas": {},
                  "replicationLag": null,
                  "role":  "HA",
                  "status":  "ONLINE",
                  "version":  "8.0.25"
             },
              "172.16.16.12:3306": {
                  "address":  "172.16.16.12:3306",
                  "memberRole":  "ARBITRATOR",
                  "mode":  "R/O",
                  "readReplicas": {},
                  "replicationLag": null,
                  "role":  "HA",
                  "status":  "ONLINE",
                  "version":  "8.0.25"
             }
         },
          "topologyMode":  "Single-Primary"
     },
      "groupInformationSourceMember":  "172.16.16.10:3306"
```

The data of the new role of arbin3 is not visible to users
```
$ mysqlshow
 +-------------------------------+
 |           Databases           |
 +-------------------------------+
 | information_schema            |
 | mysql                         |
 | mysql_innodb_cluster_metadata |
 | performance_schema            |
 | sys                           |
 +-------------------------------+
 $ ls -la binlog.*
 -rw-r----- 1 mysql mysql 179 May 13 08:08 binlog.000001
 -rw-r----- 1 mysql mysql 156 May 13 08:08 binlog.000002
 -rw-r----- 1 mysql mysql  58 May 13 08:08 binlog.index
```

On the other nodes:
```
$ mysqlshow+-------------------------------+
 |           Databases           |
 +-------------------------------+
 | information_schema            |
 | mysql                         |
 | mysql_innodb_cluster_metadata |
 | performance_schema            |
 | sbtest                        |
 | sys                           |
 +-------------------------------+

 $ ls -la binlog.*
 -rw-r----- 1 mysql mysql     179 May 13 08:05 binlog.000001
 -rw-r----- 1 mysql mysql 3848416 May 14 02:02 binlog.000002
 -rw-r----- 1 mysql mysql      58 May 13 08:06 binlog.index
```
If the binlog / binlog node does not participate in the arbitration, it only stores the state.

If some transactions spend more time in the Mgr layer than the threshold, a log similar to the following will be recorded:

> [Note] Plugin group_replication reported:  'MGR request time:130808us, id:330606, thread_ id:17368'

It indicates that the network overhead of this transaction at Mgr layer took 130808 microseconds (130.808 MS), and then check the network monitoring of that period to analyze the reasons for the high network delay.

Two other new features Single master mode fast (single primary fast mode) and Custom selector We'll leave it for later.
