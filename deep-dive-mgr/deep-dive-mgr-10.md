# 10. 选主算法、多版本兼容性及滚动升级 | 深入浅出MGR

[toc]

本文介绍MGR的选主算法，以及当MGR集群中有多个不同版本混搭时，如何才能正常运行，有什么注意事项。

## 1. 选主算法
MGR运行在单主模式时，当发生主节点切换，就需要进行选主工作。多主模式下，所有节点都是主节点，就不需要选主了。

MGR的选主工作是自动的，每个节点都会参与。选主时会检查当前最新的组视图，对潜在的新主节点（各个备选节点）进行排序，最后选出最合适的那个作为新的主节点。

不同的MySQL版本选主算法略有不同，各节点选主时会根据当前的MySQL版本选主算法而决定，因此当MGR集群中有多个版本并存时，则此时MGR会做出调整，以便各个不同版本的节点都能就选主达成算法一致。

通常而言，选主算法的各个因素优先级顺序如下：
1. 根据MySQL版本号排序，低版本的优先级更高（因为要向下兼容）。如果是MySQL 8.0.17及以上版本，则优先根据补丁版本号排序（例如17、18、20）。如果是8.0.16及以下版本，则优先根据主版本号排序（例如5.7、8.0）。
2. 版本号相同的各节点则根据各节点的权重值排序，权重越高优先级也越高。节点的权重值可通过设置 `group_replication_member_weight` 选项来调整。这个选项是MySQL 8.0版本引入的，如果是5.7版本则不支持。
3. 当版本号和节点权重值都一样时，再根据 `server_uuid`（或者说是 `MEMBER_ID`）排序（注意，不是 `server_id`），排在前面的优先级越高。MySQL Server在启动时，会生成一个随机的UUID值，其值记录在文件 *datadir/auto.cnf* 文件中，实际上可以在实例启动前，通过修改这个UUID值来改变 `server_uuid` 的值，只要符合UUID数据格式即可。因此，相当于是可以认为调整 `server_uuid` 以调整选主时节点的排序优先级。

从上面可知，当有MySQL 8.0和5.7的节点混搭运行MGR集群时，运行5.7版本的节点会优先被选中，其次再根据 `group_replication_member_weight` 选择权重高的节点，最后再根据 `server_uuid` 排序。

因此，运行MGR集群时最好各节点版本号相同，选主规则就简单多了。

在MySQL 8.0中，通过查询 `performance_schema.replication_group_members` 表的`MEMBER_ROLE` 即可知道哪个是主节点：
```
mysql> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST  | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 4ebd3504-11d9-11ec-8f92-70b5e873a570 | 172.16.16.10 |        3306 | ONLINE       | PRIMARY     | 8.0.25         |  <---主节点
| group_replication_applier | 549b92bf-11d9-11ec-88e1-70b5e873a570 | 172.16.16.11 |        3307 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | 5596116c-11d9-11ec-8624-70b5e873a570 | 172.16.16.12 |        3308 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```

如果是在MySQL 5.7中，则需要通过查询 `group_replication_primary_member` 这个 status 才能知道，比8.0麻烦。所以说，还是尽量使用MySQL 8.0来构建MGR集群。

在一个MySQL 5.7和8.0混搭的MGR集群中，从运行MySQL 8.0版本的节点上看到的状态是这样的：
```
mysql> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+---------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST   | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+---------------+-------------+--------------+-------------+----------------+
| group_replication_applier | af39db70-6850-11ec-94c9-00155d064000 | 172.16.16.13  |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | d9833e7e-6ecc-11ec-a3f6-d08e7908bcb1 | 172.16.16.10  |        3306 | ONLINE       | PRIMARY     | 5.7.36         |
| group_replication_applier | fe55e195-6ecc-11ec-a2e9-d08e7908bcb1 | 172.16.16.11  |        3306 | ONLINE       | SECONDARY   | 5.7.36         |
| group_replication_applier | ff19317f-6ecc-11ec-b17d-d08e7908bcb1 | 172.16.16.12  |        3306 | ONLINE       | SECONDARY   | 5.7.36         |
+---------------------------+--------------------------------------+---------------+-------------+--------------+-------------+----------------+
```

