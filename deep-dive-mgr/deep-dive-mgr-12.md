# 12. 新节点加入过程解读 | 深入浅出MGR

本文从日志解读MGR节点加入过程。

## 1. 从日志理解（手动）加入新节点过程
新节点加入MGR集群时，通过观察它的日志（设置 `log_error_verbosity=3` 日志中能记录更多信息，便于跟踪和排查故障），能更好的理解MGR的工作过程及数据同步机制。

下面是（命令行手工操作方式，不是通过MySQL Shell调用）新节点加入时，从Primary节点看到的日志（对时间戳、主机名等做了简单处理）：
```
-- 1. 确定当前集群中已存在的三个节点
17:05:48.297323 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 0 host 127.0.0.1'
17:05:48.297347 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 1 host 127.0.0.1'
17:05:48.297351 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 2 host 127.0.0.1'
-- 2. 有新节点要加入了
17:05:48.297355 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 3 host 127.0.0.1'
17:05:48.297373 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 6541 Installed site start={ff389be 7249 0} boot_key={ff389be 7238 0} event_horizon=10 node 0 chksum_node_list(&site->nodes) 3840072444'
-- 3. 准备进行view change
17:05:48.959766 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:05:48.959828 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'on_suspicions is activated'
17:05:48.959847 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'on_suspicions is called over'
17:05:48.959853 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view return true'
17:05:48.960279 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::xcom_receive_global_view() is called'
17:05:49.960937 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_communication do_send_message CT_INTERNAL_STATE_EXCHANGE'
17:05:49.961025 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::xcom_receive_global_view():: state exchange started.'
17:05:49.961207 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:05:49.961227 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:05:49.961352 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:05:49.961392 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:05:49.961436 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:05:49.961445 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:05:49.961451 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:05:49.961457 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
- 4. 确认通信协议版本
17:05:49.961466 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Group is able to support up to communication protocol version 8.0.16'
-- 5. 确认新节点可以加入，准备修改view
17:05:49.961472 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message()::Install new view'
17:05:49.961479 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:05:49.961482 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:05:49.961486 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:05:49.961491 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:05:49.961498 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'on_view_changed is called'
-- 6. 新节点成功加入
17:05:49.961538 [Note] [MY-011501] [Repl] Plugin group_replication reported: 'Members joined the group: 127.0.0.1:3312'
-- 7. 准备是否需要进行新主选举
17:05:49.961565 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'handle_leader_election_if_needed is activated,suggested_primary:'
-- 8. 确认新的view
17:05:49.961591 [System] [MY-011503] [Repl] Plugin group_replication reported: 'Group membership changed to 127.0.0.1:3312, 127.0.0.1:3311, 127.0.0.1:3310, 127.0.0.1:3309 on view 16444111732158542:6.'
-- 9. 启动binlog dump线程发送日志
17:05:51.033352 [Note] [MY-010462] [Repl] Start binlog_dump to master_thread_id(49) slave_server(3312), pos(, 4)
-- 10. 数据同步完成，宣告新节点转成online状态，正式加入MGR集群
17:05:51.157744 [System] [MY-011492] [Repl] Plugin group_replication reported: 'The member with address 127.0.0.1:3312 was declared online within the replication group.'
```

