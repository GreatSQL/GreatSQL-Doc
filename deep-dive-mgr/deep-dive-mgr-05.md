# 5. MGR管理维护 | 深入浅出MGR

[toc]

今天介绍MGR集群的日常管理维护操作，包括主节点切换，单主&多主模式切换等。手工操作以及利用MySQL Shell两种方式都会分别介绍。

现在有个三节点的MGR集群：
```
mysql> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST  | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | af39db70-6850-11ec-94c9-00155d064000 | 172.16.16.10 |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | b05c0838-6850-11ec-a06b-00155d064000 | 172.16.16.11 |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | b0f86046-6850-11ec-92fe-00155d064000 | 172.16.16.12 |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```

## 1. 切换主节点
当主节点需要进行维护时，或者执行滚动升级时，就可以对其进行切换，将主节点切换到其他节点。

在命令行模式下，可以使用 group_replication_set_as_primary() 这个udf实现切换，例如：
```
-- 将Primary角色切换到第二个节点
mysql> select group_replication_set_as_primary('b05c0838-6850-11ec-a06b-00155d064000');
+--------------------------------------------------------------------------+
| group_replication_set_as_primary('b05c0838-6850-11ec-a06b-00155d064000') |
+--------------------------------------------------------------------------+
| Primary server switched to: b05c0838-6850-11ec-a06b-00155d064000         |
+--------------------------------------------------------------------------+
1 row in set (1.00 sec)

[root@yejr.run:mysql.sock] [(none)]>select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST  | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | af39db70-6850-11ec-94c9-00155d064000 | 172.16.16.10 |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | b05c0838-6850-11ec-a06b-00155d064000 | 172.16.16.11 |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | b0f86046-6850-11ec-92fe-00155d064000 | 172.16.16.12 |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```

顺便提一下，在MySQL 5.7版本中，只能通过重启以实现主节点的自动切换，不能手动切换。从这个角度来说，如果想要使用MGR，最好是选择MySQL 8.0版本，而不要使用5.7版本。

如果是用MySQL Shell，则可以调用 `setPrimaryInstance()` 函数进行切换：
```
#首先获取cluster对象
 MySQL  172.16.16.10:3306 ssl  JS > var c=dba.getCluster()
#查看当前各节点列表 
 MySQL  172.16.16.10:3306 ssl  JS > c.status()

        "status": "OK",
        "statusText": "Cluster is ONLINE and can tolerate up to ONE failure.",
        "topology": {
            "172.16.16.10:3306": {
                "address": "172.16.16.10:3306",
                "memberRole": "PRIMARY",
                "mode": "R/W",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.25"
            },
            "172.16.16.11:3306": {
                "address": "172.16.16.11:3306",
                "memberRole": "SECONDARY",
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.25"
            },
            "172.16.16.12:3306": {
                "address": "172.16.16.12:3306",
                "memberRole": "SECONDARY",
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": null,
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.25"
            }
        },
        "topologyMode": "Single-Primary"
    },
    "groupInformationSourceMember": "172.16.16.10:3306"
}

#执行切换
 MySQL  172.16.16.10:3306 ssl  JS > c.setPrimaryInstance('172.16.16.11:3306')
Setting instance '172.16.16.11:3306' as the primary instance of cluster 'MGR1'...

#罗列了三个节点各自发生的变化
Instance '172.16.16.10:3306' was switched from PRIMARY to SECONDARY.
Instance '172.16.16.11:3306' was switched from SECONDARY to PRIMARY.
Instance '172.16.16.12:3306' remains SECONDARY.

WARNING: The cluster internal session is not the primary member anymore. For cluster management operations please obtain a fresh cluster handle using dba.getCluster().

#完成切换
The instance '172.16.16.11:3306' was successfully elected as primary.
```