可以看到，即便是运行MySQL 8.0版本的节点的 `server_uuid` 排序在前面，但在自动选主时，也不会被选中作为主节点。此外，运行MySQL 5.7版本的节点是无法加入主节点运行MySQL 8.0的MGR集群的，会报告类似下面的错误：
```
[ERROR] Plugin group_replication reported: 'Member version is incompatible with the group'
```
提示版本不兼容。

## 2. 多版本兼容性
正常地，为了MGR的兼容性及性能，所有节点的MySQL版本最好保持一致。尤其是在多主模式下，各节点都提供写入服务，如果兼容性方面存在问题，则可能会导致MGR集群异常或写入异常。为了避免这种情况发生，新加入节点时，会和其他节点进行版本兼容性检查。

目前MGR支持3个通信协议版本号：5.7.14、8.0.16、8.0.27，这几个版本的主要变化有：
- 从5.7.14开始，支持消息压缩。
- 从8.0.16开始，支持消息分片。
- 从8.0.27开始，支持在单主模式下，设置唯一的leader节点。

MGR集群中，各节点间的通信协议版本号必须一致，这样才能保证即使是MySQL版本号不一致，但MGR通信依然不受影响。新加入节点的通信协议版本号必须高于当前集群中使用的通信协议版本。节点加入时会检查协议版本，并向其广播当前集群中使用的协议版本，如果可以兼容，则允许加入，否则会将其踢出。

当两个节点同时加入时，只有当两个节点的通信协议版本和集群兼容时，才能同时加入成功。和当前集群不同协议版本的节点需要单独加入才行，例如：
- 一个使用8.0.16版本的实例可以成功加入使用通信协议版本5.7.24的集群。
- 一个5.7.24实例无法加入使用8.0.16的集群。
- 两个8.0.16实例无法同时加入使用5.7.24的集群。
- 两个8.0.16实例可以同时加入使用8.0.16的集群。

如果有需要，还可以在线修改通信协议版本号，使用 `group_replication_set_communication_protocol()` 这个UDF即可（MySQL 8.0以上支持），例如：
```
mysql> select version();
+-----------+
| version() |
+-----------+
| 8.0.25-15 |  <-- 当前MySQL版本是8.0.25
+-----------+
1 row in set (0.00 sec)

mysql> select group_replication_get_communication_protocol();
+------------------------------------------------+
| group_replication_get_communication_protocol() |
+------------------------------------------------+
| 8.0.16                                         |  <-- 当前MGR通信协议版本是8.0.16
+------------------------------------------------+
1 row in set (0.00 sec)

mysql> select group_replication_set_communication_protocol('5.7.14');
+-----------------------------------------------------------------------------------+
| group_replication_set_communication_protocol('5.7.14')                            |  <-- 手动修改通信协议版本为5.7.14，可以成功
+-----------------------------------------------------------------------------------+
| The operation group_replication_set_communication_protocol completed successfully |
+-----------------------------------------------------------------------------------+

mysql> select group_replication_set_communication_protocol('8.0.25');
+-----------------------------------------------------------------------------------+
| group_replication_set_communication_protocol('8.0.25')                            |
+-----------------------------------------------------------------------------------+
| The operation group_replication_set_communication_protocol completed successfully |  <-- 修改协议版本为8.0.25，接下来看看会发生什么
+-----------------------------------------------------------------------------------+
1 row in set (0.00 sec)

mysql> select group_replication_get_communication_protocol();
+------------------------------------------------+
| group_replication_get_communication_protocol() |
+------------------------------------------------+
| 8.0.16                                         |  <-- 重置为8.0.16
+------------------------------------------------+

# 尝试修改为8.0.27，会报错
mysql> select group_replication_set_communication_protocol('8.0.27');
ERROR 1123 (HY000): Can't initialize function 'group_replication_set_communication_protocol'; 8.0.27 is not between 5.7.14 and 8.0.25
```