再看看Secondary节点上的日志，看看站在Secondary节点角度加入集群的过程是怎样的：
```
-- 1. 启动MGR服务
17:05:48.204524 12 [System] [MY-013587] [Repl] Plugin group_replication reported: 'Plugin 'group_replication' is starting.'
17:05:48.204580 12 [Note] [MY-011716] [Repl] Plugin group_replication reported: 'Current debug options are: 'GCS_DEBUG_NONE'.'
-- 2. 设置super RO
17:05:48.205440 14 [System] [MY-011565] [Repl] Plugin group_replication reported: 'Setting super_read_only=ON.'
17:05:48.205531 12 [Note] [MY-011673] [Repl] Plugin group_replication reported: 'Group communication SSL configuration: group_replication_ssl_mode: "DISABLED"'
17:05:48.205989 12 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Debug messages will be sent to: asynchronous::/data/GreatSQL/mgr07/GCS_DEBUG_TRACE'
-- 3. 添加allowlist
17:05:48.206099 12 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Added automatically IP ranges 127.0.0.1/8,192.168.5.170/24,192.168.6.27/24,::1/128,fe80::215:5dff:fe06:4000/64 to the allowlist'
17:05:48.206230 12 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] SSL was not enabled'
-- 4. 初始化MGR相关选项
17:05:48.206248 12 [Note] [MY-011694] [Repl] Plugin group_replication reported: 'Initialized group communication with configuration: group_replication_group_name: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaabb1'; group_replication_local_address: '127.0.0.1:33121'; group_replication_group_seeds: '127.0.0.1:33091,127.0.0.1:33101,127.0.0.1:33111'; group_replication_bootstrap_group: 'false'; group_replication_poll_spin_loops: 0; group_replication_compression_threshold: 1000000; group_replication_ip_allowlist: 'AUTOMATIC'; group_replication_communication_debug_options: 'GCS_DEBUG_NONE'; group_replication_member_expel_timeout: '5'; group_replication_communication_max_message_size: 1048576; group_replication_message_cache_size: '1073741824u''
-- 5. 向MGR集群报告本地节点的几个设置
17:05:48.206281 12 [Note] [MY-011643] [Repl] Plugin group_replication reported: 'Member configuration: member_id: 3312; member_uuid: "5596116c-11d9-11ec-8624-70b5e873a570"; single-primary mode: "true"; group_replication_auto_increment_increment: 7; '
17:05:48.206304 12 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'Init certifier broadcast thread'
17:05:48.226848 15 [System] [MY-010597] [Repl] 'CHANGE MASTER TO FOR CHANNEL 'group_replication_applier' executed'. Previous state master_host='', master_port= 3306, master_log_file='', master_log_pos= 4, master_bind=''. New state master_host='<NULL>', master_port= 0, master_log_file='', master_log_pos= 4, master_bind=''.
17:05:48.259289 12 [Note] [MY-011670] [Repl] Plugin group_replication reported: 'Group Replication applier module successfully initialized!'
17:05:48.259341 18 [Note] [MY-010581] [Repl] Slave SQL thread for channel 'group_replication_applier' initialized, starting replication in log 'FIRST' at position 0, relay log './yejr-relay-bin-group_replication_applier.000001' position: 4
17:05:48.296509 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] XCom protocol version: 9'
17:05:48.296549 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] XCom initialized and ready to accept incoming connections on port 33121'
-- 6. MGR集群准备创建新节点
17:05:48.858593 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 0 host 127.0.0.1'
17:05:48.858742 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 7558 Installed site start={ff389be 1279 1} boot_key={ff389be 1268 1} event_horizon=10 node 4294967295 chksum_node_list(&site->nodes) 4245557582'
17:05:48.858841 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 0 host 127.0.0.1'
17:05:48.858857 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 1 host 127.0.0.1'
17:05:48.858906 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 7558 Installed site start={ff389be 1882 0} boot_key={ff389be 1871 0} event_horizon=10 node 4294967295 chksum_node_list(&site->nodes) 1527260973'
17:05:48.859040 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 0 host 127.0.0.1'
17:05:48.859060 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 1 host 127.0.0.1'
17:05:48.859071 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 2 host 127.0.0.1'
17:05:48.859121 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 7558 Installed site start={ff389be 2895 0} boot_key={ff389be 2884 0} event_horizon=10 node 4294967295 chksum_node_list(&site->nodes) 4067201187'
17:05:48.859187 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 0 host 127.0.0.1'
17:05:48.859199 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 1 host 127.0.0.1'
17:05:48.859248 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 2 host 127.0.0.1'
17:05:48.859259 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 3 host 127.0.0.1'
-- 7. 准备修改view
17:05:48.859344 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 7558 Installed site start={ff389be 7249 0} boot_key={ff389be 7238 0} event_horizon=10 node 3 chksum_node_list(&site->nodes) 3840072444'
17:05:48.860647 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Rejecting this message. The member is not in a view yet.'
17:05:48.860719 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Rejecting this message. The member is not in a view yet.'
17:05:48.860742 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:05:48.959946 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:05:48.960165 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:05:48.960385 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::xcom_receive_global_view() is called'
17:05:49.961045 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_communication do_send_message CT_INTERNAL_STATE_EXCHANGE'
17:05:49.961093 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::xcom_receive_global_view():: state exchange started.'
17:05:49.961109 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:05:49.961207 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:05:49.961224 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:05:49.961327 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:05:49.961341 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:05:49.961349 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:05:49.961352 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:05:49.961361 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:05:49.961370 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
-- 8. 确认通信协议版本
17:05:49.961376 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] This server adjusted its communication protocol to 8.0.16 in order to join the group.'
17:05:49.961381 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Group is able to support up to communication protocol version 8.0.16'
17:05:49.961387 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message()::Install new view'
17:05:49.961403 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:05:49.961412 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:05:49.961416 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:05:49.961419 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:05:49.961423 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'on_view_changed is called'
-- 9. 新的secondary节点加入成功
17:05:49.961526 12 [System] [MY-011511] [Repl] Plugin group_replication reported: 'This server is working as secondary member with primary member address 127.0.0.1:3309.'
-- 10. 开始分布式恢复，确认donor节点
17:05:50.961988 [System] [MY-013471] [Repl] Plugin group_replication reported: 'Distributed recovery will transfer data using: Incremental recovery from a group donor'
17:05:50.962330 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'handle_leader_election_if_needed is activated,suggested_primary:'
17:05:50.962338 26 [Note] [MY-011576] [Repl] Plugin group_replication reported: 'Establishing group recovery connection with a possible donor. Attempt 1/10'
-- 11. 更新view，版本增加1
17:05:50.962379 [System] [MY-011503] [Repl] Plugin group_replication reported: 'Group membership changed to 127.0.0.1:3312, 127.0.0.1:3311, 127.0.0.1:3310, 127.0.0.1:3309 on view 16444111732158542:6.'
17:05:50.994620 26 [System] [MY-010597] [Repl] 'CHANGE MASTER TO FOR CHANNEL 'group_replication_recovery' executed'. Previous state master_host='', master_port= 3306, master_log_file='', master_log_pos= 4, master_bind=''. New state master_host='127.0.0.1', master_port= 3309, master_log_file='', master_log_pos= 4, master_bind=''.
-- 12. 确认donor节点是127.0.0.1:3309，并开始恢复数据
17:05:51.010351 26 [Note] [MY-011580] [Repl] Plugin group_replication reported: 'Establishing connection to a group replication recovery donor e81475c1-89a5-11ec-bc8b-00155d064000 at 127.0.0.1 port: 3309.'
17:05:51.010616 27 [Warning] [MY-010897] [Repl] Storing MySQL user name or password information in the master info repository is not secure and is therefore not recommended. Please consider using the USER and PASSWORD connection options for START SLAVE; see the 'START SLAVE Syntax' in the MySQL Manual for more information.
17:05:51.011019 27 [System] [MY-010562] [Repl] Slave I/O thread for channel 'group_replication_recovery': connected to master 'repl@127.0.0.1:3309',replication started in log 'FIRST' at position 4
17:05:51.032633 28 [Note] [MY-010581] [Repl] Slave SQL thread for channel 'group_replication_recovery' initialized, starting replication in log 'FIRST' at position 0, relay log './yejr-relay-bin-group_replication_recovery.000001' position: 4
17:05:51.076174 29 [Note] [MY-012473] [InnoDB] DDL log insert : [DDL record: DELETE SPACE, id=2, thread_id=29, space_id=2, old_file_path=./mgr/t1.ibd]
17:05:51.076222 29 [Note] [MY-012478] [InnoDB] DDL log delete : 2
17:05:51.080727 29 [Note] [MY-012477] [InnoDB] DDL log insert : [DDL record: REMOVE CACHE, id=3, thread_id=29, table_id=1061, new_file_path=mgr/t1]
17:05:51.080753 29 [Note] [MY-012478] [InnoDB] DDL log delete : 3
17:05:51.082251 29 [Note] [MY-012472] [InnoDB] DDL log insert : [DDL record: FREE, id=4, thread_id=29, space_id=2, index_id=154, page_no=4]
17:05:51.082270 29 [Note] [MY-012478] [InnoDB] DDL log delete : 4
17:05:51.090227 29 [Note] [MY-012485] [InnoDB] DDL log post ddl : begin for thread id : 29
17:05:51.090248 29 [Note] [MY-012486] [InnoDB] DDL log post ddl : end for thread id : 29
17:05:51.100306 26 [Note] [MY-011585] [Repl] Plugin group_replication reported: 'Terminating existing group replication donor connection and purging the corresponding logs.'
17:05:51.104775 28 [Note] [MY-010587] [Repl] Slave SQL thread for channel 'group_replication_recovery' exiting, replication stopped in log 'mgr04.000002' at position 2765
17:05:51.106507 27 [Note] [MY-011026] [Repl] Slave I/O thread killed while reading event for channel 'group_replication_recovery'.
17:05:51.106536 27 [Note] [MY-010570] [Repl] Slave I/O thread exiting for channel 'group_replication_recovery', read up to log 'mgr04.000002', position 2765
-- 13. 分布式恢复结束，宣告本节点状态为online
17:05:51.139655 26 [System] [MY-010597] [Repl] 'CHANGE MASTER TO FOR CHANNEL 'group_replication_recovery' executed'. Previous state master_host='127.0.0.1', master_port= 3309, master_log_file='', master_log_pos= 4, master_bind=''. New state master_host='<NULL>', master_port= 0, master_log_file='', master_log_pos= 4, master_bind=''.
17:05:51.157750 [System] [MY-011490] [Repl] Plugin group_replication reported: 'This server was declared online within the replication group.'
```

根据上面的日志，可知加入新节点的过程（简化后）大致如下：
1. 初始化MGR相关设置。
2. 准备执行view change。
3. 新节点加入成功。
4. 确认donor节点后，进行分布式恢复（本地恢复 + 全局恢复）。
5. 宣告本节点状态为online。

