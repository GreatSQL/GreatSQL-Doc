## 0. 内容提纲

[toc]

MySQL InnoDB Cluster（简称MIC）是MySQL推出的整套解决方案，由几个部分组成：
- MySQL Server，核心是Group Replication（组复制），简称MGR。
- MySQL Shell，可编程的高级客户端，支持标准SQL语法、JavaScript语法、Python语法，以及API接口，可以更方便的管理和使用MySQL服务器。
- MySQL Router，轻量级中间件，支持透明路由规则（读写分离及读负载均衡）。

本文详细介绍如何利用MIC和GreatSQL构建MGR集群，并结合MySQL Router实现读写分离、读负载均衡以及故障自动转移架构。

为了简单起见，这个MGR集群采用单主（single-primary）模式，不采用多主（multi-primary）模式。

整体系统架构如下图所示：
![输入图片说明](https://images.gitee.com/uploads/images/2021/0623/172104_653e92d0_8779455.png "屏幕截图.png")

## 1. 部署环境及初始化

为了简单起见，建议用yum方式标准化安装MySQL Shell、Router以及社区版。

如果还没MySQL官方的yum源，需要先下载安装repo包，下载地址：
```
https://dev.mysql.com/downloads/repo/yum/
```
选择正确对应OS的版本下载并安装即可，例如：
```
[root@greatsql]# yum -y install https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm
```
之后就可以用yum安装MySQL相关的软件包了。
```
[root@greatsql]# yum install -y mysql-shell mysql-router mysql-community-server
```

除了MySQL官方社区版本外，如果想体验更可靠、稳定、高效的MGR，推荐使用GreatSQL版本。本文采用GreatSQL 8.0.22版本，关于这个版本的说明详见 [GreatSQL，打造更好的MGR生态](https://mp.weixin.qq.com/s/ByAjPOwHIwEPFtwC5jA28Q)。

GreatSQL二进制包放在 /usr/local/ 下，即 basedir = /usr/local/GreatSQL-8.0.22。

MGR集群由三个实例构成，按下面规划分配：

| 实例	| IP | 端口	| datadir
| --- |--- |--- |--- |
|GreatSQL-01|172.16.16.10|3306|/data/GreatSQL/
|GreatSQL-02|172.16.16.11|3306|/data/GreatSQL/
|GreatSQL-03|172.16.16.12|3306|/data/GreatSQL/

另外，为了mysqld服务管理方便，我直接修改系统systemd里关于mysqld服务的配置文件约第52行：
```
[root@greatsql]# vim /usr/lib/systemd/system/mysqld.service +52
...
ExecStart=/usr/local/GreatSQL-8.0.22/bin/mysqld $MYSQLD_OPTS
#ExecStart=/usr/sbin/mysqld $MYSQLD_OPTS
```
修改完，保存退出，执行下面的命令让systemd重新加载配置文件：
```
[root@greatsql]# systemctl daemon-reload
```
这样就可以利用systemd来管理mysqld服务了。
```
[root@greatsql]# systemctl start/stop/status/restart mysqld.service
```

由于 `/usr/bin/mysqld_pre_systemd` 中需要调用 `/usr/sbin/mysqld` 二进制文件，因此这个也要替换掉：
```
#yum安装的做个备份
[root@greatsql]# mv /usr/sbin/mysqld /usr/sbin/mysqld-8.0.25

#做个软链替换
[root@greatsql]# ln -s /usr/local/GreatSQL-8.0.22/bin/mysqld /usr/sbin/mysqld
```

为了能让mysqld改用jemalloc，也同时编辑文件：
```
[root@greatsql]# vim /etc/sysconfig/mysql
LD_PRELOAD=/usr/lib64/libjemalloc.so.1
```

这是一份配置参考（可自行根据实际情况适当调整）：
```
[mysqld]
basedir=/usr/local/GreatSQL-8.0.22
datadir=/data/GreatSQL
socket=/data/GreatSQL/mysql.sock
log_timestamps=SYSTEM
user = mysql
log_error_verbosity = 3
log-error=/data/GreatSQL/error.log
port=3306
server_id=3310

log-bin=binlog
binlog-format=row
log_slave_updates=ON
binlog_checksum=CRC32

master-info-repository=TABLE
relay-log-info-repository=TABLE
gtid-mode=on
enforce-gtid-consistency=true
binlog_transaction_dependency_tracking=writeset
transaction_write_set_extraction=XXHASH64
slave_parallel_type = LOGICAL_CLOCK
slave_parallel_workers=128 #可以设置为逻辑CPU数量的2-4倍
sql_require_primary_key=1
slave_preserve_commit_order=1
slave_checkpoint_period=2

#mgr
loose-plugin_load_add='mysql_clone.so'
loose-plugin_load_add='group_replication.so'

#所有节点的group_replication_group_name值必须相同
#这是一个标准的UUID格式，可以手动指定，也可以用随机生成的UUID
loose-group_replication_group_name="fbc510f0-c5ba-11eb-bfaf-5254002eb6d6"

#指定本节点的IP+端口
loose-group_replication_local_address= "172.16.16.10:33061"

#指定MGR集群各节点的IP+端口，这个端口是专用于MGR的，不是平常所说的mysqld实例端口
#如果是在多节点上部署MGR集群时，要注意这个端口是否会被防火墙拦截
loose-group_replication_group_seeds= "172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061"

#不建议启动mysqld的同时也启动MGR服务
loose-group_replication_start_on_boot=off

#默认不要作为MGR集群引导节点，有需要时再手动执行并立即改回OFF状态
loose-group_replication_bootstrap_group=off

#当退出MGR后，把该实例设置为read_only，避免误操作写入数据
loose-group_replication_exit_state_action=READ_ONLY

#一般没什么必要开启流控机制
loose-group_replication_flow_control_mode = "DISABLED"

#【强烈】建议只用单主模式，如果是实验目的，可以尝试玩玩多主模式
loose-group_replication_single_primary_mode=ON
```

最后直接启动mysqld服务即可（首次启动会自行完成初始化）：
```
[root@greatsql]# systemctl start mysqld.service
```

初始化时会为root账号生成一个临时密码，例如这样的：
```
[Note] [MY-010454] [Server] A temporary password is generated for root@localhost: h<GL%Lr:v66W
```

首次用这个密码登入后，就要立即进行修改，否则其他什么也做不了：
```
[root@GreatSQL](none)> ALTER USER CURRENT_USER() IDENTIFIED BY 'GreatSQL-##)^';
```

用同样的方法，完成其他节点的MySQL实例初始化，确认运行的GreatSQL版本号。
```
[root@GreatSQL](none)> \s
...
Server version:		8.0.22-13 Source distribution
```

## 2. 利用MySQL Shell构建MGR集群
利用MySQL Shell构建MGR集群主要简单几个命令就可以了，确实是要比手动方式部署便捷很多。

只需三步就好：
- 检查实例是否满足条件。
- 创建并初始化一个集群。
- 逐个添加实例。

想要使用MySQL Shell构建MGR集群，除了需要先满足MGR的基本要求（必须InnoDB表，且必须要有主键等）之外，还要满足其他几个条件：
- Python版本 >= 2.7。
- 启用PFS（performance_schema）。
- 各节点的server_id要唯一。

接下来就可以开始了。

MySQL实例启动后，利用 `mysqlsh` 这个MySQL Shell客户端工具连接到服务器端：
```
# 第一次先用有管理权限的root账号连接
[root@greatsql]# mysqlsh --uri root@172.16.16.10:3306
Please provide the password for 'root@172.16.16.10:3306':  <-- 提示输入密码
Save password for 'mic@172.16.16.10:3306'? [Y]es/[N]o/Ne[v]er (default No): y  <-- 提示是否存储密码（视各公司安全规则而定，这里为了方便选择了存储密码）
Fetching schema names for autocompletion... Press ^C to stop.
Closing old connection...
Your MySQL connection id is 14
Server version: 8.0.22-13 Source distribution
No default schema selected; type \use <schema> to set one.  <-- 成功连接到服务器端

 MySQL  172.16.16.10:3306 ssl  JS > \s  <-- 查看当前状态，等同于在mysql客户端下执行  \s 命令
MySQL Shell version 8.0.25  <-- mysql shell客户端版本号

Connection Id:                20425
Current schema:
Current user:                 root@GreatSQL-01
SSL:                          Cipher in use: ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2
Using delimiter:              ;
Server version:               8.0.22-13 Source distribution  <-- server端版本号
Protocol version:             Classic 10
Client library:               8.0.25
Connection:                   172.16.16.10 via TCP/IP
TCP port:                     3306
Server characterset:          utf8mb4
Schema characterset:          utf8mb4
Client characterset:          utf8mb4
Conn. characterset:           utf8mb4
Result characterset:          utf8mb4
Compression:                  Disabled
Uptime:                       2 hours 56 min 50.0000 sec

Threads: 8  Questions: 216540  Slow queries: 10563  Opens: 264  Flush tables: 3  Open tables: 183  Queries per second avg: 20.409

#也可以切换到sql命令行模式，执行一条命令
 MySQL  172.16.16.10:3306 ssl  JS > \sql select user();
+------------------------+
| user()                 |
+------------------------+
| root@GreatSQL-01       |
+------------------------+
```

**tips:**
`mysqlsh` 也可以像 `mysql` 客户端那样使用 **pager**：
```
mysqlsh> shell.enablePager();
mysqlsh> shell.options["pager"]="less -i -n -S";
Pager has been set to 'less -i -n -S'.
```

**1、检查实例是否满足安装MGR集群的条件**
接下来，执行 `dba.configureInstance()` 命令开始检查当前实例是否准备好了，可以作为MGR集群的一个节点：
```
#查看该命令的语法、用法
MySQL  172.16.16.10:3306 ssl  JS > \help dba.configureInstance
NAME
      configureInstance - Validates and configures an instance for MySQL InnoDB
                          Cluster usage.

SYNTAX
      dba.configureInstance([instance][, options])

WHERE
      instance: An instance definition.
      options: Additional options for the operation.

RETURNS
      A descriptive text of the operation result.
      ...
      
# 开始配置MIC
MySQL  172.16.16.10:3306 ssl  JS > dba.configureInstance();
Configuring local MySQL instance listening at port 3306 for use in an InnoDB cluster...

This instance reports its own address as GreatSQL-01:3306
Clients and other cluster members will communicate with it through this address by default. If this is not correct, the report_host MySQL system variable should be changed.

#root账号不能运行MGR服务，需要创建新的专用账号
ERROR: User 'root' can only connect from 'localhost'. New account(s) with proper source address specification to allow remote connection from all instances must be created to manage the cluster.

1) Create remotely usable account for 'root' with same grants and password
2) Create a new admin account for InnoDB cluster with minimal required grants
3) Ignore and continue
4) Cancel

Please select an option [1]: 2  #<-- 选择创建最小权限账号
Please provide an account name (e.g: icroot@%) to have it created with the necessary
privileges or leave empty and press Enter to cancel.
Account Name: mic  <-- 账号名
Password for new account: *******  <-- 密码***
Confirm password: *******

#节点初始化完毕
The instance 'GreatSQL-01:3306' is valid to be used in an InnoDB cluster.

#MGR管理账号创建完毕
Cluster admin user 'mic'@'%' created.
The instance 'GreatSQL-01:3306' is already ready to be used in an InnoDB cluster.      
```

上述 `dba.configureInstance()` 方法同样在其他节点上也执行一遍。

**2、创建一个MGR集群**
各节点初始化完毕后，用**mysqlsh**客户端，用新建MGR的管理账号登入PRIMARY节点，准备创建MGR集群：
```
[root@greatsql]# mysqlsh --uri mic@172.16.16.10:3306
Creating a session to 'mic@172.16.16.10:3306'
Please provide the password for 'mic@172.16.16.10:3306': *******
Save password for 'mic@172.16.16.10:3306'? [Y]es/[N]o/Ne[v]er (default No): y
Fetching schema names for autocompletion... Press ^C to stop.
Closing old connection...
Your MySQL connection id is 14
Server version: 8.0.22-13 Source distribution
No default schema selected; type \use <schema> to set one.

#在PRIMARY节点上开始创建MGR集群
# 集群命名为 greatsqlMGR，后面mysqlrouter读取元数据时用得上
MySQL  172.16.16.10:3306 ssl  JS > var mic = dba.createCluster('greatsqlMGR');
A new InnoDB cluster will be created on instance '172.16.16.10:3306'.

Validating instance configuration at 172.16.16.10:3306...

This instance reports its own address as GreatSQL-01:3306

Instance configuration is suitable.
NOTE: Group Replication will communicate with other members using 'GreatSQL-01:33061'. Use the localAddress option to override.

Creating InnoDB cluster 'greatsqlMGR' on 'GreatSQL-01:3306'...

Adding Seed Instance...
Cluster successfully created. Use Cluster.addInstance() to add MySQL instances.
At least 3 instances are needed for the cluster to be able to withstand up to
one server failure.
```

集群已经创建并初始化完毕，接下来就是继续添加其他节点了。

**3、添加其他节点**
可以在PRIMARY节点上直接添加其他节点，也可以用**mysqlsh**客户端登入其他节点执行添加节点操作，这里采用前者：
```
MySQL  172.16.16.10:3306 ssl  JS > mic.addInstance('mic@172.16.16.11:3306');  <-- 添加其他MGR节点
NOTE: The target instance 'GreatSQL-02:3306' has not been pre-provisioned (GTID set is empty). The Shell is unable to decide whether incremental state recovery can correctly provision it.
The safest and most convenient way to provision a new instance is through automatic clone provisioning, which will completely overwrite the state of 'GreatSQL-02:3306' with a physical snapshot from an existing cluster member. To use this method by default, set the 'recoveryMethod' option to 'clone'.

The incremental state recovery may be safely used if you are sure all updates ever executed in the cluster were done with GTIDs enabled, there are no purged transactions and the new instance contains the same GTID set as the cluster or a subset of it. To use this method by default, set the 'recoveryMethod' option to 'incremental'.

#选择恢复模式：克隆/增量恢复/忽略，默认选择克隆
Please select a recovery method [C]lone/[I]ncremental recovery/[A]bort (default Clone):
Validating instance configuration at 172.16.16.11:3306...

This instance reports its own address as GreatSQL-02:3306

Instance configuration is suitable.
NOTE: Group Replication will communicate with other members using 'GreatSQL-02:33061'. Use the localAddress option to override.

A new instance will be added to the InnoDB cluster. Depending on the amount of
data on the cluster this might take from a few seconds to several hours.

Adding instance to the cluster...

Monitoring recovery process of the new cluster member. Press ^C to stop monitoring and let it continue in background.
Clone based state recovery is now in progress.

# 提示在这个过程中需要重启GreatSQL-02节点实例
# 如果无法自动重启，需要手动重启
NOTE: A server restart is expected to happen as part of the clone process. If the
server does not support the RESTART command or does not come back after a
while, you may need to manually start it back.

* Waiting for clone to finish...
#从GreatSQL-01节点克隆数据
NOTE: GreatSQL-02:3306 is being cloned from GreatSQL-01:3306
** Stage DROP DATA: Completed
** Clone Transfer
    FILE COPY  ############################################################  100%  Completed
    PAGE COPY  ############################################################  100%  Completed
    REDO COPY  ############################################################  100%  Completed
    NOTE: GreatSQL-02:3306 is shutting down...

* Waiting for server restart... \   <-- 重启中
* Waiting for server restart... ready   <-- 重启完毕，如果没有加入systemed，则需要自己手工启动
* GreatSQL-02:3306 has restarted, waiting for clone to finish...
** Stage RESTART: Completed
* Clone process has finished: 59.62 MB transferred in about 1 second (~59.62 MB/s)

State recovery already finished for 'GreatSQL-02:3306'

# 新节点 GreatSQL-02:3306 已加入集群
The instance 'GreatSQL-02:3306' was successfully added to the cluster.
```

同样的操作，也在 **GreatSQL-03:3306** 节点上执行一遍，将其加入MGR集群中。

当所有节点都加入MGR集群后，查看集群状态：
```
# 查看线程列表
MySQL  172.16.16.10:3306 ssl  JS > \sql show processlist;
+-------+----------------------------+-------------------+------+---------+-------+--------------------------------------------------------+----------------------------------+-----------+---------------+
| Id    | User                       | Host              | db   | Command | Time  | State                                                  | Info                             | Rows_sent | Rows_examined |
+-------+----------------------------+-------------------+------+---------+-------+--------------------------------------------------------+----------------------------------+-----------+---------------+
|     9 | system user                |                   | NULL | Connect | 19935 | waiting for handler commit                             | Group replication applier module |         0 |             0 |
|    12 | system user                |                   | NULL | Query   |     5 | Slave has read all relay log; waiting for more updates | NULL                             |         0 |             0 |
|    13 | system user                |                   | NULL | Query   |     5 | Waiting for an event from Coordinator                  | NULL                             |         0 |             0 |
|    14 | system user                |                   | NULL | Connect | 19934 | Waiting for an event from Coordinator                  | NULL                             |         0 |             0 |
| 20425 | mic                        | GreatSQL-01:42678 | NULL | Query   |     0 | init                                                   | show processlist                 |         0 |             0 |
| 38381 | mysql_router1_2ya0m3z4582s | GreatSQL-01:54034 | NULL | Sleep   |     1 |                                                        | NULL                             |         4 |             4 |
+-------+----------------------------+-------------------+------+---------+-------+--------------------------------------------------------+----------------------------------+-----------+---------------+

# 查看集群结构
MySQL  172.16.16.10:3306 ssl  JS > mic.describe();
{
    "clusterName": "greatsqlMGR",
    "defaultReplicaSet": {
        "name": "default",
        "topology": [
            {
                "address": "GreatSQL-01:3306",
                "label": "GreatSQL-01:3306",
                "role": "HA"
            },
            {
                "address": "GreatSQL-02:3306",
                "label": "GreatSQL-02:3306",
                "role": "HA"
            },
            {
                "address": "GreatSQL-03:3306",
                "label": "GreatSQL-03:3306",
                "role": "HA"
            }
        ],
        "topologyMode": "Single-Primary"
    }
}

#查看集群详细状态
MySQL  172.16.16.10:3306 ssl  JS > mic.status();
{
    "clusterName": "greatsqlMGR",
    "defaultReplicaSet": {
        "name": "default",
        "primary": "GreatSQL-01:3306",
        "ssl": "REQUIRED",
        "status": "OK",
        "statusText": "Cluster is ONLINE and can tolerate up to ONE failure.",
        "topology": {
            "GreatSQL-01:3306": {
                "address": "GreatSQL-01:3306",
                "memberRole": "PRIMARY",
                "mode": "R/W",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
            "GreatSQL-02:3306": {
                "address": "GreatSQL-02:3306",
                "memberRole": "SECONDARY",
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
...  <-- 其余信息略过
        },
        "topologyMode": "Single-Primary"
    },
    "groupInformationSourceMember": "GreatSQL-02:3306"
}

#或者可以加上 {extended:1} 扩展属性，会打印更多信息
MySQL  172.16.16.10:3306 ssl  JS > mic.status({extended:1});
{
    "clusterName": "greatsqlMGR",
    "defaultReplicaSet": {
        "GRProtocolVersion": "8.0.16",
        "groupName": "fbc510f0-c5ba-11eb-bfaf-5254002eb6d6",
        "groupViewId": "16228692455693206:28",
        "name": "default",
        "primary": "GreatSQL-01:3306",
        "ssl": "REQUIRED",
        "status": "OK",
        "statusText": "Cluster is ONLINE and can tolerate up to ONE failure.",
        "topology": {
            "GreatSQL-01:3306": {
                "address": "GreatSQL-01:3306",
                "applierWorkerThreads": 2,
                "fenceSysVars": [],
                "memberId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1",
                "memberRole": "PRIMARY",
                "memberState": "ONLINE",
                "mode": "R/W",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
            "GreatSQL-02:3306": {
                "address": "GreatSQL-02:3306",
                "applierWorkerThreads": 2,
                "fenceSysVars": [
                    "read_only",
                    "super_read_only"
                ],
                "memberId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2",
                "memberRole": "SECONDARY",
                "memberState": "ONLINE",
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
           ...  <-- 其余信息略过
        },
        "topologyMode": "Single-Primary"
    },
    "groupInformationSourceMember": "GreatSQL-01:3306",
    "metadataServer": "GreatSQL-01:3306",
    "metadataVersion": "2.0.0"
}

#也可以用SQL命令行方式查看
MySQL  172.16.16.10:3306 ssl  JS >  \sql select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1 | GreatSQL-01 |        3306 | ONLINE       | PRIMARY     | 8.0.22         |
| group_replication_applier | bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2 | GreatSQL-02 |        3306 | ONLINE       | SECONDARY   | 8.0.22         |
| group_replication_applier | bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb3 | GreatSQL-03 |        3306 | ONLINE       | SECONDARY   | 8.0.22         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
```

到这里，利用MySQL Shell就轻松构建一个三节点的MGR集群了。

## 3. 对在线的MGR集群添加一个新节点
上面的MGR集群已经上线了，现在想添加一个新节点 **GreatSQL-04:3306**，步骤和上面基本上一样，三步走：
- 用有管理权限的账号登入MySQL实例（用**mysqlsh**客户端）。
- 执行 `dba.configureInstance()` 函数预处理。
- 执行 `cluster.addInstance()` 函数加入集群。

详细过程就不赘述了，自行操作。

如果是想删除一个节点，则改成执行 `cluster.removeInstance()` 函数即可。

## 4. 部署MySQL Router，实现读写分离以及故障自动转移
MySQL Router是一个轻量级的中间件，它采用多端口的方案实现读写分离以及读负载均衡，而且同时支持mysql和mysql x协议。

**1、mysqlrouter初始化**
MySQL Router对应的服务器端程序文件是 `/usr/bin/mysqlrouter`，第一次启动时要先进行初始化：
```
#
#参数解释
# 参数 --bootstrap 表示开始初始化
# 参数 mic@172.16.16.10:3306 是MGR集群管理员账号
# --user=mysqlrouter 是运行mysqlrouter进程的系统用户名
#
[root@greatsql]# mysqlrouter --bootstrap mic@172.16.16.10:3306 --user=mysqlrouter
Please enter MySQL password for mic:   <-- 输入密码
# 然后mysqlrouter开始自动进行初始化
# 它会自动读取MGR的元数据信息，自动生成配置文件
# Reconfiguring system MySQL Router instance...

- Fetching password for current account (mysql_router1_2ya0m3z4582s) from keyring
- Creating account(s) (only those that are needed, if any)
- Using existing certificates from the '/var/lib/mysqlrouter' directory
- Verifying account (using it to run SQL queries that would be run by Router)
- Storing account in keyring
- Adjusting permissions of generated files
- Creating configuration /etc/mysqlrouter/mysqlrouter.conf

Existing configuration backed up to '/etc/mysqlrouter/mysqlrouter.conf.bak'

# MySQL Router configured for the InnoDB Cluster 'greatsqlMGR'

After this MySQL Router has been started with the generated configuration

    $ /etc/init.d/mysqlrouter restart
or
    $ systemctl start mysqlrouter
or
    $ mysqlrouter -c /etc/mysqlrouter/mysqlrouter.conf

the cluster 'greatsqlMGR' can be reached by connecting to:

## MySQL Classic protocol  <-- MySQL协议的两个端口

- Read/Write Connections: localhost:6446
- Read/Only Connections:  localhost:6447

## MySQL X protocol  <-- MySQL X协议的两个端口

- Read/Write Connections: localhost:6448
- Read/Only Connections:  localhost:6449
```

**2、启动mysqlrouter服务**
这就初始化完毕了，按照上面的提示，直接启动 **mysqlrouter** 服务即可：
```
[root@greatsql]# systemctl start mysqlrouter

[root@greatsql]# ps -ef | grep -v grep | grep mysqlrouter
mysqlro+  6026     1  5 09:28 ?        00:00:00 /usr/bin/mysqlrouter

[root@greatsql]# netstat -lntp | grep mysqlrouter
tcp        0      0 0.0.0.0:6446            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:6447            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:6448            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:6449            0.0.0.0:*               LISTEN      6026/mysqlrouter
tcp        0      0 0.0.0.0:8443            0.0.0.0:*               LISTEN      6026/mysqlrouter
```
可以看到 **mysqlrouter** 服务正常启动了。

**mysqlrouter** 初始化时自动生成的配置文件是 `/etc/mysqlrouter/mysqlrouter.conf`，主要是关于R/W、RO不同端口的配置，例如：
```
[routing:greatsqlMGR_rw]
bind_address=0.0.0.0
bind_port=6446
destinations=metadata-cache://greatsqlMGR/?role=PRIMARY
routing_strategy=first-available
protocol=classic
```
可以根据需要自行修改绑定的IP地址和端口。

**3、确认读写分离效果**
现在，用客户端连接到6446（读写）端口，确认连接的是PRIMARY节点：
```
[root@greatsql]# mysql -h172.16.16.10 -u mic -p -P6446
Enter password:
...
mic@GreatSQL [(none)]>select @@server_uuid;
+--------------------------------------+
| @@server_uuid                        |
+--------------------------------------+
| bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1 |
+--------------------------------------+
# 确实是连接的PRIMARY节点（GreatSQL-01）
```

同样地，连接6447（只读）端口，确认连接的是SECONDARY节点：
```
[root@greatsql]# mysql -h172.16.16.10 -u mic -p -P6447
Enter password:
...
mic@GreatSQL [(none)]>select @@server_uuid;
+--------------------------------------+
| @@server_uuid                        |
+--------------------------------------+
| bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2 |
+--------------------------------------+
# 确实是连接的SECONDARY节点（GreatSQL-02）
```

**4、确认只读负载均衡效果**
该连接保持住不退出，继续新建到6447端口的连接，查看 **server_uuid**，应该会发现读取到的是 `GreatSQL-03` 节点的值，因为 **mysqlrouter** 的读负载均衡机制是在几个只读节点间自动轮询（只读请求是不会打到PRIMARY节点的）。

**5、确认故障自动转移功能**
接下来模拟PRIMARY节点宕机或切换时，**mysqlrouter** 也能实现自动故障转移。

登入MGR集群任意节点：
```
[root@greatsql]# mysqlsh --uri mic@172.16.16.10:3306
...
MySQL  172.16.16.10:3306 ssl  JS >  var mic=dba.getCluster();
MySQL  172.16.16.10:3306 ssl  JS >  mic.setPrimaryInstance('GreatSQL-02:3306');   <-- 将GreatSQL-02:3306切换为PRIMARY节点
Setting instance 'GreatSQL-02:3306' as the primary instance of cluster 'greatsqlMGR'...

Instance 'GreatSQL-01:3306' was switched from PRIMARY to SECONDARY.   <-- 切换了，从PRIMARY到SECONDARY
Instance 'GreatSQL-02:3306' was switched from SECONDARY to PRIMARY.   <-- 切换了，从SECONDARY到PRIMARY
Instance 'GreatSQL-03:3306' remains SECONDARY.   <-- 保持不变
Instance 'GreatSQL-04:3306' remains SECONDARY.   <-- 保持不变

WARNING: The cluster internal session is not the primary member anymore. For cluster management operations please obtain a fresh cluster handle using dba.getCluster().

The instance 'GreatSQL-02:3306' was successfully elected as primary.
```

回到前面连接6446端口的那个会话，再次查询 **server_uuid**，此时会发现连接自动断开了：
```
mic@GreatSQL [(none)]> select @@server_uuid;
ERROR 2013 (HY000): Lost connection to MySQL server during query
mic@GreatSQL [(none)]> select @@server_uuid;
ERROR 2006 (HY000): MySQL server has gone away
No connection. Trying to reconnect...
Connection id:    157990
Current database: *** NONE ***

+--------------------------------------+
| @@server_uuid                        |
+--------------------------------------+
| bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2 |   <-- 确认server_uuid变成GreatSQL-02节点的值
+--------------------------------------+
```
这就实现了自动故障转移。

再次查看切换后的MGR集群状态：
```
MySQL  172.16.16.10:3306 ssl  JS >  mic.status();
...
        "topology": {
            "GreatSQL-01:3306": {
                "address": "GreatSQL-01:3306",
                "memberRole": "SECONDARY",   <-- 切换成SECONDARY节点
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
            "GreatSQL-02:3306": {
                "address": "GreatSQL-02:3306",
                "memberRole": "PRIMARY",   <-- 新的PRIMARY节点
                "mode": "R/W",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.22"
            },
...
```

至此，利用InnoDB Cluster配合GreatSQL构建一套支持读写分离、读负载均衡以及故障自动转移的MGR集群就部署完毕了。
