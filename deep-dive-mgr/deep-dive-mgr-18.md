# 18. 最佳实践参考 | 深入浅出MGR

本文介绍MGR最佳实践参考以及使用MGR的约束限制。

## 1. 参数选项设置
下面是几个MGR相关参数选项设置建议：
```
#建议只用单主模式
loose-group_replication_single_primary_mode=ON

#不要启用引导模式
loose-group_replication_bootstrap_group=OFF 

#默认值150MB，但建议调低在20MB以内，不要使用大事务
loose-group_replication_transaction_size_limit = 10M

#大消息分片处理，每个分片10M，避免网络延迟太大
loose-group_replication_communication_max_message_size = 10M

#节点退出后的默认行为，将本节点设置为RO模式
loose-group_replication_exit_state_action = READ_ONLY

#超过多长时间收不到广播消息就认定为可疑节点，如果网络环境不好，可以适当调高
loose-group_replication_member_expel_timeout = 5

#建议关闭MySQL流控机制
loose-group_replication_flow_control_mode = "DISABLED"

#AFTER模式下，只要多数派达成一致就可以，不需要全部节点一致
loose-group_replication_majority_after_mode = ON

#是否设置为仲裁节点
loose-group_replication_arbitrator = 0

#启用快速单主模式
loose-group_replication_single_primary_fast_mode = 1

#当MGR层耗时超过100ms就记录日志，确认是否MGR层的性能瓶颈问题
loose-group_replication_request_time_threshold = 100

#记录更多日志信息，便于跟踪问题
log_error_verbosity=3
```

## 2. MGR相关约束
下面是关于MGR使用的一些限制：
- 所有表必须是InnoDB引擎。可以创建非InnoDB引擎表，但无法写入数据，在利用Clone构建新节点时也会报错（在GreatSQL中，可以设置选项 `enforce_storage_engine = InnoDB` 只允许使用InnoDB引擎，而禁用其他引擎）。
- 所有表都必须要有主键。同上，能创建没有主键的表，但无法写入数据，在利用Clone构建新节点时也会报错。
- 尽量不要使用大事务，默认地，事务超过150MB会报错，最大可支持2GB的事务（在GreatSQL未来的版本中，会增加对大事务的支持，提高大事务上限，但依然不建议运行大事务）。
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
- 要求启用 GTID，即设置 `gtid_mode=ON` 及 `enforce_gtid_consistency=ON`。
- 要求 `master_info_repository=TABLE` 及 `relay_log_info_repository=TABLE`，不过从MySQL 8.0.23开始，这两个选项已经默认设置TABLE，因此无需再单独设置。
- 所有节点上的表名大小写参数 `lower_case_table_names` 设置要求一致。
- 最好在局域网内部署MGR，而不要跨公网，网络延迟太大的话，会导致MGR性能很差或很容易出错。
- 建议启用writeset模式，即设置以下几个参数
    - `slave_parallel_type = LOGICAL_CLOCK`
    - `slave_parallel_workers = N`，N>0，可以设置为逻辑CPU数的2倍
    - `binlog_transaction_dependency_tracking = WRITESET`
- `slave_preserve_commit_order = 1`
    - `slave_checkpoint_period = 2`


## 3. MGR使用建议
在使用MGR时，有以下几个建议：
- 不同版本不要混用，尤其是不同大版本不要混用，要尽快完成升级。
- 对同一个表的DDL和DML都只在同一个节点，否则可能会造成节点意外退出MGR。
- 不要跑大事务，每个事务尽量控制在10MB以内。


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