## 2. 从日志理解（mysql shell调用）加入新节点过程
如果通过MySQL Shell新增一个MGR节点，操作过程简单很多，可以参考这篇文档：[4. 利用MySQL Shell安装部署MGR集群 | 深入浅出MGR](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-04.md)。这里通过阅读日志来理解利用MySQL Shell加入新节点的逻辑过程：
```
-- 1. 启动MGR服务
17:44:05.068256 [System] [MY-010597] [Repl] 'CHANGE MASTER TO FOR CHANNEL 'group_replication_recovery' executed'. Previous state master_host='', master_port= 3306, master_log_file='', master_log_pos= 4, master_bind=''. New state master_host='', master_port= 3306, master_log_file='', master_log_pos= 4, master_bind=''.
17:44:05.077153 [System] [MY-013587] [Repl] Plugin group_replication reported: 'Plugin 'group_replication' is starting.'
17:44:05.077175 [Note] [MY-011716] [Repl] Plugin group_replication reported: 'Current debug options are: 'GCS_DEBUG_NONE'.'
17:44:05.077581 [Note] [MY-011673] [Repl] Plugin group_replication reported: 'Group communication SSL configuration: group_replication_ssl_mode: "DISABLED"'
17:44:05.077982 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Debug messages will be sent to: asynchronous::/data/GreatSQL/mgr07/GCS_DEBUG_TRACE'
-- 2. 添加allowlist
17:44:05.078073 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Added automatically IP ranges 127.0.0.1/8,192.168.5.170/24,192.168.6.27/24,::1/128,fe80::215:5dff:fe06:4000/64 to the allowlist'
17:44:05.078182 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] SSL was not enabled'
-- 3. 初始化MGR相关选项
17:44:05.078213 [Note] [MY-011694] [Repl] Plugin group_replication reported: 'Initialized group communication with configuration: group_replication_group_name: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaabb1'; group_replication_local_address: '127.0.0.1:33121'; group_replication_group_seeds: '127.0.0.1:33111,127.0.0.1:33101,127.0.0.1:33091'; group_replication_bootstrap_group: 'false'; group_replication_poll_spin_loops: 0; group_replication_compression_threshold: 1000000; group_replication_ip_allowlist: 'AUTOMATIC'; group_replication_communication_debug_options: 'GCS_DEBUG_NONE'; group_replication_member_expel_timeout: '5'; group_replication_communication_max_message_size: 1048576; group_replication_message_cache_size: '1073741824u''
17:44:05.078244 [Note] [MY-011643] [Repl] Plugin group_replication reported: 'Member configuration: member_id: 3312; member_uuid: "5ab47c08-8d7a-11ec-b39d-00155d064000"; single-primary mode: "true"; group_replication_auto_increment_increment: 7; '
-- 4. 初始化广播线程
17:44:05.078263 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'Init certifier broadcast thread'
-- 5. 发现新节点之前曾经加入过
17:44:05.078389 [Note] [MY-011531] [Repl] Plugin group_replication reported: 'Detected previous RESET MASTER invocation or an issue exists in the group replication applier relay log. Purging existing applier logs.'
-- 6. 初始化group_replication_applier channel
17:44:05.102423 [System] [MY-010597] [Repl] 'CHANGE MASTER TO FOR CHANNEL 'group_replication_applier' executed'. Previous state master_host='<NULL>', master_port= 0, master_log_file='', master_log_pos= 4, master_bind=''. New state master_host='<NULL>', master_port= 0, master_log_file='', master_log_pos= 4, master_bind=''.
17:44:05.127744 [Note] [MY-011670] [Repl] Plugin group_replication reported: 'Group Replication applier module successfully initialized!'
17:44:05.127793 [Note] [MY-010581] [Repl] Slave SQL thread for channel 'group_replication_applier' initialized, starting replication in log 'FIRST' at position 0, relay log './yejr-relay-bin-group_replication_applier.000001' position: 4
-- 7. 确认MGR通信协议版本
17:44:05.163865 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] XCom protocol version: 9'
-- 8. 确认MGR通信端口
17:44:05.163917 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] XCom initialized and ready to accept incoming connections on port 33121'
-- 9. 准备创建新节点
17:44:05.664725 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 0 host 127.0.0.1'
17:44:05.664830 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 1 host 127.0.0.1'
17:44:05.665023 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 2 host 127.0.0.1'
17:44:05.665132 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 16239 Installed site start={ff389be 678813 3} boot_key={ff389be 678802 3} event_horizon=10 node 4294967295 chksum_node_list(&site->nodes) 4067201187'
17:44:05.665252 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 0 host 127.0.0.1'
17:44:05.665268 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 1 host 127.0.0.1'
17:44:05.665279 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 2 host 127.0.0.1'
17:44:05.665294 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 3 host 127.0.0.1'
17:44:05.665394 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 16239 Installed site start={ff389be 680207 1} boot_key={ff389be 680196 1} event_horizon=10 node 3 chksum_node_list(&site->nodes) 3840072444'
17:44:05.665470 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 0 host 127.0.0.1'
17:44:05.665484 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 1 host 127.0.0.1'
17:44:05.665495 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 2 host 127.0.0.1'
17:44:05.665508 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 16239 Installed site start={ff389be 687570 3} boot_key={ff389be 687559 3} event_horizon=10 node 4294967295 chksum_node_list(&site->nodes) 4067201187'
17:44:05.665581 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 0 host 127.0.0.1'
17:44:05.665595 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 1 host 127.0.0.1'
17:44:05.665606 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 2 host 127.0.0.1'
17:44:05.665618 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 3 host 127.0.0.1'
17:44:05.665631 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 16239 Installed site start={ff389be 688175 2} boot_key={ff389be 688164 2} event_horizon=10 node 3 chksum_node_list(&site->nodes) 3840072444'
-- 10. 准备执行view change
17:44:05.667140 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Rejecting this message. The member is not in a view yet.'
17:44:05.667219 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:44:05.667345 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:44:05.670284 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:44:05.767888 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::xcom_receive_global_view() is called'
17:44:06.770059 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_communication do_send_message CT_INTERNAL_STATE_EXCHANGE'
17:44:06.770281 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::xcom_receive_global_view():: state exchange started.'
17:44:06.770698 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:44:06.770734 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:44:06.770791 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:44:06.770837 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:44:06.770852 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:44:06.770886 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:44:06.770917 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:44:06.771507 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:44:06.771558 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
-- 11. 确定通信协议版本
17:44:06.771585 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] This server adjusted its communication protocol to 8.0.16 in order to join the group.'
17:44:06.771599 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Group is able to support up to communication protocol version 8.0.16'
-- 12. 准备更新view
17:44:06.771613 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message()::Install new view'
17:44:06.771632 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:44:06.771643 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:44:06.771654 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:44:06.771664 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:44:06.771677 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'on_view_changed is called'
-- 13. 确认新节点为secondary
17:44:06.772081 [System] [MY-011511] [Repl] Plugin group_replication reported: 'This server is working as secondary member with primary member address 127.0.0.1:3309.'
-- 14. 准备进行分布式恢复（这里选择用clone全备，还可以选择增备，或者不进行恢复）
17:44:07.773597 [Warning] [MY-013469] [Repl] Plugin group_replication reported: 'This member will start distributed recovery using clone. It is due to the number of missing transactions being higher than the configured threshold of 1.'
17:44:08.776083 [System] [MY-013471] [Repl] Plugin group_replication reported: 'Distributed recovery will transfer data using: Cloning from a remote group donor.'
-- 15. 确认primary节点
17:44:08.776961 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'handle_leader_election_if_needed is activated,suggested_primary:'
17:44:08.777225 [System] [MY-011503] [Repl] Plugin group_replication reported: 'Group membership changed to 127.0.0.1:3311, 127.0.0.1:3312, 127.0.0.1:3310, 127.0.0.1:3309 on view 16444111732158542:36.'
17:44:08.778024 [System] [MY-011566] [Repl] Plugin group_replication reported: 'Setting super_read_only=OFF.'
17:44:08.778362 [Note] [MY-010596] [Repl] Error reading relay log event for channel 'group_replication_applier': slave SQL thread was killed
17:44:08.778786 [Note] [MY-010587] [Repl] Slave SQL thread for channel 'group_replication_applier' exiting, replication stopped in log 'FIRST' at position 0
-- 16. 开始clone恢复数据
17:44:08.788318 [Note] [MY-013272] [Clone] Plugin Clone reported: 'Client: Task Connect.'
17:44:08.788886 [Note] [MY-013272] [Clone] Plugin Clone reported: 'Client: Master ACK Connect.'
17:44:08.788918 [Note] [MY-013457] [InnoDB] Clone Apply Begin Master Version Check
17:44:08.825495 [Note] [MY-013457] [InnoDB] Clone Apply Version End Master Task ID: 0 Passed, code: 0:
17:44:08.846718 [Note] [MY-013457] [InnoDB] Clone Apply Begin Master Task
17:44:08.846824 [Warning] [MY-013460] [InnoDB] Clone removing all user data for provisioning: Started
17:44:08.846830 [Note] [MY-011977] [InnoDB] Clone Drop all user data
17:44:08.878784 [Note] [MY-011977] [InnoDB] Clone: Fix Object count: 184 task: 0
17:44:08.881267 [Note] [MY-011977] [InnoDB] Clone Drop User schemas
17:44:08.881327 [Note] [MY-011977] [InnoDB] Clone: Fix Object count: 4 task: 0
17:44:08.881360 [Note] [MY-011977] [InnoDB] Clone Drop User tablespaces
17:44:08.881671 [Note] [MY-011977] [InnoDB] Clone: Fix Object count: 6 task: 0
17:44:08.893368 [Note] [MY-011977] [InnoDB] Clone Drop: finished successfully
17:44:08.893388 [Warning] [MY-013460] [InnoDB] Clone removing all user data for provisioning: Finished
17:44:08.894941 [Note] [MY-013272] [Clone] Plugin Clone reported: 'Client: Command COM_INIT.'
17:44:08.896913 [Note] [MY-013458] [InnoDB] Clone Apply State Change : Number of tasks = 1
17:44:08.896926 [Note] [MY-013458] [InnoDB] Clone Apply State FILE COPY:
17:44:08.896988 [Note] [MY-011978] [InnoDB] Clone estimated size: 6.36 GiB Available space: 643.30 GiB
17:44:09.439170 [Note] [MY-013272] [Clone] Plugin Clone reported: 'Client: Total Data: 367 MiB @ 678 MiB/sec, Network: 367 MiB @ 678 MiB/sec.'
17:44:09.440327 [Note] [MY-013458] [InnoDB] Clone Apply State Change : Number of tasks = 1
17:44:09.440344 [Note] [MY-013458] [InnoDB] Clone Apply State PAGE COPY:
17:44:09.440362 [Note] [MY-013272] [Clone] Plugin Clone reported: 'Client: Total Data: 367 MiB @ 675 MiB/sec, Network: 367 MiB @ 675 MiB/sec.'
17:44:09.448591 [Note] [MY-013458] [InnoDB] Clone Apply State Change : Number of tasks = 1
17:44:09.448605 [Note] [MY-013458] [InnoDB] Clone Apply State REDO COPY:
17:44:09.448685 [Note] [MY-013272] [Clone] Plugin Clone reported: 'Client: Total Data: 367 MiB @ 666 MiB/sec, Network: 367 MiB @ 666 MiB/sec.'
17:44:09.449744 [Note] [MY-013458] [InnoDB] Clone Apply State Change : Number of tasks = 1
17:44:09.449755 [Note] [MY-013458] [InnoDB] Clone Apply State FLUSH DATA:
17:44:09.454223 [Note] [MY-013458] [InnoDB] Clone Apply State FLUSH REDO:
17:44:09.559917 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile0.#clone size to 2048 MB. Progress : 10%
17:44:09.661473 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile0.#clone size to 2048 MB. Progress : 20%
17:44:09.777159 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile0.#clone size to 2048 MB. Progress : 30%
17:44:09.881932 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile0.#clone size to 2048 MB. Progress : 40%
17:44:09.985945 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile0.#clone size to 2048 MB. Progress : 50%
17:44:10.090829 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile0.#clone size to 2048 MB. Progress : 60%
17:44:10.196516 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile0.#clone size to 2048 MB. Progress : 70%
17:44:10.309041 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile0.#clone size to 2048 MB. Progress : 80%
17:44:10.419228 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile0.#clone size to 2048 MB. Progress : 90%
17:44:10.531019 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile0.#clone size to 2048 MB. Progress : 100%
17:44:10.641421 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile1.#clone size to 2048 MB. Progress : 10%
17:44:10.751576 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile1.#clone size to 2048 MB. Progress : 20%
17:44:10.864604 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile1.#clone size to 2048 MB. Progress : 30%
17:44:10.969377 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile1.#clone size to 2048 MB. Progress : 40%
17:44:11.069824 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile1.#clone size to 2048 MB. Progress : 50%
17:44:11.174559 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile1.#clone size to 2048 MB. Progress : 60%
17:44:11.278711 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile1.#clone size to 2048 MB. Progress : 70%
17:44:11.381693 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile1.#clone size to 2048 MB. Progress : 80%
17:44:11.493723 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile1.#clone size to 2048 MB. Progress : 90%
17:44:11.608019 [Note] [MY-012887] [InnoDB] Setting log file ./ib_logfile1.#clone size to 2048 MB. Progress : 100%
17:44:11.610686 [Note] [MY-013458] [InnoDB] Clone Apply State DONE
17:44:11.610715 [Note] [MY-013272] [Clone] Plugin Clone reported: 'Client: Command COM_EXECUTE.'
17:44:11.610813 [Note] [MY-013272] [Clone] Plugin Clone reported: 'Client: Master ACK COM_EXIT.'
17:44:11.610976 [Note] [MY-013272] [Clone] Plugin Clone reported: 'Client: Master ACK Disconnect : abort: false.'
17:44:11.611147 [Note] [MY-013272] [Clone] Plugin Clone reported: 'Client: Task COM_EXIT.'
17:44:11.611254 [Note] [MY-013272] [Clone] Plugin Clone reported: 'Client: Task Disconnect : abort: false.'
17:44:11.611324 [Note] [MY-013457] [InnoDB] Clone Apply End Master Task ID: 0 Passed, code: 0:
-- 17. clone恢复结束，关闭相关的服务线程
17:44:11.612106 [Note] [MY-010067] [Server] Giving 9 client threads a chance to die gracefully
17:44:11.612164 [Note] [MY-010117] [Server] Shutting down slave threads
17:44:11.612177 [Note] [MY-010054] [Server] Event Scheduler: Killing the scheduler thread, thread id 6
17:44:11.612184 [Note] [MY-010050] [Server] Event Scheduler: Waiting for the scheduler thread to reply
17:44:11.612317 [Note] [MY-010048] [Server] Event Scheduler: Stopped
17:44:13.612473 [Note] [MY-010118] [Server] Forcefully disconnecting 6 remaining clients
17:44:13.612563 [Warning] [MY-010909] [Server] /usr/local/GreatSQL-8.0.32-25/bin/mysqld: Forcing close of thread 19  user: 'root'.
17:44:13.612811 [Warning] [MY-010909] [Server] /usr/local/GreatSQL-8.0.32-25/bin/mysqld: Forcing close of thread 27  user: 'GreatSQL'.
17:44:13.613020 [Warning] [MY-010909] [Server] /usr/local/GreatSQL-8.0.32-25/bin/mysqld: Forcing close of thread 28  user: 'GreatSQL'.
17:44:13.613112 [Note] [MY-011650] [Repl] Plugin group_replication reported: 'Plugin 'group_replication' is stopping.'
-- 18. 准备关闭mysql实例，关闭MGR服务，需要执行view change
17:44:13.613226 [Note] [MY-011647] [Repl] Plugin group_replication reported: 'Going to wait for view modification'
17:44:13.614837 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 0 host 127.0.0.1'
17:44:13.614976 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 1 host 127.0.0.1'
17:44:13.615010 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 2 host 127.0.0.1'
17:44:13.615040 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 16239 Installed site start={ff389be 688238 3} boot_key={ff389be 688227 3} event_horizon=10 node 4294967295 chksum_node_list(&site->nodes) 4067201187'
17:44:16.645432 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Installing leave view.'
17:44:16.645466 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::install_view():: No exchanged data'
17:44:16.645472 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'on_view_changed is called'
17:44:16.645512 [System] [MY-011504] [Repl] Plugin group_replication reported: 'Group membership changed: This member has left the group.'
17:44:16.650868 [Note] [MY-011444] [Repl] Plugin group_replication reported: 'The group replication applier thread was killed.'
17:44:16.651058 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'Destroy certifier broadcast thread'
17:44:16.651183 [System] [MY-011651] [Repl] Plugin group_replication reported: 'Plugin 'group_replication' has been stopped.'
17:44:16.651201 [Note] [MY-010043] [Server] Event Scheduler: Purging the queue. 0 events
17:44:16.655273 [Note] [MY-012330] [InnoDB] FTS optimize thread exiting.
17:44:16.956235 [Note] [MY-010120] [Server] Binlog end
17:44:16.964448 [Note] [MY-010733] [Server] Shutting down plugin 'group_replication'
17:44:16.964523 [Note] [MY-011665] [Repl] Plugin group_replication reported: 'All Group Replication server observers have been successfully unregistered'
17:44:16.964556 [Note] [MY-010733] [Server] Shutting down plugin 'clone'
17:44:16.964571 [Note] [MY-010733] [Server] Shutting down plugin 'mysqlx'
17:44:16.965905 [Note] [MY-010733] [Server] Shutting down plugin 'mysqlx_cache_cleaner'
17:44:16.965941 [Note] [MY-010733] [Server] Shutting down plugin 'ngram'
17:44:16.965947 [Note] [MY-010733] [Server] Shutting down plugin 'BLACKHOLE'
17:44:16.965953 [Note] [MY-010733] [Server] Shutting down plugin 'ARCHIVE'
17:44:16.965958 [Note] [MY-010733] [Server] Shutting down plugin 'TempTable'
17:44:16.965963 [Note] [MY-010733] [Server] Shutting down plugin 'MRG_MYISAM'
17:44:16.965968 [Note] [MY-010733] [Server] Shutting down plugin 'MyISAM'
17:44:16.965977 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_CHANGED_PAGES'
17:44:16.965982 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_TABLESPACES_SCRUBBING'
17:44:16.965987 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_TABLESPACES_ENCRYPTION'
17:44:16.965992 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_SESSION_TEMP_TABLESPACES'
17:44:16.965997 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_CACHED_INDEXES'
17:44:16.966001 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_VIRTUAL'
17:44:16.966006 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_COLUMNS'
17:44:16.966010 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_TABLESPACES'
17:44:16.966016 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_INDEXES'
17:44:16.966020 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_TABLESTATS'
17:44:16.966025 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_TABLES'
17:44:16.966029 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_FT_INDEX_TABLE'
17:44:16.966034 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_FT_INDEX_CACHE'
17:44:16.966038 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_FT_CONFIG'
17:44:16.966042 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_FT_BEING_DELETED'
17:44:16.966054 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_FT_DELETED'
17:44:16.966059 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_FT_DEFAULT_STOPWORD'
17:44:16.966063 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_METRICS'
17:44:16.966067 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_TEMP_TABLE_INFO'
17:44:16.966072 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_BUFFER_POOL_STATS'
17:44:16.966076 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_BUFFER_PAGE_LRU'
17:44:16.966081 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_BUFFER_PAGE'
17:44:16.966085 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_CMP_PER_INDEX_RESET'
17:44:16.966089 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_CMP_PER_INDEX'
17:44:16.966094 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_CMPMEM_RESET'
17:44:16.966099 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_CMPMEM'
17:44:16.966107 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_CMP_RESET'
17:44:16.966112 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_CMP'
17:44:16.966116 [Note] [MY-010733] [Server] Shutting down plugin 'INNODB_TRX'
17:44:16.966121 [Note] [MY-010733] [Server] Shutting down plugin 'InnoDB'
17:44:16.966152 [Note] [MY-013072] [InnoDB] Starting shutdown...
17:44:16.966397 [Note] [MY-011944] [InnoDB] Dumping buffer pool(s) to /data/GreatSQL/mgr07/ib_buffer_pool
17:44:16.966967 [Note] [MY-011944] [InnoDB] Buffer pool(s) dump completed at 220214 17:44:16
17:44:16.975517 [Note] [MY-013084] [InnoDB] Log background threads are being closed...
17:44:17.501062 [Note] [MY-012980] [InnoDB] Shutdown completed; log sequence number 18232670
17:44:17.501148 [Note] [MY-012255] [InnoDB] Removed temporary tablespace data file: "ibtmp1"
17:44:17.501165 [Note] [MY-010733] [Server] Shutting down plugin 'MEMORY'
17:44:17.501170 [Note] [MY-010733] [Server] Shutting down plugin 'CSV'
17:44:17.501174 [Note] [MY-010733] [Server] Shutting down plugin 'PERFORMANCE_SCHEMA'
17:44:17.501191 [Note] [MY-010733] [Server] Shutting down plugin 'daemon_keyring_proxy_plugin'
17:44:17.501199 [Note] [MY-010733] [Server] Shutting down plugin 'sha2_cache_cleaner'
17:44:17.501202 [Note] [MY-010733] [Server] Shutting down plugin 'caching_sha2_password'
17:44:17.501206 [Note] [MY-010733] [Server] Shutting down plugin 'sha256_password'
17:44:17.501208 [Note] [MY-010733] [Server] Shutting down plugin 'mysql_native_password'
17:44:17.502296 [Note] [MY-010733] [Server] Shutting down plugin 'binlog'
17:44:17.509905 [System] [MY-010910] [Server] /usr/local/GreatSQL-8.0.32-25/bin/mysqld: Shutdown complete (mysqld 8.0.32-25)  GreatSQL (GPL), Release 25, Revision 79f57097e3f.
-- 19. 启动mysql实例
17:44:18.598602 [Warning] [MY-010140] [Server] Could not increase number of max_open_files to more than 10000 (request: 65535)
17:44:18.786863 [Note] [MY-010098] [Server] --secure-file-priv is set to NULL. Operations related to importing and exporting data are disabled
17:44:18.786898 [Note] [MY-010949] [Server] Basedir set to /usr/local/GreatSQL-8.0.32-25/.
17:44:18.786904 [System] [MY-010116] [Server] /usr/local/GreatSQL-8.0.32-25/bin/mysqld (mysqld 8.0.32-25) starting as process 16415
17:44:18.798984 [Warning] [MY-012364] [InnoDB] innodb_open_files should not be greater than the open_files_limit.
17:44:18.799025 [Note] [MY-012366] [InnoDB] Using Linux native AIO
17:44:18.799319 [Note] [MY-010747] [Server] Plugin 'FEDERATED' is disabled.
17:44:18.799364 [Warning] [MY-000081] [Server] option 'mysqlx-port': unsigned value 0 adjusted to 1.
17:44:18.800468 [System] [MY-013576] [InnoDB] InnoDB initialization has started.
17:44:18.800547 [Note] [MY-013546] [InnoDB] Atomic write enabled
17:44:18.800580 [Note] [MY-012932] [InnoDB] PUNCH HOLE support available
17:44:18.800606 [Note] [MY-012944] [InnoDB] Uses event mutexes
17:44:18.800630 [Note] [MY-012945] [InnoDB] GCC builtin __atomic_thread_fence() is used for memory barrier
17:44:18.800656 [Note] [MY-012948] [InnoDB] Compressed tables use zlib 1.2.11
17:44:18.802271 [Note] [MY-013251] [InnoDB] Number of pools: 1
17:44:18.802374 [Note] [MY-012951] [InnoDB] Using CPU crc32 instructions
17:44:18.802620 [Note] [MY-012203] [InnoDB] Directories to scan './'
-- 20. 重启后执行数据恢复
17:44:18.802684 [Note] [MY-011976] [InnoDB] Clone Old File Roll Forward: Skipped cloned file ./ib_logfile0 state: 101
17:44:18.802725 [Note] [MY-011976] [InnoDB] Clone Old File Roll Forward: Skipped cloned file ./ib_logfile1 state: 101
17:44:18.802776 [Note] [MY-011976] [InnoDB] Clone Old File Roll Forward: Saved data file ./ib_logfile2 state: 1
17:44:18.802824 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Save data file /data/GreatSQL/mgr07/ib_buffer_pool state: 101
17:44:18.802865 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Rename clone to data file /data/GreatSQL/mgr07/ib_buffer_pool state: 101
17:44:18.802917 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Save data file ibdata1 state: 101
17:44:18.802982 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Rename clone to data file ibdata1 state: 101
17:44:18.803041 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Save data file sys/sys_config.ibd state: 101
17:44:18.803084 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Rename clone to data file sys/sys_config.ibd state: 101
17:44:18.803136 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Save data file mysql.ibd state: 101
17:44:18.803185 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Rename clone to data file mysql.ibd state: 101
17:44:18.803240 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Save data file ./undo_002 state: 101
17:44:18.803291 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Rename clone to data file ./undo_002 state: 101
17:44:18.803347 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Save data file ./undo_001 state: 101
17:44:18.803404 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Rename clone to data file ./undo_001 state: 101
17:44:18.803468 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Save data file ./ib_logfile0 state: 101
17:44:18.803523 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Rename clone to data file ./ib_logfile0 state: 101
17:44:18.803583 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Save data file ./ib_logfile1 state: 101
17:44:18.803642 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Rename clone to data file ./ib_logfile1 state: 101
17:44:18.803726 [Note] [MY-012204] [InnoDB] Scanning './'
17:44:18.810459 [Note] [MY-012208] [InnoDB] Completed space ID check of 21 files.
17:44:18.811222 [Note] [MY-012955] [InnoDB] Initializing buffer pool, total size = 2.000000G, instances = 8, chunk size =128.000000M
17:44:18.849695 [Note] [MY-012957] [InnoDB] Completed initialization of buffer pool
17:44:18.855473 [Note] [MY-011952] [InnoDB] If the mysqld execution user is authorized, page cleaner and LRU manager thread priority can be changed. See the man page of setpriority().
17:44:18.857311 [Note] [MY-013532] [InnoDB] Using './#ib_16384_0.dblwr' for doublewrite
17:44:18.858346 [Note] [MY-013532] [InnoDB] Using './#ib_16384_1.dblwr' for doublewrite
17:44:18.885057 [Note] [MY-013566] [InnoDB] Double write buffer files: 2
17:44:18.885155 [Note] [MY-013565] [InnoDB] Double write buffer pages per instance: 4
17:44:18.885234 [Note] [MY-013532] [InnoDB] Using './#ib_16384_0.dblwr' for doublewrite
17:44:18.885312 [Note] [MY-013532] [InnoDB] Using './#ib_16384_1.dblwr' for doublewrite
17:44:18.886060 [Note] [MY-012556] [InnoDB] Opening cloned database
17:44:18.886155 [Note] [MY-012560] [InnoDB] The log sequence number 17818012 in the system tablespace does not match the log sequence number 536974192 in the ib_logfiles!
17:44:18.886229 [Note] [MY-012551] [InnoDB] Database was not shutdown normally!
17:44:18.886308 [Note] [MY-012552] [InnoDB] Starting crash recovery.
17:44:18.886872 [Note] [MY-013086] [InnoDB] Starting to parse redo log at lsn = 536973859, whereas checkpoint_lsn = 536974192 and start_lsn = 536973824
17:44:18.886977 [Note] [MY-012550] [InnoDB] Doing recovery: scanned up to log sequence number 536978901
17:44:18.893421 [Note] [MY-013083] [InnoDB] Log background threads are being started...
17:44:18.893779 [Note] [MY-012532] [InnoDB] Applying a batch of 11 redo log records ...
17:44:18.896068 [Note] [MY-012533] [InnoDB] 100%
17:44:19.409674 [Note] [MY-012535] [InnoDB] Apply batch completed!
17:44:19.411509 [Note] [MY-013041] [InnoDB] Resizing redo log from 2*2147483648 to 3*2147483648 bytes, LSN=536978901
17:44:19.411834 [Note] [MY-013084] [InnoDB] Log background threads are being closed...
17:44:19.417583 [Note] [MY-011976] [InnoDB] Clone Old File Roll Forward: Skipped cloned file ./ib_logfile0 state: 11
17:44:19.417696 [Note] [MY-011976] [InnoDB] Clone Old File Roll Forward: Skipped cloned file ./ib_logfile1 state: 11
17:44:19.417832 [Note] [MY-011976] [InnoDB] Clone Old File Roll Forward: Remove saved file ./ib_logfile2 state: 10
17:44:19.418014 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Remove saved data file /data/GreatSQL/mgr07/ib_buffer_pool state: 11
17:44:19.418145 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Remove saved data file ibdata1 state: 11
17:44:19.418270 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Remove saved data file sys/sys_config.ibd state: 11
17:44:19.418427 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Remove saved data file mysql.ibd state: 11
17:44:19.418544 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Remove saved data file ./undo_002 state: 11
17:44:19.418663 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Remove saved data file ./undo_001 state: 11
17:44:19.419953 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Remove saved data file ./ib_logfile0 state: 11
17:44:19.420112 [Note] [MY-011976] [InnoDB] Clone File Roll Forward: Remove saved data file ./ib_logfile1 state: 11
17:44:19.420252 [Note] [MY-012968] [InnoDB] Starting to delete and rewrite log files.
17:44:19.420489 [Note] [MY-013575] [InnoDB] Creating log file ./ib_logfile101
17:44:19.422010 [Note] [MY-013575] [InnoDB] Creating log file ./ib_logfile1
17:44:19.422990 [Note] [MY-013575] [InnoDB] Creating log file ./ib_logfile2
17:44:19.462164 [Note] [MY-012892] [InnoDB] Renaming log file ./ib_logfile101 to ./ib_logfile0
17:44:19.462360 [Note] [MY-012893] [InnoDB] New log files created, LSN=536978956
17:44:19.462492 [Note] [MY-013083] [InnoDB] Log background threads are being started...
17:44:19.462856 [Note] [MY-013252] [InnoDB] Using undo tablespace './undo_001'.
17:44:19.463380 [Note] [MY-013252] [InnoDB] Using undo tablespace './undo_002'.
17:44:19.463906 [Note] [MY-012910] [InnoDB] Opened 2 existing undo tablespaces.
17:44:19.464062 [Note] [MY-011980] [InnoDB] GTID recovery trx_no: 5962
17:44:19.576642 [Note] [MY-012923] [InnoDB] Creating shared tablespace for temporary tables
17:44:19.576842 [Note] [MY-012265] [InnoDB] Setting file './ibtmp1' size to 12 MB. Physically writing the file full; Please wait ...
17:44:19.607274 [Note] [MY-012266] [InnoDB] File './ibtmp1' size is now 12 MB.
17:44:19.607493 [Note] [MY-013627] [InnoDB] Scanning temp tablespace dir:'./#innodb_temp/'
17:44:19.620971 [Note] [MY-013018] [InnoDB] Created 128 and tracked 128 new rollback segment(s) in the temporary tablespace. 128 are now active.
17:44:19.621579 [Note] [MY-012976] [InnoDB] Percona XtraDB (http://www.percona.com) 8.0.32-25 started; log sequence number 536978956
17:44:19.622059 [System] [MY-013577] [InnoDB] InnoDB initialization has ended.
17:44:19.628832 [Note] [MY-011089] [Server] Data dictionary restarting version '80023'.
17:44:19.694094 [Note] [MY-012357] [InnoDB] Reading DD tablespace files
17:44:19.702047 [Note] [MY-012356] [InnoDB] Scanned 23 tablespaces. Validated 23.
17:44:19.702239 [Note] [MY-011977] [InnoDB] Clone Fixup: check and create schema directory
17:44:19.702492 [Note] [MY-011977] [InnoDB] Clone: Fix Object count: 7 task: 0
17:44:19.702695 [Note] [MY-011977] [InnoDB] Clone Fixup: create empty MyIsam and CSV tables
17:44:19.756611 [Note] [MY-011977] [InnoDB] Clone: Fix Object count: 100 task: 0
17:44:19.756867 [Note] [MY-011977] [InnoDB] Clone: Fix Object count: 1 task: 2
17:44:19.757216 [Note] [MY-011977] [InnoDB] Clone: Fix Object count: 100 task: 1
17:44:19.762557 [Note] [MY-011977] [InnoDB] Clone Fixup: replication configuration tables
17:44:19.762786 [Note] [MY-011977] [InnoDB] Clone Fixup: finished successfully
17:44:19.777416 [Note] [MY-010006] [Server] Using data dictionary with version '80023'.
17:44:19.790724 [Note] [MY-011332] [Server] Plugin mysqlx reported: 'IPv6 is available'
17:44:19.797762 [ERROR] [MY-011300] [Server] Plugin mysqlx reported: 'Setup of bind-address: '*' port: 1 failed, `bind()` failed with error: Permission denied (13). Do you already have another mysqld server running with Mysqlx ?'
17:44:19.797986 [ERROR] [MY-013597] [Server] Plugin mysqlx reported: 'Value '*' set to `Mysqlx_bind_address`, X Plugin can't bind to it. Skipping this value.'
17:44:19.798162 [Note] [MY-011323] [Server] Plugin mysqlx reported: 'X Plugin ready for connections. socket: '/tmp/mysqlx.sock''
17:44:19.798350 [Note] [MY-011322] [Server] Plugin mysqlx reported: 'Please see the MySQL documentation for 'mysqlx_port,mysqlx_bind_address' system variables to fix the error'
17:44:19.798536 [System] [MY-011323] [Server] X Plugin ready for connections. Socket: /tmp/mysqlx.sock
17:44:19.802975 [System] [MY-013587] [Repl] Plugin group_replication reported: 'Plugin 'group_replication' is starting.'
17:44:19.803206 [Note] [MY-011716] [Repl] Plugin group_replication reported: 'Current debug options are: 'GCS_DEBUG_NONE'.'
17:44:19.813865 [Note] [MY-010902] [Server] Thread priority attribute setting in Resource Group SQL shall be ignored due to unsupported platform or insufficient privilege.
17:44:19.828677 [Note] [MY-012487] [InnoDB] DDL log recovery : begin
17:44:19.829254 [Note] [MY-012488] [InnoDB] DDL log recovery : end
17:44:19.829725 [Note] [MY-011946] [InnoDB] Loading buffer pool(s) from /data/GreatSQL/mgr07/ib_buffer_pool
17:44:19.833100 [Note] [MY-012922] [InnoDB] Waiting for purge to start
17:44:19.887951 [Note] [MY-011946] [InnoDB] Buffer pool(s) load completed at 220214 17:44:19
17:44:19.890042 [Note] [MY-010182] [Server] Found ca.pem, server-cert.pem and server-key.pem in data directory. Trying to enable SSL support using them.
17:44:19.890306 [Note] [MY-010304] [Server] Skipping generation of SSL certificates as certificate files are present in data directory.
17:44:19.891114 [Warning] [MY-010068] [Server] CA certificate ca.pem is self signed.
17:44:19.891369 [System] [MY-013602] [Server] Channel mysql_main configured to support TLS. Encrypted connections are now supported for this channel.
17:44:19.891611 [Note] [MY-010308] [Server] Skipping generation of RSA key pair through --sha256_password_auto_generate_rsa_keys as key files are present in data directory.
17:44:19.891817 [Note] [MY-010308] [Server] Skipping generation of RSA key pair through --caching_sha2_password_auto_generate_rsa_keys as key files are present in data directory.
17:44:19.892091 [Note] [MY-010252] [Server] Server hostname (bind-address): '*'; port: 3312
17:44:19.892307 [Note] [MY-010253] [Server] IPv6 is available.
17:44:19.892512 [Note] [MY-010264] [Server]   - '::' resolves to '::';
17:44:19.892718 [Note] [MY-010251] [Server] Server socket created on IP: '::'.
17:44:19.909924 [Warning] [MY-010604] [Repl] Neither --relay-log nor --relay-log-index were used; so replication may break when this MySQL server acts as a slave and has his hostname changed!! Please use '--relay-log=yejr-relay-bin' to avoid this problem.
17:44:19.956694 [Note] [MY-011025] [Repl] Failed to start slave threads for channel ''.
17:44:19.959308 [Note] [MY-010051] [Server] Event Scheduler: scheduler thread started with id 6
17:44:19.960078 [Note] [MY-011240] [Server] Plugin mysqlx reported: 'Using SSL configuration from MySQL Server'
17:44:19.960445 [Note] [MY-011243] [Server] Plugin mysqlx reported: 'Using OpenSSL for TLS connections'
17:44:19.960638 [System] [MY-010931] [Server] /usr/local/GreatSQL-8.0.32-25/bin/mysqld: ready for connections. Version: '8.0.32-25'  socket: '/data/GreatSQL/mgr07/mysql.sock'  port: 3312  GreatSQL (GPL), Release 25, Revision 79f57097e3f.
17:44:19.961001 [Note] [MY-011673] [Repl] Plugin group_replication reported: 'Group communication SSL configuration: group_replication_ssl_mode: "DISABLED"'
17:44:19.961750 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Debug messages will be sent to: asynchronous::/data/GreatSQL/mgr07/GCS_DEBUG_TRACE'
-- 21. 新节点准备加入MGR
17:44:19.961851 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Added automatically IP ranges 127.0.0.1/8,192.168.5.170/24,192.168.6.27/24,::1/128,fe80::215:5dff:fe06:4000/64 to the allowlist'
17:44:19.961978 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] SSL was not enabled'
17:44:19.962000 [Note] [MY-011694] [Repl] Plugin group_replication reported: 'Initialized group communication with configuration: group_replication_group_name: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaabb1'; group_replication_local_address: '127.0.0.1:33121'; group_replication_group_seeds: '127.0.0.1:33111,127.0.0.1:33101,127.0.0.1:33091'; group_replication_bootstrap_group: 'false'; group_replication_poll_spin_loops: 0; group_replication_compression_threshold: 1000000; group_replication_ip_allowlist: 'AUTOMATIC'; group_replication_communication_debug_options: 'GCS_DEBUG_NONE'; group_replication_member_expel_timeout: '5'; group_replication_communication_max_message_size: 1048576; group_replication_message_cache_size: '1073741824u''
17:44:19.962043 [Note] [MY-011643] [Repl] Plugin group_replication reported: 'Member configuration: member_id: 3312; member_uuid: "5ab47c08-8d7a-11ec-b39d-00155d064000"; single-primary mode: "true"; group_replication_auto_increment_increment: 7; '
17:44:19.962066 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'Init certifier broadcast thread'
17:44:19.968634 [System] [MY-010597] [Repl] 'CHANGE MASTER TO FOR CHANNEL 'group_replication_applier' executed'. Previous state master_host='<NULL>', master_port= 0, master_log_file='', master_log_pos= 4, master_bind=''. New state master_host='<NULL>', master_port= 0, master_log_file='', master_log_pos= 4, master_bind=''.
17:44:19.994719 [Note] [MY-011670] [Repl] Plugin group_replication reported: 'Group Replication applier module successfully initialized!'
17:44:19.994761 [Note] [MY-010581] [Repl] Slave SQL thread for channel 'group_replication_applier' initialized, starting replication in log 'FIRST' at position 0, relay log './yejr-relay-bin-group_replication_applier.000001' position: 4
17:44:20.031917 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] XCom protocol version: 9'
17:44:20.031965 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] XCom initialized and ready to accept incoming connections on port 33121'
17:44:20.518585 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 0 host 127.0.0.1'
17:44:20.518719 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 1 host 127.0.0.1'
17:44:20.518772 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 2 host 127.0.0.1'
17:44:20.518828 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 16415 Installed site start={ff389be 687570 3} boot_key={ff389be 687559 3} event_horizon=10 node 4294967295 chksum_node_list(&site->nodes) 4067201187'
17:44:20.519010 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 0 host 127.0.0.1'
17:44:20.519040 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 1 host 127.0.0.1'
17:44:20.519052 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 2 host 127.0.0.1'
17:44:20.519063 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Creating new server node 3 host 127.0.0.1'
17:44:20.519163 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 16415 Installed site start={ff389be 688175 2} boot_key={ff389be 688164 2} event_horizon=10 node 3 chksum_node_list(&site->nodes) 3840072444'
17:44:20.519235 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 0 host 127.0.0.1'
17:44:20.519248 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 1 host 127.0.0.1'
17:44:20.519258 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 2 host 127.0.0.1'
17:44:20.519270 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 16415 Installed site start={ff389be 688238 3} boot_key={ff389be 688227 3} event_horizon=10 node 4294967295 chksum_node_list(&site->nodes) 4067201187'
17:44:20.519411 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 0 host 127.0.0.1'
17:44:20.519433 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 1 host 127.0.0.1'
17:44:20.519444 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 2 host 127.0.0.1'
17:44:20.519454 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Re-using server node 3 host 127.0.0.1'
17:44:20.519473 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] pid 16415 Installed site start={ff389be 688289 2} boot_key={ff389be 688278 2} event_horizon=10 node 3 chksum_node_list(&site->nodes) 3840072444'
17:44:20.520746 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Rejecting this message. The member is not in a view yet.'
17:44:20.520830 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Rejecting this message. The member is not in a view yet.'
17:44:20.520857 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::xcom_receive_global_view() is called'
17:44:21.523030 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_communication do_send_message CT_INTERNAL_STATE_EXCHANGE'
17:44:21.523190 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::xcom_receive_global_view():: state exchange started.'
17:44:21.523228 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:44:21.523240 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:44:21.523257 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] xcom_receive_local_view is called'
17:44:21.523282 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:44:21.523297 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:44:21.523315 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:44:21.523325 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:44:21.523337 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:44:21.523347 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:44:21.524564 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Do receive CT_INTERNAL_STATE_EXCHANGE message from xcom'
17:44:21.524613 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message():: Received a control message'
17:44:21.524644 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] This server adjusted its communication protocol to 8.0.16 in order to join the group.'
17:44:21.524662 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Group is able to support up to communication protocol version 8.0.16'
17:44:21.524681 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] ::process_control_message()::Install new view'
17:44:21.524705 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:44:21.524721 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:44:21.524748 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:44:21.524762 [Note] [MY-011735] [Repl] Plugin group_replication reported: '[GCS] Processing exchanged data while installing the new view'
17:44:21.524778 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'on_view_changed is called'
17:44:21.525097 [System] [MY-011511] [Repl] Plugin group_replication reported: 'This server is working as secondary member with primary member address 127.0.0.1:3309.'
-- 22. 执行增量恢复（自从上次全量clone恢复以来可能还有新数据产生）
17:44:22.526376 [System] [MY-013471] [Repl] Plugin group_replication reported: 'Distributed recovery will transfer data using: Incremental recovery from a group donor'
17:44:22.526749 [Note] [MY-011576] [Repl] Plugin group_replication reported: 'Establishing group recovery connection with a possible donor. Attempt 1/10'
17:44:22.526770 [Note] [MY-011071] [Repl] Plugin group_replication reported: 'handle_leader_election_if_needed is activated,suggested_primary:'
17:44:22.526824 [System] [MY-011503] [Repl] Plugin group_replication reported: 'Group membership changed to 127.0.0.1:3311, 127.0.0.1:3312, 127.0.0.1:3310, 127.0.0.1:3309 on view 16444111732158542:38.'
17:44:22.540641 [System] [MY-010597] [Repl] 'CHANGE MASTER TO FOR CHANNEL 'group_replication_recovery' executed'. Previous state master_host='<NULL>', master_port= 0, master_log_file='', master_log_pos= 4, master_bind=''. New state master_host='127.0.0.1', master_port= 3310, master_log_file='', master_log_pos= 4, master_bind=''.
-- 23. 选择增备的donor节点
17:44:22.557253 [Note] [MY-011580] [Repl] Plugin group_replication reported: 'Establishing connection to a group replication recovery donor 6d2d72aa-89a7-11ec-a145-00155d064000 at 127.0.0.1 port: 3310.'
17:44:22.557545 [Warning] [MY-010897] [Repl] Storing MySQL user name or password information in the master info repository is not secure and is therefore not recommended. Please consider using the USER and PASSWORD connection options for START SLAVE; see the 'START SLAVE Syntax' in the MySQL Manual for more information.
17:44:22.559750 [System] [MY-010562] [Repl] Slave I/O thread for channel 'group_replication_recovery': connected to master 'mysql_innodb_cluster_3310@127.0.0.1:3310',replication started in log 'FIRST' at position 4
17:44:22.571016 [Note] [MY-010581] [Repl] Slave SQL thread for channel 'group_replication_recovery' initialized, starting replication in log 'FIRST' at position 0, relay log './yejr-relay-bin-group_replication_recovery.000001' position: 4
17:44:22.729209 [Note] [MY-011585] [Repl] Plugin group_replication reported: 'Terminating existing group replication donor connection and purging the corresponding logs.'
17:44:22.733380 [Note] [MY-010587] [Repl] Slave SQL thread for channel 'group_replication_recovery' exiting, replication stopped in log 'mgr05.000002' at position 769728576
17:44:22.734618 [Note] [MY-011026] [Repl] Slave I/O thread killed while reading event for channel 'group_replication_recovery'.
17:44:22.734634 [Note] [MY-010570] [Repl] Slave I/O thread exiting for channel 'group_replication_recovery', read up to log 'mgr05.000002', position 769728576
17:44:22.766828 [System] [MY-010597] [Repl] 'CHANGE MASTER TO FOR CHANNEL 'group_replication_recovery' executed'. Previous state master_host='127.0.0.1', master_port= 3310, master_log_file='', master_log_pos= 4, master_bind=''. New state master_host='<NULL>', master_port= 0, master_log_file='', master_log_pos= 4, master_bind=''.
-- 24. 恢复完成，新节点成功加入
17:44:22.781981 [System] [MY-011490] [Repl] Plugin group_replication reported: 'This server was declared online within the replication group.'
17:44:22.954124 [System] [MY-010597] [Repl] 'CHANGE MASTER TO FOR CHANNEL 'group_replication_recovery' executed'. Previous state master_host='<NULL>', master_port= 0, master_log_file='', master_log_pos= 4, master_bind=''. New state master_host='<NULL>', master_port= 0, master_log_file='', master_log_pos= 4, master_bind=''.
```

日志比较多，简化后会发现和手动加入的过程基本上是一样的。

## 3. 小结
本文主要介绍MGR集群中新节点加入的过程是怎样的。

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
