# 审计日志入表

[toc]

GreatSQL支持将审计日志写入数据表中，并且设置审计日志入表规则，以便达到不同的审计需求。

审计内容将包括操作账户、客户端ip、被操作的数据库对象、操作的完整语句、操作结果。

审计日志入表后，即可实现几个作用：
- 对登录失败行为进行审计。
- 对数据库服务的启动和关闭进行审计。
- 允许基于数据库操作类型对数据库的操作进行审计，允许配置1个到多个的数据操作类型进行审计。
- 允许基于数据库对象对数据库的操作进行审计，允许配置针对1个到多个的数据库对象的操作进行审计。
- 允许基于数据库用户的操作进行审计，允许配置针对1个到多个的数据库用户的操作进行审计。

```sql
--安装插件
greatsql> INSTALL PLUGIN audit_log SONAME 'audit_log.so';

--启用审计入表特性
greatsql> SET GLOBAL audit_log_to_table = 1;

--查看审计信息
greatsql> select * from sys_audit.audit_log\G
*************************** 1. row ***************************
         name: Query
       record: 16_2023-04-21T06:07:54
    timestamp: 2023-04-21T14:08:48Z
command_class: set_option
connection_id: 11
       status: 0
      sqltext: set global audit_log_to_table = 1
         user: root[root] @ localhost []
         host: localhost
      os_user:
           ip: 
           db: sys_audit
```

新增变量说明
```sql
greatsql> SHOW variables LIKE 'audit%';
+-----------------------------+---------------+
| Variable_name               | Value         |
+-----------------------------+---------------+
| audit_log_buffer_size       | 1048576       |
| audit_log_exclude_accounts  |               |
| audit_log_exclude_commands  |               |
| audit_log_exclude_databases |               |
| audit_log_file              | audit.log     |
| audit_log_flush             | OFF           |
| audit_log_format            | OLD           |
| audit_log_handler           | FILE          |
| audit_log_include_accounts  |               |
| audit_log_include_commands  |               |
| audit_log_include_databases |               |
| audit_log_policy            | ALL           |
| audit_log_rotate_on_size    | 0             |
| audit_log_rotations         | 0             |
| audit_log_strategy          | ASYNCHRONOUS  |
| audit_log_syslog_facility   | LOG_USER      |
| audit_log_syslog_ident      | percona-audit |
| audit_log_syslog_priority   | LOG_INFO      |
+-----------------------------+---------------+
```

**新增参数/选项**

| 参数/选项 | 默认值 | 备注 | 
| --- | --- | --- |
| audit_log_exclude_accounts  |   空  | 审计排除名单，用户规则                            |
| audit_log_exclude_commands  |   空  | 审计排除名单，命令规则                            |
| audit_log_exclude_databases |   空  | 审计排除名单，数据库规则                           |
| audit_log_include_accounts  |   空  | 审计包含名单，用户规则                            |
| audit_log_include_commands  |   空  | 审计包含名单，命令规则                            |
| audit_log_include_databases |   空  | 审计包含名单，数据库规则                           |
| audit_log_policy            | ALL | 指定审计事件，可选配置：ALL, LOGINS, QUERIES, NONE |

**应用案例**
```
-- 排除管理用户的操作记录
-- 注意，这里只是排除，而不是禁止管理员的操作
greatsql> set persist audit_log_exclude_accounts = 'root@localhost, admin@%, app_adm@%';

— 重置排除名单，注意这里要设置 = NULL，而不是 = 'NULL'
greatsql> set persist audit_log_exclude_accounts = NULL;

-- 查看审计日志（按时间倒序）
greatsql> select * from sys_audit.audit_log order by timestamp desc limit 10;
```
