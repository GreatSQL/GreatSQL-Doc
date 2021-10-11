At the "3306π" community Guangzhou station on May 22, CTO of GreatDB, Lou Shuai gave his recommended configuration reference. Let's take a look:
```
group_replication_single_primary_mode=ON
log_error_verbosity=3
group_replication_bootstrap_group=OFF
group_replication_start_on_boot=OFF
group_replication_transaction_size_limit=<the default value is 150MB, but it is recommended to reduce it to less than 20MB, and do not use large transactions>
group_replication_communication_max_message_size=10M
group_replication_flow_control_mode="DISABLED" #The official version of the flow control mechanism is not reasonable, in fact, you can consider turning it off
group_replication_exit_state_action=READ_ONLY
group_replication_member_expel_timeout=5 #If the network environment is not good, you can increase it appropriately

#Parallel copy related configuration
slave_parallel_type = LOGICAL_CLOCK
#Can be set to 2 times the number of logical CPUs
slave_parallel_workers = 64
binlog_transaction_dependency_tracking=writeset
enforce-gtid-consistency=true
transaction_write_set_extraction=XXHASH64
```

In addition, other suggestions for using MGR are:
- Just use InnoDB tables.
- Every table must have a primary key.
- The number of nodes is odd(and less than 9).
- Ensure network reliability, low-latency environment, and do not deploy across cities (generally it is recommended that the network delay be less than 1ms).
- Use single master mode.
- BINLOG_FORMAT=ROW.

For more information about the best practices of MGR, [poke here to watch the video playback](https://ke.qq.com/course/3548616?taid=11551443395159496&tuin=47bb23).
