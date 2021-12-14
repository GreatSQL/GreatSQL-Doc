# GreatSQL FAQ

> The FAQ about GreatSQL and MGR, continuously updated.
> 
> Last Update: 2021.12.14。

## 0. About GreatSQL
GreatSQL is a MySQL branch maintained by GreatDB, which is open source and free. GreatSQL is based on Percona Server, which further enhances the performance and reliability of MGR (MySQL Group Replication). In addition, GreatSQL incorporates Patch contributed by Huawei's Kunpeng computing team, implements InnoDB parallel query features, and optimizes InnoDB transaction locks.

GreatSQL can be used as an alternative to MySQL or Percona Server for online production environments.

GreatSQL is completely free and compatible with MySQL or Percona Server.

## 1. What are the features of GreatSQL

GreatSQL has several advantages over MySQL community server:
- InnoDB better performance
  - Support InnoDB parallel query, TPC-H test on average to improve the performance of aggregation analysis SQL 15 times, the highest increase of more than 40 times.
  - Optimize InnoDB transaction locks to improve tps performance by about 10%.
- MGR is more reliable, stable and has better performance.
  - Geo-label feature is introduced into MGR, which is mainly used to solve the problem of data synchronization in multiple computer rooms.
  - The flow control algorithm is optimized in MGR, and the operation is more stable.
  - Solve the problem of MGR cluster blocking when the disk space is full.
  - Solve the problem that MGR multi-master mode or failover may cause data loss.
  - Fix an issue that causes performance jitter when nodes abnormally exit the MGR cluster.
  - MGR node abnormal state judgment is more perfect.
  - The MGR transaction authentication queue cleaning algorithm is redesigned, and the problem of performance jitter every 60 seconds no longer exists.
  - Fixed an issue with long waiting times during recovery.
  - Fixed the problem that transmitting big data may lead to an endless loop of logical judgment.
  - Fix an issue with view updates caused by different types of abnormal exit of majority nodes from the cluster.
Whether it's a more reliable MGR or a better performing InnoDB, it's worth upgrading your current MySQL or Percona Server to GreatSQL.