其实说这么多版本兼容性的话题，还不如一个简单的原则：**让所有节点的版本号都一致**。这样构建MGR集群更简单，节点间通信也不会被复杂化。

## 3. MGR 5.7滚动升级至8.0
MGR 5.7集群滚动升级至8.0可以参考这篇文章：[**MySQL MGR从5.7滚动升级至8.0**](https://mp.weixin.qq.com/s/bPb-0agjqEvuAjHT-MqX9g)，简言之，可以分为以下几步：
1. 在现有MGR 5.7集群中，新增MySQL 8.0的Secondary节点。
2. 一比一下线一个MySQL 5.7的Secondary节点。
3. 如此往复，直到剩下最后一个MySQL 5.7的Primary节点。
4. 再次上线一个MySQL 8.0的Secondary节点。
5. 停止最后一个MySQL 5.7的Primary节点，这是会切换主节点，并且选择其中一个MySQL 8.0节点作为新的Primary节点，这就完成升级了。

在这里实操演示大概的过程。

在MGR 5.7的集群中，增加一个MySQL 8.0的Secondary节点：
```
#在5.7节点上看节点状态
#原生的MySQL 5.7 MGR看不到 MEMBER_ROLE 这列
#这是GreatSQL 5.7新增的特性
mysql> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+
| group_replication_applier | c8ec34c4-78fc-11ec-864a-111111111111 | 127.0.0.1   |        4306 | ONLINE       | PRIMARY     |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-222222222222 | 127.0.0.1   |        4307 | ONLINE       | SECONDARY   |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-333333333333 | 127.0.0.1   |        4308 | ONLINE       | SECONDARY   |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-888888888333 | 127.0.0.1   |        3309 | ONLINE       | SECONDARY   |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+

#在8.0节点上看
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | c8ec34c4-78fc-11ec-864a-111111111111 | 127.0.0.1   |        4306 | ONLINE       | PRIMARY     | 5.7.36         |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-222222222222 | 127.0.0.1   |        4307 | ONLINE       | SECONDARY   | 5.7.36         |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-333333333333 | 127.0.0.1   |        4308 | ONLINE       | SECONDARY   | 5.7.36         |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-888888888333 | 127.0.0.1   |        3309 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
```

现在，利用MySQL Shell删除一个旧节点：
```
c.removeInstance('127.0.0.1:4308');
The instance will be removed from the InnoDB cluster. Depending on the instance
being the Seed or not, the Metadata session might become invalid. If so, please
start a new session to the Metadata Storage R/W instance.

Instance '127.0.0.1:4308' is attempting to leave the cluster...
WARNING: On instance '127.0.0.1:4308' configuration cannot be persisted since MySQL version 5.7.36 does not support the SET PERSIST command (MySQL version >= 8.0.11 required). Please set the 'group_replication_start_on_boot' variable to 'OFF' in the server configuration file, otherwise it might rejoin the cluster upon restart.
WARNING: Instance '127.0.0.1:4306' cannot persist configuration since MySQL version 5.7.36 does not support the SET PERSIST command (MySQL version >= 8.0.11 required). Please use the dba.configureLocalInstance() command locally to persist the changes.

The instance '127.0.0.1:4308' was successfully removed from the cluster.
```

之后再查看节点状态：
```
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | c8ec34c4-78fc-11ec-864a-111111111111 | 127.0.0.1   |        4306 | ONLINE       | PRIMARY     | 5.7.36         |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-222222222222 | 127.0.0.1   |        4307 | ONLINE       | SECONDARY   | 5.7.36         |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-888888888333 | 127.0.0.1   |        3309 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
```

如此往复，直到只剩最后一个5.7节点：
```
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | c8ec34c4-78fc-11ec-864a-111111111111 | 127.0.0.1   |        4306 | ONLINE       | PRIMARY     | 5.7.36         |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-888888888333 | 127.0.0.1   |        3309 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-888888888444 | 127.0.0.1   |        3310 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-888888888555 | 127.0.0.1   |        3311 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
```

关闭最后一个5.7节点，会自动切换主节点：
```
 MySQL  127.0.0.1:4306 ssl  JS > c.removeInstance('127.0.0.1:4306');
The instance will be removed from the InnoDB cluster. Depending on the instance
being the Seed or not, the Metadata session might become invalid. If so, please
start a new session to the Metadata Storage R/W instance.

Instance '127.0.0.1:4306' is attempting to leave the cluster...
WARNING: On instance '127.0.0.1:4306' configuration cannot be persisted since MySQL version 5.7.36 does not support the SET PERSIST command (MySQL version >= 8.0.11 required). Please set the 'group_replication_start_on_boot' variable to 'OFF' in the server configuration file, otherwise it might rejoin the cluster upon restart.

The instance '127.0.0.1:4306' was successfully removed from the cluster.
```

之后可以看到5.7节点全部下线了，只剩下8.0节点：
```
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | c8ec34c4-78fc-11ec-864a-888888888333 | 127.0.0.1   |        3309 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-888888888444 | 127.0.0.1   |        3310 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | c8ec34c4-78fc-11ec-864a-888888888555 | 127.0.0.1   |        3311 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
```

查看切换过程：
```
2022-01-20T22:19:10.753644+08:00 0 [Warning] [MY-011499] [Repl] Plugin group_replication reported: 'Members removed from the group: 127.0.0.1:4306'
2022-01-20T22:19:10.753648+08:00 0 [System] [MY-011500] [Repl] Plugin group_replication reported: 'Primary server with address 127.0.0.1:4306 left the group. Electing new Primary.'
2022-01-20T22:19:10.753705+08:00 0 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'handle_leader_election_if_neede
d is activated,suggested_primary:'
2022-01-20T22:19:10.754747+08:00 0 [Note] [MY-013519] [Repl] Plugin group_replication reported: 'Elected primary member gtid_exe
cuted: 082b900b-79d5-11ec-8fe2-00155d064000:1-32, 36ab409a-79d6-11ec-9cd5-00155d064000:1-37'
2022-01-20T22:19:10.754790+08:00 0 [Note] [MY-013519] [Repl] Plugin group_replication reported: 'Elected primary member applier
channel received_transaction_set: 082b900b-79d5-11ec-8fe2-00155d064000:1-32, 36ab409a-79d6-11ec-9cd5-00155d064000:1-37'
2022-01-20T22:19:11.754969+08:00 0 [System] [MY-011507] [Repl] Plugin group_replication reported: 'A new primary with address ye
jr.run:3309 was elected. The new primary will execute all previous group transactions before allowing writes.'
2022-01-20T22:19:11.755803+08:00 92 [System] [MY-011566] [Repl] Plugin group_replication reported: 'Setting super_read_only=OFF.
'
2022-01-20T22:19:12.752517+08:00 0 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Failure reading from fd=5
3 n=0'
2022-01-20T22:19:12.755961+08:00 0 [System] [MY-011503] [Repl] Plugin group_replication reported: 'Group membership changed to y
ejr.run:3309, 127.0.0.1:3310, 127.0.0.1:3311 on view 16426721489193731:9.'
2022-01-20T22:19:12.756296+08:00 91 [System] [MY-011566] [Repl] Plugin group_replication reported: 'Setting super_read_only=OFF.
'
2022-01-20T22:19:12.756744+08:00 91 [System] [MY-011510] [Repl] Plugin group_replication reported: 'This server is working as pr
imary member.'
2022-01-20T22:19:12.756787+08:00 30 [Note] [MY-011485] [Repl] Plugin group_replication reported: 'Primary had applied all relay
logs, disabled conflict detection.'
```
这就完成滚动升级了。

## 4. 小结
本文介绍了MGR集群中是如何进行选主的，当有5.7、8.0版本混合时的兼容性，以及如何把MGR 5.7滚动升级到8.0。最后多说一句，哪怕是不用MGR，8.0相对5.7还是有很多企业级特性，5.6、5.7也只能是过渡版本，最终还是强烈建议升级到8.0版本。

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