# GreatSQL FAQ

> 关于GreatSQL及MGR的FAQ，持续更新中。
>
> Last Update: 2022.01.21。

## 0. GreatSQL简介
GreatSQL是由万里数据库维护的MySQL分支，开源、免费。GreatSQL基于Percona Server，在其基础上进一步提升MGR（MySQL Group Replication）的性能及可靠性。此外，GreatSQL合并了华为鲲鹏计算团队贡献的Patch，实现了InnoDB并行查询特性，以及对InnoDB事务锁的优化。

GreatSQL可以作为MySQL或Percona Server的可选替代方案，用于线上生产环境。

GreatSQL完全免费并兼容MySQL或Percona Server。

## 1. GreatSQL的特色有哪些

相对于MySQL官方社区版，GreatSQL有以下几个优势：
- InnoDB性能更好
    - 支持InnoDB并行查询，TPC-H测试中平均提升聚合分析型SQL性能15倍，最高提升40多倍。
    - 优化InnoDB事务锁，tps性能可提升约10%。
- MGR更可靠、稳定，性能也更好。
    - MGR中引入地理标签特性，主要用于解决多机房数据同步的问题。
    - MGR中优化了流控算法，运行更加平稳。
    - 解决磁盘空间爆满时导致MGR集群阻塞的问题。
    - 解决MGR多主模式下或切主时可能导致丢数据的问题。
    - 解决节点异常退出MGR集群时导致性能抖动的问题。
    - MGR节点异常状态判断更完善。
    - 重新设计MGR事务认证队列清理算法，不复存在每隔60秒性能抖动的问题。
    - 修复了recovery过程中长时间等待的问题。
    - 修复了传输大数据可能导致逻辑判断死循环问题。
    - 修复了多数派节点不同类型异常退出集群导致的视图更新的问题。

无论是更可靠的MGR还是性能更好的InnoDB，都值得将当前的MySQL或Percona Server升级到GreatSQL。