Read the following articles about the advantages of GreatSQL:
- [GreatSQL Update Notes 8.0.25](https://github.com/GreatSQL/GreatSQL-Doc/blob/main/relnotes/changes-greatsql-8-0-25-20210826.md)
- [GreatSQL feature, InnoDB parallel parallel query optimization benchmark](https://mp.weixin.qq.com/s/_LeEtwJlfyvIlxzLoyNVdA)
- [GreatSQL is officially open source](https://mp.weixin.qq.com/s/cI_wPKQJuXItVWpOx_yNTg)

## 2. Where can I download GreatSQL

### Binary package, RPM package
Binary package download address: https://gitee.com/GreatSQL/GreatSQL/releases .

At present, it provides CentOS 7 and CentOS 8 operating systems, as well as binary packages and RPM packages under two different architectures of X86 and ARM.

The installation package with **minimal** keyword is after stripping the binary file, so the file size is small and there is no essential difference in function. It only does not support gdb debug function and can be used with confidence.

### Source code
You can download GreatSQL source code directly with git clone, for example:
```
# 可从gitee下载
$ git clone https://gitee.com/GreatSQL/GreatSQL.git

# 或从github下载
$ git clone https://github.com/GreatSQL/GreatSQL.git
```

### Ansible installation package

GreatSQL provides Ansible installation package, which can be downloaded from gitee or github:
- https://gitee.com/GreatSQL/GreatSQL-Ansible/releases
- https://github.com/GreatSQL/GreatSQL-Ansible/releases

### Docker image
GreatSQL provides Docker images that can be pulled directly from the docker hub:
```
# pull the latest version
$ docker pull docker.io/greatsql/greatsql

# specified tag
$ docker pull docker.io/greatsql/greatsql:8.0.25

# pull ARM version
$ docker pull docker.io/greatsql/greatsql:8.0.25-aarch64
```


## 3. Who to call when you encounter problems with GreatSQL

If you encounter problems during the use of GreatSQL, you can sort out the details of the problem and contact the GreatSQL community for help.

Scan the code and add GreatSQL Community Assistant<br/>
![](https://gitee.com/GreatSQL/GreatSQL-Doc/raw/master/docs/greatsql-wx-assist.jpg)

Or scan the code to join the GreatSQL community QQ group (533341697)<br/>
![](https://gitee.com/GreatSQL/GreatSQL-Doc/raw/master/docs/greatsql-qqqun.jpg)

In addition, we have released a series of videos related to MGR in Bilibili, you can go to learn, video link: https://space.bilibili.com/1363850082.

## 4. What is the GreatSQL version plan
GreatSQL does not plan to follow every minor version, and tentatively odd versions follow the way, that is, 8.0.25, 8.0.27, 8.0.29... And so on.

We will update if there are changes in the version plan in the future.

## 5. Does GreatSQL support read-write separation?
You can use MySQL Router to separate reads and writes.

## 6. Can I use MySQL Shell to manage GreatSQL?
Yes, it is best to use the same version number of the MySQL shell.

## 7. Are there any restrictions on using MGR

Here are some restrictions on the use of MGR:
- All tables must be InnoDB engine. Non-InnoDB engine tables can be created, but data cannot be written, and errors are reported when new nodes are built with Clones.
- All tables must have primary keys. As above, you can create a table without a primary key, but you cannot write data. You will also report an error when building a new node with Clone.
- Do not use large transactions. By default, transactions over 150MB will report errors, and transactions up to 2GB can be supported (in future versions of GreatSQL, support for large transactions will be increased, and the upper limit of large transactions will be increased).
- If you are upgrading from an older version, you cannot choose MINIMAL mode for upgrading. It is recommended to choose AUTO mode, that is, upgrade = AUTO .
- Since the MGR transaction authentication thread does not support gap lock , it is recommended to change the transaction isolation level of all nodes to READ COMMITTED . For the same reason, table lock and name lock (that is, the GET_LOCK () function) should not be used in MGR clusters.
- Serial ( SERIALIZABLE ) isolation levels are not supported in multi-primary mode.
- It is not supported to execute DML and DDL on the same table on different MGR nodes, which may cause data loss or node error exit.
- Multilevel cascaded foreign key tables are not supported in multi-primary mode. In addition, in order to avoid MGR errors caused by using foreign keys, it is recommended to set group_replication_enforce_update_everywhere_checks = ON .
- In multi-primary mode, if multiple nodes perform SELECT... FOR UPDATE Post-commit transactions cause deadlocks.
- The Replication Filters setting is not supported.
It seems that there are a lot of restrictions, but most of the time it does not affect normal business use.
In addition, there are several requirements to enable MGR:
- Binlog must be enabled for each node.
- Each node must dump binlog, that is, set log_slave_updates = 1 .
- The binlog format must be row mode, i.e. binlog_format = ROW .
- The server_id and server_uuid of each node cannot be the same.
- Before 8.0.20, binlog_checksum = NONE is required, but after 8.0.20, binlog_checksum = CRC32 can be set.
- Requires GTID enabled, i.e. set gtid_mode = ON .
- Requires master_info_repository = TABLE and relay_log_info_repository = TABLE , but since MySQL 8.0.23, these two options have been set by default TABLE, so there is no need to set them separately.
- The table name case parameters lower_case_table_names settings on all nodes are consistent.
- It is best to deploy MGR within the local area network, not across the public network. If the network delay is too large, the MGR will have poor performance or be prone to errors.
- It is recommended to enable writeset mode, that is, set the following parameters
  - slave_parallel_type = LOGICAL_CLOCK
  - slave_parallel_workers = N , N > 0, can be set to 2 times the number of logical CPUs
  - binlog_transaction_dependency_tracking = WRITESET
  - slave_preserve_commit_order = 1
  - slave_checkpoint_period = 2

## 8. Maximum number of nodes supported by MGR
MGR can support up to 9 nodes, either in single-master or multi-master mode.

## 9. Can MGR be set to self-start
Set the parameter group_replication_bootstrap_group = ON . However, when the first MGR node initializes and starts, or when the entire MGR cluster is closed and restarted, the first node must first adopt boot mode group_replication_bootstrap_group = ON .

## 10. Does MGR support read load balancing
Yes. You can mount MySQL Router on the front end of the MGR cluster to achieve read load balancing.

## 11. Does MGR support write load balancing
No. Because MGR uses the shared nothing mode, each node stores the full amount of data, so all writes to each node must be applied again.

## 12. Will MGR consume more resources such as CPU, memory and bandwidth than traditional leader/follower replication
To a certain extent, yes. Because MGR needs transaction collision detection between multiple nodes, but the overhead is limited and it is generally good.

## 13. Why is there an additional 33061 port after starting MGR
When the MGR service is enabled, MySQL listens on port 33061, which is used for communication between MGR nodes. So when there is a firewall policy between servers, remember to open it for that port.

Of course, you can define the port yourself, for example group_replication_local_address = 192.168.0.1:33062 .

## 14. Do you have to set hostnames for all nodes when deploying MGR
This is not necessary.

The reason for adding the hostname comparison table of each node on each node is that during the communication between MGR nodes, the host name that may be received is inconsistent with the actual local configuration.

In this case, you can also set your own report_host and report_port on each node to solve this problem.

## 15. Can I deploy MGR across public networks
Yes, but it is not recommended.
In addition, since MGR's default allowlist does not contain public network addresses, public network addresses need to be added, for example:
```
group_replication_ip_allowlist='192.0.2.0/24, 114.114.114.0/24'
```

By the way, the default allowlist range of MGR ( group_replication_ip_allowlist = AUTOMATIC ) is as follows
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
Sometimes the Internet Protocol Address of the docker container is not in the above range, which will also cause the MGR service to fail to start.


## 16. How to check whether MGR is currently in single-master or multi-master mode
Execute the following command:
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
If you see only one node with a MEMBER_ROLE value of PRIMARY , this is a single master pattern. If you see that the state value is PRIMARY on all nodes, it means that this is a multi-master mode.

Alternatively, you can confirm by querying the MySQL option values:
```
[root@GreatSQL]# mysqladmin var|grep -i group_replication_single_primary_mode
| group_replication_single_primary_mode        | ON
```
The value is ON , which means that the single master mode is used. If the value is OFF , it indicates a multi-master mode.
You can also check the status in the MySQL shell to confirm:
```
MySQL  GreatSQL:3306 ssl  JS > var c=dba.getCluster()
MySQL  GreatSQL:3306 ssl  JS > c.describe() /* 或者 c.status() */
...
        "topologyMode": "Single-Primary"
...
```

P.S, the single master mode is strongly recommended, the probability of encountering bugs or other problems is lower, and running MGR is more stable and reliable.


## 17. How to switch between single or multi-master
In MySQL client side command line mode, execute the following command:
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

Note: When switching, the master will be re-selected. The new master node may not be the one before switching. At this time, you can run the following command to re-specify:
```
[root@GreatSQL]> SELECT group_replication_set_as_primary('ed5fe7ba-37c2-11ec-8e12-70b5e873a570');
+--------------------------------------------------------------------------+
| group_replication_set_as_primary('ed5fe7ba-37c2-11ec-8e12-70b5e873a570') |
+--------------------------------------------------------------------------+
| Primary server switched to: ed5fe7ba-37c2-11ec-8e12-70b5e873a570         |
+--------------------------------------------------------------------------+
```

You can also use MySQL Shell to operate:
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
P.S, the single master mode is strongly recommended, the probability of encountering bugs or other problems is lower, and running MGR is more stable and reliable.

## 18. How to check if there is a delay in the MGR slave node
First, you can execute the following command to see if the current trx_tobe_applied or trx_tobe_verified values of other nodes except the PRIMARY node are large:
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

Wherein the value of trx_tobe_applied represents the size of the transaction queue waiting to be applied, trx_tobe_verified represents the size of the transaction queue waiting to be authenticated, either of which is greater than 0, indicating that there is currently a certain degree of delay.
In addition, you can also look at the gap between the received transaction and the executed transaction to judge:
```
[root@GreatSQL]> SELECT RECEIVED_TRANSACTION_SET FROM performance_schema.replication_connection_status WHERE  channel_name = 'group_replication_applier' UNION ALL SELECT variable_value FROM performance_schema.global_variables WHERE  variable_name = 'gtid_executed'\G
*************************** 1. row ***************************
RECEIVED_TRANSACTION_SET: 6cfb873b-573f-11ec-814a-d08e7908bcb1:1-3124520
*************************** 2. row ***************************
RECEIVED_TRANSACTION_SET: 6cfb873b-573f-11ec-814a-d08e7908bcb1:1-3078139
```
It can be seen that the received transaction GTID has reached 3124520, while the local execution only reached 3078139, and the difference between the two is 46381. By the way, we can keep an eye on the change of this difference and estimate whether the local node can match the delay or increase the delay.

## 19. Does MySQL Router support single-machine multi-instance deployment?
Yes, support.

When MySQL Router initializes deployment, add parameters such as --name , --directory and port number, for example:
```
-- deploy the first instance
root@GreatSQL# mysqlrouter --bootstrap mymgr@192.168.1.1:3306 --name=MGR1 --directory=/etc/mysqlrouter/MGR1  --user=mysqlrouter --conf-base-port=6446 --https-port=8443

-- deploy the second instance
root@GreatSQL# mysqlrouter --bootstrap mymgr@192.168.1.1:4306 --name=MGR2 --directory=/etc/mysqlrouter/MGR2  --user=mysqlrouter --conf-base-port=7446 --https-port=9443
```

Then each instance can start and stop with the start.sh and stop.sh scripts in their respective directories.
On the MySQL Router multi-instance deployment method, you can refer to this reference doc: "[Ask Ye#38, MGR whole cluster hung up, how to automatically select the main, without manual intervention](https://mp.weixin.qq.com/s/9eLnQ2EJIMQnZuEvScIhiw) .