## 2. 切换单主/多主模式
在命令行模式下，可以调用 `group_replication_switch_to_single_primary_mode()` 和 `group_replication_switch_to_multi_primary_mode()` 来切换单主/多主模式。
```
#直接调用函数即可
mysql> select group_replication_switch_to_multi_primary_mode();
+--------------------------------------------------+
| group_replication_switch_to_multi_primary_mode() |
+--------------------------------------------------+
| Mode switched to multi-primary successfully.     |
+--------------------------------------------------+

#查看各节点状态
mysql> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST  | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | af39db70-6850-11ec-94c9-00155d064000 | 172.16.16.10 |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | b05c0838-6850-11ec-a06b-00155d064000 | 172.16.16.11 |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | b0f86046-6850-11ec-92fe-00155d064000 | 172.16.16.12 |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+

#切换成单主模式时可以指定某个节点的 server_uuid，如果不指定则会根据规则自动选择一个新的主节点
#在这里，我选择了指定mgr3节点作为新主
mysql> select group_replication_switch_to_single_primary_mode('b0f86046-6850-11ec-92fe-00155d064000');
+-----------------------------------------------------------------------------------------+
| group_replication_switch_to_single_primary_mode('b0f86046-6850-11ec-92fe-00155d064000') |
+-----------------------------------------------------------------------------------------+
| Mode switched to single-primary successfully.                                           |
+-----------------------------------------------------------------------------------------+
```

在MySQL Shell中，可以调用 `switchToSinglePrimaryMode()` 以及 `switchToMultiPrimaryMode()` 函数进行切换。同样地，函数 `switchToSinglePrimaryMode()` 里也可以指定某个节点作为新的主节点。
```
 MySQL  172.16.16.10:3306 ssl  JS > var c=dba.getCluster()

#切换到多主模式 
 MySQL  172.16.16.10:3306 ssl  JS > c.switchToMultiPrimaryMode()
 
#切换到单主模式，这里我指定mgr2节点作为新主
 MySQL  172.16.16.10:3306 ssl  JS > c.switchToSinglePrimaryMode("172.16.16.11:3306")
```

**注意**，在已经是单主模式时，无论是 `group_replication_switch_to_single_primary_mode()` 还是 `switchToSinglePrimaryMode()` 函数中指定另一个节点时是不会发生切换的，但也不会报错，只有提示。

## 3. 添加新节点
接下来我们演示如何向MGR集群中添加一个新节点。

首先，要先完成MySQL Server初始化，创建好MGR专用账户、设置好MGR服务通道等前置工作，这部分的操作可以参考前文 [**3. 安装部署MGR集群**](x)。

接下来，直接执行命令 `start group_replication` 启动MGR服务即可，新增的节点会进入分布式恢复这个步骤，它会从已有节点中自动选择一个作为捐献者（donor），并自行决定是直接读取binlog进行恢复，还是利用Clone进行全量恢复。

如果是已经在线运行一段时间的MGR集群，有一定存量数据，这时候新节点加入可能会比较慢，建议手动利用Clone进行一次全量复制。还记得前面创建MGR专用账户时，给加上了 **BACKUP_ADMIN** 授权吗，这时候就排上用场了，Clone需要用到这个权限。

下面演示如何利用Clone进行一次全量数据恢复，假定要新增的节点是 *172.16.16.13* （给它命名为 mgr4）。
```
#在mgr4上设置捐献者
#为了降低对Primary节点的影响，建议选择其他Secondary节点
mysql> set global clone_valid_donor_list='172.16.16.11:3306';

#停掉mgr服务（如果有的话），关闭super_read_only模式，然后开始复制数据
#注意这里要填写的端口是3306（MySQL正常服务端口），而不是33061这个MGR服务专用端口
mysql> stop group_replication; set global super_read_only=0; clone INSTANCE FROM GreatSQL@172.16.16.11:3306 IDENTIFIED BY 'GreatSQL';
```
全量复制完数据后，该节点会进行一次自动重启。重启完毕后，再次确认 `group_replication_group_name`、`group_replication_local_address`、`group_replication_group_seeds` 这些选项值是否正确，如果没问题，执行 `start group_replication` 后，该节点应该就可以正常加入集群了。

