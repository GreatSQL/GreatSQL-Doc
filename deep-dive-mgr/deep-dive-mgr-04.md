# 4. 利用MySQL Shell安装部署MGR集群 | 深入浅出MGR

本文介绍如何利用MySQL Shell for GreatSQL + GreatSQL 8.0.32构建一个三节点的MGR集群。

MySQL Shell for GreatSQL（下面简称GreatSQL Shell）是一个客户端工具，可用于方便管理和操作MySQL/GreatSQL，支持SQL、JavaScript、Python等多种语言，也包括完善的API。GreatSQL Shell支持文档型和关系型数据库模式，通过X DevAPI可以管理文档型数据，通过AdminAPI可以管理InnoDB Cluster、InnoDB ClusterSet及InnoDB ReplicaSet等。

GreatSQL Shell在原生的MySQL Shell基础上增加对仲裁节点（Arbitrator节点）的支持，如果使用GreatSQL构建一个包含Arbitrator节点的MGR集群，推荐使用GreatSQL Shell来管理和操作。

## 1. 安装准备
准备好下面三台服务器：

| IP | 端口 | 角色 | 
| --- | --- | --- |
| 172.16.16.10 | 3306 | mgr1 | 
| 172.16.16.11 | 3306 | mgr2 | 
| 172.16.16.12 | 3306 | mgr3 | 

确保三个节点间的网络是可以互通的，并且没有针对3306和33061端口的防火墙拦截规则。

