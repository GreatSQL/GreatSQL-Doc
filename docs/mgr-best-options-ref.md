在「3306π」社区广州站5月22日的分享会上，万里数据库CTO娄帅给出了他建议的配置参考，我们一起来看下：
```
group_replication_single_primary_mode=ON
log_error_verbosity=3
group_replication_bootstrap_group=OFF
group_replication_start_on_boot=OFF
group_replication_transaction_size_limit=<默认值150MB，但建议调低在20MB以内，不要使用大事务>
group_replication_communication_max_message_size=10M
group_replication_flow_control_mode="DISABLED" #官方版本的流控机制不太合理，其实可以考虑关闭
group_replication_exit_state_action=READ_ONLY
group_replication_member_expel_timeout=5 #如果网络环境不好，可以适当调高

#并行复制相关配置
slave_parallel_type = LOGICAL_CLOCK
#可以设置为逻辑CPU数量的2倍
slave_parallel_workers = 64
binlog_transaction_dependency_tracking=writeset
enforce-gtid-consistency=true
transaction_write_set_extraction=XXHASH64
```

另外，使用MGR的其他建议有：

只是用InnoDB表。
每个表都必须要有主键。
节点数采用奇数。
保证网络可靠性，低延迟环境，不要跨城部署（一般建议网络延迟低于1ms）。
使用单主模式。
BINLOG_FORMAT=ROW。

更多关于MGR的最佳使用实践，[戳此观看娄帅老师的分享视频回放](https://ke.qq.com/course/3548616?taid=11551443395159496&tuin=47bb23)。