如果是用MySQL Shell添加新节点则更简单。先执行MySQL Server初始化，并执行 `dba.dba.configureInstance()` 创建MGR专用账号后。而后，连接到Primary节点，直接调用 `addInstance()` 函数即可：
```
#连接到Primary节点
$ mysqlsh --uri GreatSQL@172.16.16.10:3306
 MySQL  172.16.16.10:3306 ssl  JS > var c=dba.getCluster()
 MySQL  172.16.16.10:3306 ssl  JS > c.addInstance('GreatSQL@172.16.16.13:3306')

WARNING: A GTID set check of the MySQL instance at '172.16.16.13:3306' determined that it contains transactions that do not originate from the cluster, which must be discarded before it can join the cluster. 
...
NOTE: 172.16.16.13:3306 is being cloned from 172.16.16.10:3306  #<--自动选择一个donor节点
** Stage DROP DATA: Completed
** Clone Transfer
    FILE COPY  ############################################################  100%  Completed
    PAGE COPY  ############################################################  100%  Completed
    REDO COPY  ############################################################  100%  Completed

NOTE: 172.16.16.13:3306 is shutting down...

* Waiting for server restart... ready
* 172.16.16.13:3306 has restarted, waiting for clone to finish...
** Stage RESTART: Completed
* Clone process has finished: 72.43 MB transferred in about 1 second (~72.43 MB/s)

Incremental state recovery is now in progress.

* Waiting for distributed recovery to finish...
NOTE: '172.16.16.13:3306' is being recovered from '172.16.16.12:3306'
* Distributed recovery has finished

#新节点成功加入完毕
The instance '172.16.16.13:3306' was successfully added to the cluster.

#确认添加成功，已在MGR集群列表中
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
            },
            {
                "address": "172.16.16.13:3306",  <--新加入的节点
                "label": "172.16.16.13:3306",
                "role": "HA"
            }
        ],
        "topologyMode": "Single-Primary"
    }
} 
```
确认新节点添加成功。

## 4. 删除节点
在命令行模式下，一个节点想退出MGR集群，直接执行 `stop group_replication` 即可，如果这个节点只是临时退出集群，后面还想加回集群，则执行 `start group_replication` 即可自动再加入。而如果是想彻底退出集群，则停止MGR服务后，执行 `reset master; reset slave all;` 重置所有复制（包含MGR）相关的信息就可以了。

在MySQL Shell里，只需调用 `removeInstance()` 函数即可删除某个节点，例如：
```
 MySQL  172.16.16.10:3306 ssl  JS > c.removeInstance('172.16.16.13:3306');
The instance will be removed from the InnoDB cluster. Depending on the instance
being the Seed or not, the Metadata session might become invalid. If so, please
start a new session to the Metadata Storage R/W instance.

Instance '172.16.16.13:3306' is attempting to leave the cluster...

The instance '172.16.16.13:3306' was successfully removed from the cluster.
```
这就将该节点踢出集群了，并且会重置 `group_replication_group_seeds` 和 `group_replication_local_address` 两个选项值。之后该节点如果想再加入集群，需要调用 `addInstance()` 重新加回。

## 5. 异常退出的节点重新加回
当节点因为网络断开、实例crash等异常情况与MGR集群断开连接后，这个节点的状态会变成 **UNREACHABLE**，待到超过 `group_replication_member_expel_timeout` + 5 秒后，集群会踢掉该节点。等到这个节点再次启动并执行 `start group_replication`，正常情况下，该节点应能自动重新加回集群。

在MySQL Shell里，可以调用 `rejoinInstance()` 函数将异常的节点重新加回集群：
```
 MySQL  172.16.16.10:3306 ssl  JS > c.rejoinInstance('172.16.16.13:3306');
 
Rejoining instance '172.16.16.13:3306' to cluster 'MGR1'...
The instance '172.16.16.13:3306' was successfully rejoined to the cluster.
```

## 6. 重启MGR集群
正常情况下，MGR集群中的Primary节点退出时，剩下的节点会自动选出新的Primary节点。当最后一个节点也退出时，相当于整个MGR集群都关闭了。这时候任何一个节点启动MGR服务后，都不会自动成为Primary节点，需要在启动MGR服务前，先设置 `group_replication_bootstrap_group=ON`，使其成为引导节点，再启动MGR服务，它才会成为Primary节点，后续启动的其他节点也才能正常加入集群。可自行测试，这里不再做演示。

P.S，第一个节点启动完毕后，记得重置选项 `group_replication_bootstrap_group=OFF`，避免在后续的操作中导致MGR集群分裂。

如果是用MySQL Shell重启MGR集群，调用 `rebootClusterFromCompleteOutage()` 函数即可，它会自动判断各节点的状态，选择其中一个作为Primary节点，然后拉起各节点上的MGR服务，完成MGR集群重启。可以参考这篇文章：[万答#12，MGR整个集群挂掉后，如何才能自动选主，不用手动干预](https://mp.weixin.qq.com/s/07o1poO44zwQIvaJNKEoPA)

## 7. 小结
本文介绍了MGR集群几种常见管理维护操作方法，包括切换主节点，切换单主/多主模式，添加节点，删除节点，异常节点重加入，重启整个MGR集群等。总的来看，利用MySQL Shell管理MGR集群会更简单方便些，也有利于管理平台的封装，不过手工操作的方式也不能忘记，有些时候可能没有配套的MySQL Shell工具，就得靠手工了。


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