访问 [https://gitee.com/GreatSQL/GreatSQL/releases/tag/GreatSQL-8.0.32-25](https://gitee.com/GreatSQL/GreatSQL/releases/tag/GreatSQL-8.0.32-25)，选择并下载和GreatSQL 8.0.32-25相同的发行版，如：*greatsql-shell-8.0.32-25-glibc2.28-x86_64.tar.xz*。

假定已经参考前文 [**3. 安装部署MGR集群**](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-03.md) 做好GreatSQL数据库实例的安装及初始化。

接下来直接利用GreatSQL Shell部署MGR。

## 2. 利用GreatSQL Shell构建MGR集群
利用GreatSQL Shell构建MGR集群比较简单，主要有几个步骤：
1. 检查实例是否满足条件。
2. 创建并初始化一个集群。
3. 逐个添加实例。

首先，用管理员账号 root 连接到第一个节点：
```
#在本地通过socket方式登入
$ mysqlsh -S /data/GreatSQL/mysql.sock root@localhost
Please provide the password for 'root@.%2Fmysql.sock': ********
Save password for 'root@.%2Fmysql.sock'? [Y]es/[N]o/Ne[v]er (default No): yes
MySQL Shell 8.0.32
...
```
执行命令 `\status` 查看当前节点的状态，确认连接正常可用。

执行 `dba.configureInstance()` 命令开始检查当前实例是否满足安装MGR集群的条件，如果不满足可以直接配置成为MGR集群的一个节点：
```
 MySQL  localhost  JS > dba.configureInstance()
Configuring local MySQL instance listening at port 3306 for use in an InnoDB cluster...

This instance reports its own address as 172.16.16.10:3306

#提示当前的用户是管理员，不能直接用于MGR集群，需要新建一个账号
ERROR: User 'root' can only connect from 'localhost'. New account(s) with proper source address specification to allow remote connection from all instances must be created to manage the cluster.

1) Create remotely usable account for 'root' with same grants and password
2) Create a new admin account for InnoDB cluster with minimal required grants
3) Ignore and continue
4) Cancel

Please select an option [1]: 2 <-- 这里我们选择方案2，即创建一个最小权限账号
Please provide an account name (e.g: icroot@%) to have it created with the necessary
privileges or leave empty and press Enter to cancel.
Account Name: GreatSQL
Password for new account: ********
Confirm password: ********

applierWorkerThreads will be set to the default value of 4.

The instance '172.16.16.10:3306' is valid to be used in an InnoDB cluster.

Cluster admin user 'GreatSQL'@'%' created.
The instance '172.16.16.10:3306' is already ready to be used in an InnoDB cluster.

Successfully enabled parallel appliers.
```
完成检查并创建完新用户后，退出当前的管理员账户，并用新创建的MGR专用账户登入，准备初始化创建一个新集群：
```
$ mysqlsh --uri GreatSQL@172.16.16.10:3306
Please provide the password for 'GreatSQL@172.16.16.10:3306': ********
Save password for 'GreatSQL@172.16.16.10:3306'? [Y]es/[N]o/Ne[v]er (default No): yes
MySQL Shell 8.0.32

...
#定义一个变量名c，方便下面引用
 MySQL  172.16.16.10:3306 ssl  JS > var c = dba.createCluster('MGR1');
A new InnoDB cluster will be created on instance '172.16.16.10:3306'.

Validating instance configuration at 172.16.16.10:3306...

This instance reports its own address as 172.16.16.10:3306

Instance configuration is suitable.
NOTE: Group Replication will communicate with other members using '172.16.16.10:33061'. Use the localAddress option to override.

Creating InnoDB cluster 'MGR1' on '172.16.16.10:3306'...

Adding Seed Instance...

Cluster successfully created. Use Cluster.addInstance() to add MySQL instances.
At least 3 instances are needed for the cluster to be able to withstand up to
one server failure.

 MySQL  172.16.16.10:3306 ssl  JS >
```
这就完成了MGR集群的初始化并加入第一个节点（引导节点）。

接下来，用同样方法先用 root 账号分别登入到另外两个节点，完成节点的检查并创建最小权限级别用户（此过程略过。。。注意各节点上创建的用户名、密码都要一致），之后回到第一个节点，执行 `addInstance()` 添加另外两个节点。
```
 MySQL  172.16.16.10:3306 ssl  JS > c.addInstance('GreatSQL@172.16.16.11:3306');  <-- 这里要指定MGR专用账号

WARNING: A GTID set check of the MySQL instance at '172.16.16.11:3306' determined that it contains transactions that do not originate from the cluster, which must be discarded before it can join the cluster.

172.16.16.11:3306 has the following errant GTIDs that do not exist in the cluster:
b05c0838-6850-11ec-a06b-00155d064000:1

WARNING: Discarding these extra GTID events can either be done manually or by completely overwriting the state of 172.16.16.11:3306 with a physical snapshot from an existing cluster member. To use this method by default, set the 'recoveryMethod' option to 'clone'.

Having extra GTID events is not expected, and it is recommended to investigate this further and ensure that the data can be removed prior to choosing the clone recovery method.

Please select a recovery method [C]lone/[A]bort (default Abort): Clone  <-- 选择用Clone方式从第一个节点全量复制数据
Validating instance configuration at 172.16.16.11:3306...

This instance reports its own address as 172.16.16.11:3306

Instance configuration is suitable.
NOTE: Group Replication will communicate with other members using '172.16.16.11:33061'. Use the localAddress option to override.

A new instance will be added to the InnoDB cluster. Depending on the amount of
data on the cluster this might take from a few seconds to several hours.

Adding instance to the cluster...

Monitoring recovery process of the new cluster member. Press ^C to stop monitoring and let it continue in background.
Clone based state recovery is now in progress.

NOTE: A server restart is expected to happen as part of the clone process. If the
server does not support the RESTART command or does not come back after a
while, you may need to manually start it back.

* Waiting for clone to finish...
NOTE: 172.16.16.11:3306 is being cloned from 172.16.16.10:3306
** Stage DROP DATA: Completed
** Clone Transfer
    FILE COPY  ############################################################  100%  Completed
    PAGE COPY  ############################################################  100%  Completed
    REDO COPY  ############################################################  100%  Completed

NOTE: 172.16.16.11:3306 is shutting down...  <-- 数据Clone完成，准备重启实例。如果该实例无法完成自动重启，则需要手动启动

* Waiting for server restart... ready
* 172.16.16.11:3306 has restarted, waiting for clone to finish...
** Stage RESTART: Completed
* Clone process has finished: 72.43 MB transferred in about 1 second (~72.43 MB/s)

State recovery already finished for '172.16.16.11:3306'

The instance '172.16.16.11:3306' was successfully added to the cluster.  <-- 新实例加入成功

 MySQL  172.16.16.10:3306 ssl  JS >
```
用同样的方法，将 172.16.16.12:3306 实例也加入到集群中。

现在，一个有这三节点的MGR集群已经部署完毕，来确认下：
```
 MySQL  172.16.16.10:3306 ssl  JS > c.describe()
{
    "clusterName": "MGR1",
    "defaultReplicaSet": {
        "name": "default",
        "topology": [
            {
                "address": "172.16.16.10:3306",
                "label": "172.16.16.10:3306",
                "role": "HA"
            },
            {
                "address": "172.16.16.11:3306",
                "label": "172.16.16.11:3306",
                "role": "HA"
            },
            {
                "address": "172.16.16.12:3306",
                "label": "172.16.16.12:3306",
                "role": "HA"
            }
        ],
        "topologyMode": "Single-Primary"
    }
} 
```
或者执行 `c.status()` 可以打印出集群更多的信息。

至此，利用GreatSQL Shell构建一个三节点的MGR集群做好了，可以尝试向 Primary 节点写入数据观察测试。

## 3. GreatSQL Shell接管现存的MGR集群
对于已经在运行中的MGR集群，也是可以用GreatSQL Shell接管的。只需要在调用 `createCluster()` 函数时，加上 `adoptFromGR:true` 选项即可。实际上不加这个选项的话，GreatSQL Shell也会自动检测到该MGR集群已存在，并询问是否要接管。

在这里简单演示下：
```
#不加上 adoptFromGr:true 选项
 MySQL  172.16.16.10:3306 ssl  JS > var c=dba.createCluster('MGR1');
A new InnoDB cluster will be created on instance '172.16.16.10:3306'.

You are connected to an instance that belongs to an unmanaged replication group.
Do you want to setup an InnoDB cluster based on this replication group? [Y/n]:
```
可以看到，会有提示信息询问是否要接管。

如果加上 `adoptFromGr:true` 选项，则会直接创建集群，不再询问：
```
var c=dba.createCluster('MGR1', {adoptFromGr:true});
A new InnoDB cluster will be created based on the existing replication group on instance '172.16.16.10:3306'.

Creating InnoDB cluster 'MGR1' on '172.16.16.10:3306'...

Adding Seed Instance...
Adding Instance '172.16.16.10:3306'...
Adding Instance '172.16.16.11:3306'...
Adding Instance '172.16.16.12:3306'...
...
```

如果是MGR集群的metadata发生变化，这时候无论调用 `dba.getCluster()` 还是 `dba.createCluster` 都可能会报告类似下面的错误：
```
Dba.getCluster: Unable to get an InnoDB cluster handle. The instance '192.168.6.27:3306' may belong to a different cluster from the one registered in the Metadata since the value of 'group_replication_group_name' does not match the one registered in the Metadata: possible split-brain scenario. Please retry while connected to another member of the cluster. (RuntimeError)
```

这种情况下，可以调用 `dba.dropMetadataSchema()` 函数删除元数据，再调用 `dba.createCluster()` 接管集群：
```
#确保不影响正常业务的话，删除无用MGR元数据
 MySQL  172.16.16.10:3306 ssl  JS > dba.dropMetadataSchema()
Are you sure you want to remove the Metadata? [y/N]: y
Metadata Schema successfully removed.

#接管现有集群
 MySQL  172.16.16.10:3306 ssl  JS > var c=dba.createCluster('MGR1', {adoptFromGr:true})
...
```
这样就可以了接管了。

## 4. 使用GreatSQL Shell的窍门
在GreatSQL Shell中，也是可以启用pager（分页器）的，像下面这样设置即可：
```
mysqlsh> shell.enablePager();
mysqlsh> shell.options["pager"]="less -i -n -S";
Pager has been set to 'less -i -n -S'.
```

在用GreatSQL Shell连接时，也可以加上 `--dba-log-sql=2 --log-level=debug3` 参数，以启用debug模式，并记录运行过程中实际调用的SQL命令，默认日志文件是 `~/.mysqlsh/mysqlsh.log`。

## 5. 小结
本文主要介绍了如何利用GreatSQL Shell构建一个三节点的MGR集群，以及如何用GreatSQL Shell接管现有集群，处理元数据冲突的问题。相对于手工方式搭建MGR集群，用GreatSQL Shell操作会方便很多，推荐使用。

## 参考资料、文档
- [MySQL 8.0 Reference Manual](https://dev.mysql.com/doc/refman/8.0/en/group-replication.html) 
- [数据库内核开发 - 温正湖](https://www.zhihu.com/column/c_206071340)
- [Group Replication原理 - 宋利兵](https://mp.weixin.qq.com/s/LFJtdpISVi45qv9Wksv19Q)

## 免责声明
因个人水平有限，专栏中难免存在错漏之处，请勿直接复制文档中的命令、方法直接应用于线上生产环境。请读者们务必先充分理解并在测试环境验证通过后方可正式实施，避免造成生产环境的破坏或损害。

## 加入团队
如果您有兴趣一起加入协作，欢迎联系我们，可直接提交PR，或者将内容以markdown的格式发送到邮箱：greatsql@greatdb.com。

亦可通过微信、QQ联系我们。

![Contact Us](../docs/contact-us.png)