关于GreatSQL的优势可阅读下面几篇文章：
- [GreatSQL 更新说明 8.0.25](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-20210820.md)
- [GreatSQL重磅特性，InnoDB并行并行查询优化测试](https://mp.weixin.qq.com/s/_LeEtwJlfyvIlxzLoyNVdA)
- [面向金融级应用的GreatSQL正式开源](https://mp.weixin.qq.com/s/cI_wPKQJuXItVWpOx_yNTg)

## 2. GreatSQL在哪里可以下载
### 二进制包、RPM包
二进制包下载地址：[https://gitee.com/GreatSQL/GreatSQL/releases](https://gitee.com/GreatSQL/GreatSQL/releases)。

目前提供CentOS 7、CentOS 8两种操作系统，以及X86和ARM两种不同架构下的二进制包、RPM包。

带 **minimal** 关键字的安装包是对二进制文件进行strip后，所以文件尺寸较小，功能上没本质区别，仅是不支持gdb debug功能，可以放心使用。
### 源码
可以直接用git clone的方式下载GreatSQL源码，例如：
```
# 可从gitee下载
$ git clone https://gitee.com/GreatSQL/GreatSQL.git

# 或从github下载
$ git clone https://github.com/GreatSQL/GreatSQL.git
```

### Ansible安装包
GreatSQL提供Ansible一键安装包，可在gitee或github下载：
- https://gitee.com/GreatSQL/GreatSQL-Ansible/releases
- https://github.com/GreatSQL/GreatSQL-Ansible/releases

### Docker镜像
GreatSQL提供Docker镜像，可直接从docker hub拉取：
```
# 直接下载最新版本
$ docker pull docker.io/greatsql/greatsql

# 或自行指定版本
$ docker pull docker.io/greatsql/greatsql:8.0.25

# 或指定ARM版本
$ docker pull docker.io/greatsql/greatsql:8.0.25-aarch64
```

## 3. 使用GreatSQL遇到问题时找谁

使用GreatSQL过程中如果遇到问题，可将问题细节整理清楚后，联系GreatSQL社区寻求帮助。

扫码添加GreatSQL社区助手<br/>
![输入图片说明](greatsql-wx-assist.jpg)

或扫码加入GreatSQL社区QQ群（533341697）<br/>
![输入图片说明](greatsql-qqqun.jpg)

此外，我们已经在B站发布MGR相关系列视频，可以前往学习，视频链接：[https://space.bilibili.com/1363850082](https://space.bilibili.com/1363850082) 。

## 4. GreatSQL版本计划是怎样的
GreatSQL不计划每个小版本都跟随，暂定奇数版本跟随方式，即 8.0.25、8.0.27、8.0.29 ... 以此类推。

未来若有版本计划变更我们再更新。

## 5. GreatSQL支持读写分离吗
可以利用MySQL Router来实现读写分离。

## 6. 可以使用MySQL Shell来管理GreatSQL吗
是可以的，最好采用相同版本号的MySQL Shell即可。

## 7. 使用MGR有什么限制吗
下面是关于MGR使用的一些限制：
- 所有表必须是InnoDB引擎。可以创建非InnoDB引擎表，但无法写入数据，在利用Clone构建新节点时也会报错。
- 所有表都必须要有主键。同上，能创建没有主键的表，但无法写入数据，在利用Clone构建新节点时也会报错。
- 不要使用大事务，默认地，事务超过150MB会报错，最大可支持2GB的事务（在GreatSQL未来的版本中，会增加对大事务的支持，提高大事务上限）。
- 如果是从旧版本进行升级，则不能选择 MINIMAL 模式升级，建议选择 AUTO 模式，即 `upgrade=AUTO`。
- 由于MGR的事务认证线程不支持 `gap lock`，因此建议把所有节点的事务隔离级别都改成 `READ COMMITTED`。基于相同的原因，MGR集群中也不要使用 `table lock` 及 `name lock`（即 `GET_LOCK()` 函数 ）。
- 在多主（`multi-primary`）模式下不支持串行（`SERIALIZABLE`）隔离级别。
- 不支持在不同的MGR节点上，对同一个表分别执行DML和DDL，可能会造成数据丢失或节点报错退出。
- 在多主（`multi-primary`）模式下不支持多层级联外键表。另外，为了避免因为使用外键造成MGR报错，建议设置 `group_replication_enforce_update_everywhere_checks=ON`。
- 在多主（`multi-primary`）模式下，如果多个节点都执行 `SELECT ... FOR UPDATE` 后提交事务会造成死锁。
- 不支持复制过滤（Replication Filters）设置。

看起来限制有点多，但绝大多数时候并不影响正常的业务使用。

此外，想要启用MGR还有几个要求：
- 每个节点都要启用binlog。
- 每个节点都要转存binlog，即设置 `log_slave_updates=1`。
- binlog format务必是row模式，即 `binlog_format=ROW`。
- 每个节点的 `server_id` 及 `server_uuid` 不能相同。
- 在8.0.20之前，要求 `binlog_checksum=NONE`，但是从8.0.20后，可以设置 `binlog_checksum=CRC32`。
- 要求启用 GTID，即设置 `gtid_mode=ON`。
- 要求 `master_info_repository=TABLE` 及 `relay_log_info_repository=TABLE`，不过从MySQL 8.0.23开始，这两个选项已经默认设置TABLE，因此无需再单独设置。
- 所有节点上的表名大小写参数 `lower_case_table_names` 设置要求一致。
- 最好在局域网内部署MGR，而不要跨公网，网络延迟太大的话，会导致MGR性能很差或很容易出错。
- 建议启用writeset模式，即设置以下几个参数
    - `slave_parallel_type = LOGICAL_CLOCK`
    - `slave_parallel_workers = N`，N>0，可以设置为逻辑CPU数的2倍
    - `binlog_transaction_dependency_tracking = WRITESET`
    - `slave_preserve_commit_order = 1`
    - `slave_checkpoint_period = 2`

## 8. MGR最多可支持多少个节点
MGR最多可支持9个节点，无论是单主还是多主模式。

## 9. MGR可以设置为自启动吗
设置参数 `group_replication_bootstrap_group=ON` 即可。但是当MGR第一个节点初始化启动时，或者整个MGR集群都关闭再重启时，第一个节点都必须先采用引导模式 `group_replication_bootstrap_group=ON`。

## 10. MGR支持读负载均衡吗
支持的。可以在MGR集群的前端挂载MySQL Router，即可实现读负载均衡。

## 11. MGR支持写负载均衡吗
不支持。由于MGR采用shared nothing模式，每个节点都存储全量数据，因此所有写入每个节点都要再应用一次。

## 12. MGR相对传统主从复制是不是会更耗CPU、内存和带宽等资源
一定程度上来说，是的。因为MGR需要在多个节点间进行事务冲突检测，不过这方面的开销有限，总体来说也还好。

## 13. 为什么启动MGR后，多了个33061端口
当启用MGR服务后，MySQL会监听33061端口，该端口用于MGR节点间的通信。因此当服务器间有防火墙策略时，记得针对该端口开放。

当然了，可自行定义该端口，例如 `group_replication_local_address=192.168.0.1:33062`。

## 14. 部署MGR时，务必对所有节点都设置hostname吗
这个不是必须的。

之所以要在每个节点上都加上各节点的hostname对照表，是因为在MGR节点间通信过程中，可能收到的主机名和本地实际配置的不一致。

这种情况下，也可以在每个节点上自行设置 `report_host` 及 `report_port` 来解决这个问题。

## 15. 可以跨公网部署MGR吗
可以的，但非常不推荐。

此外，由于MGR默认的allowlist不包含公网地址，因此需要将公网地址加进去，例如：
```
group_replication_ip_allowlist='192.0.2.0/24, 114.114.114.0/24'
```

顺便提醒下，MGR默认的allowlist范围（`group_replication_ip_allowlist=AUTOMATIC`）是以下几个
```
IPv4 (as defined in RFC 1918)
10/8 prefix       (10.0.0.0 - 10.255.255.255) - Class A
172.16/12 prefix  (172.16.0.0 - 172.31.255.255) - Class B
192.168/16 prefix (192.168.0.0 - 192.168.255.255) - Class C

IPv6 (as defined in RFC 4193 and RFC 5156)
fc00:/7 prefix    - unique-local addresses
fe80::/10 prefix  - link-local unicast addresses

127.0.0.1 - localhost for IPv4
::1       - localhost for IPv6
```
有时候docker容器的IP地址不在上述范围中，也会导致MGR服务无法启动。

## 16. 怎么查看MGR当前是单主还是多主模式
执行下面的命令：
```
[root@GreatSQL]> SELECT * FROM performance_schema.replication_group_members;
+---------------------------+-----------...-+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID ... | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+-----------...-+-------------+--------------+-------------+----------------+
| group_replication_applier | 4ebd3504-1... |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | 549b92bf-1... |        3307 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | 5596116c-1... |        3308 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | ed5fe7ba-3... |        3309 | ONLINE       | PRIMARY     | 8.0.25         |
+---------------------------+-----------...-+-------------+--------------+-------------+----------------+
```
如果只看到一个节点的 `MEMBER_ROLE` 值为 **PRIMARY**，则表示这是单主模式。如果看到所有节点上该状态值均为 **PRIMARY**，则表示这是多主模式。

另外，也可以通过查询MySQL选项值来确认：
```
[root@GreatSQL]# mysqladmin var|grep -i group_replication_single_primary_mode
| group_replication_single_primary_mode        | ON
```
值为 **ON**，这表示采用单主模式。如果该值为 **OFF**，则表示采用多主模式。

在MySQL Shell中也可以查看状态来确认：
```
MySQL  GreatSQL:3306 ssl  JS > var c=dba.getCluster()
MySQL  GreatSQL:3306 ssl  JS > c.describe() /* 或者 c.status() */
...
        "topologyMode": "Single-Primary"
...
```

P.S，强烈建议采用单主模式，遇到bug或其他问题的概率更低，运行MGR更稳定可靠。

## 17. 怎么切换单主或多主
在MySQL客户端命令行模式下，执行下面的命令即可：
```
-- 从单主切换为多主
[root@GreatSQL]> SELECT group_replication_switch_to_multi_primary_mode();
+--------------------------------------------------+
| group_replication_switch_to_multi_primary_mode() |
+--------------------------------------------------+
| Mode switched to multi-primary successfully.     |
+--------------------------------------------------+

-- 从多主切换为单主
[root@GreatSQL]> SELECT group_replication_switch_to_single_primary_mode();
+---------------------------------------------------+
| group_replication_switch_to_single_primary_mode() |
+---------------------------------------------------+
| Mode switched to single-primary successfully.     |
+---------------------------------------------------+
```
**注意：** 切换时会重新选主，新的主节点有可能不是切换之前的那个，这时可以运行下面的命令来重新指定：
```
[root@GreatSQL]> SELECT group_replication_set_as_primary('ed5fe7ba-37c2-11ec-8e12-70b5e873a570');
+--------------------------------------------------------------------------+
| group_replication_set_as_primary('ed5fe7ba-37c2-11ec-8e12-70b5e873a570') |
+--------------------------------------------------------------------------+
| Primary server switched to: ed5fe7ba-37c2-11ec-8e12-70b5e873a570         |
+--------------------------------------------------------------------------+
```

也可以通过MySQL Shell来操作：
```
MySQL  GreatSQL:3306 ssl  JS > var c=dba.getCluster()
> c.switchToMultiPrimaryMode()  /*切换为多主模式*/
Switching cluster 'MGR27' to Multi-Primary mode...

Instance 'GreatSQL:3306' was switched from SECONDARY to PRIMARY.
Instance 'GreatSQL:3307' was switched from SECONDARY to PRIMARY.
Instance 'GreatSQL:3308' was switched from SECONDARY to PRIMARY.
Instance 'GreatSQL:3309' remains PRIMARY.

The cluster successfully switched to Multi-Primary mode.

> c.switchToSinglePrimaryMode()  /*切换为单主模式*/
Switching cluster 'MGR27' to Single-Primary mode...

Instance 'GreatSQL:3306' remains PRIMARY.
Instance 'GreatSQL:3307' was switched from PRIMARY to SECONDARY.
Instance 'GreatSQL:3308' was switched from PRIMARY to SECONDARY.
Instance 'GreatSQL:3309' was switched from PRIMARY to SECONDARY.

WARNING: The cluster internal session is not the primary member anymore. For cluster management operations please obtain a fresh cluster handle using dba.getCluster().

WARNING: Existing connections that expected a R/W connection must be disconnected, i.e. instances that became SECONDARY.

The cluster successfully switched to Single-Primary mode.

> c.setPrimaryInstance('GreatSQL:3309');  /*重新设置主节点*/
Setting instance 'GreatSQL:3309' as the primary instance of cluster 'MGR27'...

Instance 'GreatSQL:3306' was switched from PRIMARY to SECONDARY.
Instance 'GreatSQL:3307' remains SECONDARY.
Instance 'GreatSQL:3308' remains SECONDARY.
Instance 'GreatSQL:3309' was switched from SECONDARY to PRIMARY.

The instance 'GreatSQL:3309' was successfully elected as primary.
```

P.S，强烈建议采用单主模式，遇到bug或其他问题的概率更低，运行MGR更稳定可靠。

## 18. 怎么查看MGR从节点是否有延迟
首先，可以执行下面的命令查看当前除了 **PRIMARY** 节点外，其他节点的 `trx_tobe_applied` 或 `trx_tobe_verified` 值是否较大：
```
[root@GreatSQL]> SELECT MEMBER_ID AS id, COUNT_TRANSACTIONS_IN_QUEUE AS trx_tobe_verified, COUNT_TRANSACTIONS_REMOTE_IN_APPLIER_QUEUE AS trx_tobe_applied, COUNT_TRANSACTIONS_CHECKED AS trx_chkd, COUNT_TRANSACTIONS_REMOTE_APPLIED AS trx_done, COUNT_TRANSACTIONS_LOCAL_PROPOSED AS proposed FROM performance_schema.replication_group_member_stats;
+--------------------------------------+-------------------+------------------+----------+----------+----------+
| id                                   | trx_tobe_verified | trx_tobe_applied | trx_chkd | trx_done | proposed |
+--------------------------------------+-------------------+------------------+----------+----------+----------+
| 4ebd3504-11d9-11ec-8f92-70b5e873a570 |                 0 |                0 |   422248 |        6 |   422248 |
| 549b92bf-11d9-11ec-88e1-70b5e873a570 |                 0 |           238391 |   422079 |   183692 |        0 |
| 5596116c-11d9-11ec-8624-70b5e873a570 |              2936 |           238519 |   422115 |   183598 |        0 |
| ed5fe7ba-37c2-11ec-8e12-70b5e873a570 |              2976 |           238123 |   422167 |   184044 |        0 |
+--------------------------------------+-------------------+------------------+----------+----------+----------+
```
其中，`trx_tobe_applied` 的值表示等待被apply的事务队列大小，`trx_tobe_verified` 表示等待被认证的事务队列大小，这二者任何一个值大于0，都表示当前有一定程度的延迟。

另外，也可以查看接收到的事务和已执行完的事务之间的差距来判断：
```
[root@GreatSQL]> SELECT RECEIVED_TRANSACTION_SET FROM performance_schema.replication_connection_status WHERE  channel_name = 'group_replication_applier' UNION ALL SELECT variable_value FROM performance_schema.global_variables WHERE  variable_name = 'gtid_executed'\G
*************************** 1. row ***************************
RECEIVED_TRANSACTION_SET: 6cfb873b-573f-11ec-814a-d08e7908bcb1:1-3124520
*************************** 2. row ***************************
RECEIVED_TRANSACTION_SET: 6cfb873b-573f-11ec-814a-d08e7908bcb1:1-3078139
```
可以看到，接收到的事务 GTID 已经到了 3124520，而本地只执行到 3078139，二者的差距是 46381。可以顺便持续关注这个差值的变化情况，估算出本地节点是否能追平延迟，还是会加大延迟。


## 19. MySQL Router支持单机多实例部署吗
是的，支持。
在MySQL Router初始化部署时，添加 `--name`、`--directory` 及端口号等参数即可，例如：
```
-- 部署第一个实例
root@GreatSQL# mysqlrouter --bootstrap mymgr@192.168.1.1:3306 --name=MGR1 --directory=/etc/mysqlrouter/MGR1  --user=mysqlrouter --conf-base-port=6446 --https-port=8443

-- 部署第二个实例
root@GreatSQL# mysqlrouter --bootstrap mymgr@192.168.1.1:4306 --name=MGR2 --directory=/etc/mysqlrouter/MGR2  --user=mysqlrouter --conf-base-port=7446 --https-port=9443
```
然后每个实例用各自目录下的 `start.sh` 和 `stop.sh` 脚本启停即可。

关于MySQL Router多实例部署的方法，可以参考这篇参考文档：[**《叶问》38期，MGR整个集群挂掉后，如何才能自动选主，不用手动干预**](https://mp.weixin.qq.com/s/9eLnQ2EJIMQnZuEvScIhiw)。

## 20. 两个MGR集群间还可以构建主从复制关系吗
首先，答案是肯定的，可以的。

其次，为了保障MGR的数据安全性，对不同角色节点的要求是这样的：
- 在单主模式（Single-Primary）时，从节点（Secondary）不能同时作为Master-Slave的从节点（Slave）
- 在单主模式时，主节点（Primary）可以同时作为M-S的从节点（Slave）
- 在多主模式时，任何节点可以作为MS的从节点（Slave）。提醒：强烈建议不要使用多主模式
- 要求都是InnoDB表，且没有数据冲突（例如数据重复、数据不存在等），没有使用外键
- 节点重启时，注意要先启动MGR服务，再启动M-S服务。这时候可以设置 `group_replication_start_on_boot=ON` 和 `skip_slave_start=ON` 予以保证

在这两个MGR集群间的主从复制可以采用异步复制，也可以采用半同步复制，主要取决于两个集群间的网络延迟情况及架构设计方案。这时候，整体架构方案类似下面这样：
![两个MGR间构建M-S复制架构](6.%E5%90%8C%E5%9F%8EMGR.png)

在这个架构下，两个MGR集群间是相互独立的，如果前端挂载MySQL Router的话，需要单独创建对应的连接。

如果担心MGR节点因为发生切换，只要原来指向的Master没有退出MGR集群，则这个主从复制关系还是存在的，不受影响。如果担心原来的Master节点退出MGR集群而导致复制中断，则可以采用MySQL 8.0.22后推出的新特性 **Async Replication Auto failover** 来解决，把各节点都加到复制源中，可以参考下面的资料：
- [金融应用场景下跨数据中心的MGR架构方案](https://mp.weixin.qq.com/s/A3yJUz6DNvCgIfqD78t_qQ)
- [Switching Sources and Replicas with Asynchronous Connection Failover](https://dev.mysql.com/doc/refman/8.0/en/replication-asynchronous-connection-failover.html)
- [视频：MGR是如何保障数据一致性的](https://www.bilibili.com/video/BV1NT4y1R7Zi)

## 21. 三节点的MGR集群，有两个节点宕机后还能正常工作吗
要看具体是哪种情况。

如果两个节点是正常关闭的话，则会向MGR集群发送退出信号，这种情况下，这两个节点属于正常退出，最后仅剩的节点会被提升为Primary角色，还可以正常工作，允许对其进行读写，只是此时没有可用性冗余了。当其他节点再次启动并加入集群后，又能恢复正常服务。

如果是因为网络故障，或者mysqld进程发生oom、或被误杀、或其他原因退出了，则这些节点会被标识为 **UNREACHABLE** 状态，等待直到 `group_replication_member_expel_timeout` 时长（单位：秒）后这个节点才会正式退出集群。在这种情况下，一旦超过多数派节点处于 **UNREACHABLE** 状态时，则整个集群不可用，无法提供读写服务。这种情况下，需要把剩下的节点重启MGR服务才能恢复。

正常情况下，不要把 `group_replication_member_expel_timeout` 值调整太大，并且MGR的事务一致性级别尽量不要选择 **AFTER** 模式，以防出现整个集群服务不可用的问题，详细参见这篇文章：[为什么MGR一致性模式不推荐AFTER](https://mp.weixin.qq.com/s/zy0VUgF_5gJuZYbzNVxPXA)。

## 22. MGR可以像主从复制那样只启动两个节点吗
MGR在初始化启动时，是可以只启动两个节点，甚至只有一个节点，但是这样就失去MGR的意义了。**因为只要少于三个节点，就没办法进行多数派投票**，当发生网络故障等情况时，无法投票确认哪些节点该被踢出集群。

## 23. MGR中可以创建无主键的InnoDB表吗
是可以的，并且会复制到所有MGR节点，但是仅能创建空表，业务上不能写入数据。

往无主键的InnoDB表中写入数据时，会报告类似下面的错误：
```
[root@GreatSQL] [test]> insert into t3 select 1;
ERROR 3098 (HY000): The table does not comply with the requirements by an external plugin.
```
同理，也可以创建MyISAM表，但写入时会提示失败。

此外，当欲加入MGR集群的新实例中有无主键的InnoDB表时，如果要通过 **MySQL Shell** 添加该节点，会发出类似下面的报错，无法加入：
```
Validating instance configuration at mgr03:3306...

This instance reports its own address as mgr03:3306
ERROR: The following tables do not have a Primary Key or equivalent column:
test.t3

Group Replication requires tables to use InnoDB and have a PRIMARY KEY or PRIMARY KEY Equivalent (non-null unique key). Tables that do not follow these requirements will be readable but not updateable when used with Group Replication. If your applications make updates (INSERT, UPDATE or DELETE) to these tables, ensure they use the InnoDB storage engine and have a PRIMARY KEY or PRIMARY KEY Equivalent.
If you can't change the tables structure to include an extra visible key to be used as PRIMARY KEY, you can make use of the INVISIBLE COLUMN feature available since 8.0.23: https://dev.mysql.com/doc/refman/8.0/en/invisible-columns.html

ERROR: Instance must be configured and validated with dba.checkInstanceConfiguration() and dba.configureInstance() before it can be used in an InnoDB cluster.
Cluster.addInstance: Instance check failed (RuntimeError)
```
这个报错在MySQL 8.0.25依然存在，据说在MySQL 8.0.27得到解决。

如果改成手动加入新节点，或者直接删除无主键表，则可以成功。

从上面的错误提示也能看出来，如果创建一个和主键等价的唯一索引（且要求不允许为NULL），该唯一索引可用做InnoDB表的聚集索引，就不会再报错了，业务也能正常写入数据。

## 24. MySQL Router可以配置在MGR主从节点间轮询吗
MySQL Router通过两个端口来区分读写服务请求，默认是 6446端口提供读写服务，6447端口提供只读服务。
在单主模式下，读写服务只会连接到Primary节点。对于读写服务端口，可选的策略有以下两种：
- first-available，只连接第一个可用节点
- round-robin（默认），在多个主节点间轮询

只读服务默认是对所有Secondary节点轮询。对于只读服务端口，可选的策略有以下X种：
- first-available，只连第一个可用节点
- round-robin，在所有可用Secondary节点间轮询，如果所有Secondary节点都不可用时，只读服务则不可用，不会连接到Primary节点
- round-robin-with-fallback（默认），在所有Secondary节点间轮询。如果所有Secondary节点都不可用时，会再连接到Primary节点

现在我们知道了，MySQL Router只有在所有Secondary节点都不可用时，才会去连接Primary节点读数据，无法做到在发起只读请求时，同时连接主从节点。

更多关于 MySQL Router 可用的策略请参见文档 **[routing_strategy参数/选项](https://dev.mysql.com/doc/mysql-router/8.0/en/mysql-router-conf-options.html#option_mysqlrouter_routing_strategy)**。

## 25. 都有哪些情况可能导致MGR服务无法启动
简单整理了下，大概有以下原因可能导致MGR服务无法启动：
1. 网络原因，例如网络本来就不通，或被防火墙拦住。防火墙通常至少有两道，操作系统默认的firewall策略，以及云主机被默认的安全策略。
2. 第一个启动的节点没先做初始引导操作（`group_replication_bootstrap_group=ON`）。
3. 没有正确配置group_name，所有节点的 `group_replication_group_name` 值要一致才可以。
4. 没正确配置 `group_replication_group_name`，常见于新手。要为MGR服务专门新开一个服务端口，常用33061端口，但新手可能会照样写成3306端口。
5. 通常，我们会在各MGR节点的 hosts 文件里加上所有节点的hostname。这是为了防止本地节点使用的hostname和MGR收到的hostname不一致，这种情况下，可以在每个本地节点设置 `report-host`，主动上报hostname即可解决。
7. 没设置正确的allowlist。有可能加入MGR各节点的IP不在默认的allowlist中，可参考这篇文章：[MySQL Group Replication集群对IP地址的限制导致的一些问题与解决办法](https://mp.weixin.qq.com/s/sbYufrlOx4cKiT8sV3hCaw)。
8. 个别节点的本地事务更多，例如误操作写入数据，也会无法加入MGR，这种情况需要重建本地节点。
9. 个别节点的本地事务缺失太多，且加入MGR时无法自动完成恢复，这种情况比较少见，需要手动执行clone复制数据，或者其他类似操作。

## 26. MySQL Shell 8.0能管理MySQL 5.7的MGR集群吗
答案是肯定的。

不过由于MySQL 5.7里没有MGR管理的几个UDF，因此在MySQL Shell里调用 `setPrimaryInstance()`、`switchToMultiPrimaryMode()` 等函数时会报错，是不支持的。

所以说，还是尽量升级到MySQL 8.0吧。