# 备份恢复
---

本文档介绍GreatSQL数据库的备份恢复方法，主要包括：
1. 逻辑备份恢复
2. 物理备份恢复

## 1. 逻辑备份恢复

`mysqldump` 是GreatSQL数据库自带的逻辑备份工具，可以实现对整个数据库、单库、单表，以及表中部分数据进行备份等多种方式。

### 1.1 全库备份

```
$ mysqldump -S/data/GreatSQL/mysql.sock -A --triggers --routines --events > /backup/GreatSQL/fullbackup-`date +'%Y%m%d'`.sql
```
除了备份数据之外，还备份触发器、存储函数、event等其他元数据。

如果不想备份触发器、存储函数、event的话，则去掉上述几个选项 `--triggers --routines --events`。

### 1.2 单库备份

```
$ export db="greatsql"
$ mysqldump -S/data/GreatSQL/mysql.sock --triggers --routines --events -B ${db} > /backup/GreatSQL/${db}-`date +'%Y%m%d'`.sql
```

如果不是备份全库数据，此时可能会有如下提示：
```
Warning: A partial dump from a server that has GTIDs will by default include the GTIDs of all transactions, even those that changed suppressed parts of the database. If you don't want to restore GTIDs, pass --set-gtid-purged=OFF. To make a complete dump, pass --all-databases --triggers --routines --events.
```

大意是本次是部分数据备份，无法用于全量恢复，因此加上 `gtid_purged` 有一定风险，建议手动加上选项 `--set-gtid-purged=OFF`。

这个选项建议不要加上，如果本次的逻辑备份文件用于后面的恢复时，再利用sed去掉 `gtid_purged` 信息，或者恢复之前先记录当时的 `gtid_purged` 信息，恢复结束后再还原回去。

### 1.3 单表备份

```
$ export db="greatsql"
$ export table="t1"
$ mysqldump -S/data/GreatSQL/mysql.sock --triggers --routines --events ${db} ${table} > /backup/GreatSQL/${db}-${table}-`date +'%Y%m%d'`.sql
```

### 1.4 只备份部分数据

运行 `mysqldump` 时，加上 `-w / --where` 选项，可以指定 WHERE过滤条件，达到只备份某一部分数据的目的，例如：
```
$ export db="greatsql"
$ export table="t1"

# 只备份单表的部分数据
$ mysqldump -S/data/GreatSQL/mysql.sock -w "id>=10000" ${db} ${table} > /backup/GreatSQL/${db}-${table}-partial-`date +'%Y%m%d'`.sql

# 备份单库所有表的部分数据
$ mysqldump -S/data/GreatSQL/mysql.sock -f -w "id>=10000" -B ${db} > /backup/GreatSQL/${db}-partial-`date +'%Y%m%d'`.sql
```

如果个别表没有where条件中指定的列名，则会报告类似下面的错误：
```
mysqldump: Couldn't execute 'SELECT /*!40001 SQL_NO_CACHE */ * FROM `t4` WHERE id>=1000000': Unknown column 'id' in 'where clause' (1054)
```

加上选项 `-f / --force` 后，备份任务依然可以继续，不影响后面其他表的备份。

### 1.5 逻辑备份恢复

逻辑备份文件恢复很简单，调用mysql客户端执行恢复，有两种方式：
```
mysql> source /backup/GreatSQL/greatsql-20220721.sql;
```
在mysql客户端工具里，执行 `source` 指令导入SQL文件。

或者
```
$ mysql -f -S/data/GreatSQL/mysql.sock greatsql < /backup/GreatSQL/greatsql-20220721.sql;
```
或者操作系统命令行模式下，直接用管道方式导入SQL文件。

关于 `mysqldump` 更详细说明详见文档：[mysqldump](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html)。

还可以利用 [mysqlpump](https://dev.mysql.com/doc/refman/8.0/en/mysqlpump.html) 以及 [mydumper](https://github.com/mydumper/mydumper) 实现并行备份，提高备份效率，这里不赘述。

参考资料：

- [mysqldump](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html)
- [mysqlpump](https://dev.mysql.com/doc/refman/8.0/en/mysqlpump.html)
- [mydumper](https://github.com/mydumper/mydumper)
- [如何从mysqldump全量备份中抽取部分库表用于恢复](https://imysql.com/2010/06/01/mysql-faq-how-to-extract-data-from-dumpfile.html)

## 2. 物理备份恢复

业内通常采用Percona出品的 `Xtrabackup` 工具执行物理备份和恢复，也可以利用MySQL企业版工具 `mysqlbackup` 实现物理备份恢复。

此外，从MySQL 8.0.17开始推出的 `Clone` 技术也可以很方便的实现物理备份恢复。

本文重点介绍利用 `Xtrabackup` 和 `Clone` 进行物理备份恢复。

## 3. Xtrabackup备份恢复

`Xtrabackup` 是由Percona公司出品的开源免费备份工具，它能很方便的对MySQL数据库进行在线热备，并且支持压缩、加密、流式备份等多种方式。

这是`Xtrabackup`安装包[下载地址](https://www.percona.com/downloads/Percona-XtraBackup-LATEST/)，这是[文档地址](https://docs.percona.com/percona-xtrabackup/latest/manual.html)。

本文档环境选择的是 `Xtrabackup 8.0.25-17` 版本。

可根绝个人喜好选择RPM包抑或二进制包，安装步骤略过。

`Xtrabackup`备份的流程大致如下：

1. 发起备份，初始化检查等；
2. 备份系统表空间文件ibdata1及各表空间.ibd文件；
3. 备份其他非InnoDB表；
4. 执行操作 `FLUSH NO_WRITE_TO_BINLOG BINARY LOGS`，刷新binlog；
5. 从`p_s.log_status`中获取最新的redo log lsn，以及binlog点位信息；
6. 备份最新的binlog文件（步骤4刷新后新产生的binlog文件）；
7. 更新备份目标目录下的binlog.index文件；
8. 更新xtrabackup_binlog_info文件；
9. 执行操作`FLUSH NO_WRITE_TO_BINLOG ENGINE LOGS`；
10. 备份ib_buffer_pool文件；
11. 备份结束。

而在Xtrabackup 2.X及更早的版本中，第5步这里直接执行FTWRL，不管是否只有InnoDB表。

在MySQL 8.0中（XtraBackup也响应升级到8.x版本），仅存在InnoDB表的话，不再执行FTWRL，而是直接读元数据。

### 3.1 常规全量备份

```
$ xtrabackup --backup --datadir=/data/GreatSQL/ --target-dir=/backup/GreatSQL/full/`date +'%Y%m%d'`/
...
xtrabackup: Transaction log of lsn (46865086) to (46876581) was copied.
220722 10:24:59 completed OK!

$ ls /backup/GreatSQL/`date +'%Y%m%d'`/
backup-my.cnf   binlog.000007  mysql.ibd                      db1   undo_001                xtrabackup_checkpoints  xtrabackup_tablespaces
ib_buffer_pool  binlog.index   mysql_innodb_cluster_metadata  sys   undo_002                xtrabackup_info
ibdata1         mysql          performance_schema             db2   xtrabackup_binlog_info  xtrabackup_logfile
```

几个选项的作用分别是：

- `--backup`，指定本次操作是备份
- `--datadir`，指定数据库的datadir
- `--target-dir`，指定本次备份的目标目录

备份完毕后，目标目录下的几个文件作用分别是：

- backup-my.cnf，记录执行xtrabackup相关选项参数，用于后续恢复
- xtrabackup_binlog_info，记录备份时的BINLOG及GTID信息，用于将数据恢复后作为从节点时设置主从复制相关选项
- xtrabackup_checkpoints，记录本次备份redo log的lsn及checkpoint信息，用于数据全量/增量恢复时的事务恢复点位判断
- xtrabackup_info，记录本次备份常规信息

### 3.2 只备份部分库表

```
$ xtrabackup --backup --datadir=/data/GreatSQL/ --tables="db1.t_user_*,db2.t_log_*" --target-dir=/backup/GreatSQL/partial/`date +'%Y%m%d'`/
...
xtrabackup: Transaction log of lsn (48318000) to (48324707) was copied.
220722 10:45:46 completed OK!

$ ls /backup/GreatSQL/`date +'%Y%m%d'`/
backup-my.cnf   ibdata1        binlog.index  db1  undo_001  xtrabackup_binlog_info  xtrabackup_info     xtrabackup_tablespaces
ib_buffer_pool  binlog.000006  mysql.ibd     db2  undo_002  xtrabackup_checkpoints  xtrabackup_logfile
```

### 3.3 压缩备份

在原来的基础上增加 `--compress` 选项即可，例如：
```
$ xtrabackup --backup --compress --datadir=/data/GreatSQL/ --target-dir=/backup/GreatSQL/full/`date +'%Y%m%d'`/
```
通常而言，大概有4倍左右的压缩比。

### 3.4 并行压缩，并且流式备份
```
$ xtrabackup --backup --stream=xbstream --compress --compress-threads=4 --datadir=/data/GreatSQL/ > /backup/GreatSQL/full/xbk-`date +'%Y%m%d'`.xbstream
```
并发4个线程压缩，并且采用流文件方式备份。

### 3.5 增量备份

Xtrabackup还支持增量备份，即在上一次备份的基础上，只备份发生新变化的数据。

发起增量备份前，得先有一份全量备份，才能有所谓的增量。
```
# 假定全备文件放在 /backup/GreatSQL/ 目录下
# 发起增量备份
$ xtrabackup --backup --incremental-basedir=/backup/GreatSQL/full/`date +'%Y%m%d'`/ --target-dir=/backup/GreatSQL/inc-backup/`date +'%Y%m%d%H'`/
```
查看`xtrabackup_info`和`xtrabackup_checkpoints`文件内容：
```
$ cat xtrabackup_info
...
innodb_from_lsn = 91534393  <--全备的LSN
innodb_to_lsn = 98570737  <--本次增背后的LSN
partial = N
incremental = Y  <--表示增备
format = file
compressed = N
encrypted = N

# 记录本次增备lsn相关信息
$ cat xtrabackup_checkpoints
backup_type = incremental
from_lsn = 91534393
to_lsn = 98570737
last_lsn = 98574379
flushed_lsn = 98574369
```

**建议：** 增量备份总是基于上一次全量备份的基础，不要基于上一次增量备份，这样在还原时会更方便。例如每天0点做一次全量备份，每小时做一次增量备份，执行增备时指定基于0点的全备。

### 3.5 全备还原

XtraBackup备份文件不能直接用来拉起数据库，需要先做预处理：
```
$ cd /backup/GreatSQL/full/`date +'%Y%m%d'`/
$ xtrabackup --prepare --target-dir=./
...
Starting shutdown...
Log background threads are being closed...
Shutdown completed; log sequence number 176148580
Number of pools: 1
220725 16:54:30 completed OK!
```

预处理没问题的话，就可以将数据文件copy/move到数据库目录下，用于拉起。

目标目录需要先清空，否则会报错。
```
$ cd /backup/GreatSQL/full/`date +'%Y%m%d'`/
$ xtrabackup --copy-back --target-dir=./ --datadir=/data/GreatSQL
...
220725 17:01:08 [01] Copying ./xtrabackup_master_key_id to /data/GreatSQL/xtrabackup_master_key_id
220725 17:01:08 [01]        ...done
220725 17:01:08 completed OK!

# 如果不想copy，而是move的话，修改下即可
$ xtrabackup --move-back --target-dir=./ --datadir=/data/GreatSQL
...
220725 17:02:01 [01] Moving ./xtrabackup_master_key_id to /data/GreatSQL/xtrabackup_master_key_id
220725 17:02:01 [01]        ...done
220725 17:02:01 completed OK!
```

### 3.6 全量压缩备份还原

先将流式文件恢复成正常压缩文件
```
$ cd /backup/GreatSQL/full/`date +'%Y%m%d'`
$ xbstream -x < xbk-`date +'%Y%m%d'`.xbstream
```

再进行解压缩：
```
$ cd /backup/GreatSQL/full/`date +'%Y%m%d'`
$ xtrabackup --decompress --target-dir=.
```

然后和上面一样，先 *--prepare* 后，再将还原出来的数据文件 *--copy-back* 到数据库目录下拉起即可。

P.S，解压缩过程中需要安装 `qpress`，可以从[这里下载源码或二进制文件](http://www.quicklz.com)。

### 3.7 增量备份还原

假定每天0点做一次全备，每小时做一次相对0点的增备，现在需要还原到当天8:00的增备时间点。可以像下面这么做：

首先，在全备文件目录下执行下面的操作（不执行事务回滚操作）：
```
$ cd /backup/GreatSQL/full/20220725
$ xtrabackup --prepare --apply-log-only --target-dir=/backup/GreatSQL/full/20220725
...
Log background threads are being closed...
Shutdown completed; log sequence number 101667236
Number of pools: 1
220725 10:45:23 completed OK!
```

接下来应用增备日志：
```
$ xtrabackup --prepare --apply-log-only --target-dir=/backup/GreatSQL/full/20220725 --incremental-dir=/backup/GreatSQL/inc-backup/2022072508
...
incremental backup from 101659735 is enabled.
xtrabackup: cd to /backup/GreatSQL/full/20220725
xtrabackup: This target seems to be already prepared with --apply-log-only.
Number of pools: 1
xtrabackup: xtrabackup_logfile detected: size=8388608, start_lsn=(101688040)
xtrabackup: using the following InnoDB configuration for recovery:
xtrabackup:   innodb_data_home_dir = .
xtrabackup:   innodb_data_file_path = ibdata1:12M:autoextend
xtrabackup:   innodb_log_group_home_dir = /backup/GreatSQL/inc-backup/2022072508/
...
xtrabackup: page size for /backup/GreatSQL/inc-backup/2022072508//ibdata1.delta is 16384 bytes
Applying /backup/GreatSQL/inc-backup/2022072508//ibdata1.delta to ./ibdata1...
...
220725 10:49:58 completed OK!
```

之后将还原后的数据文件copy/move到目标目录即可：
```
$ xtrabackup --copy-back --target-dir=/backup/GreatSQL/full/20220725 --datadir=/data/GreatSQL
...
220725 17:26:52 [01] Copying ./xtrabackup_info to /data/GreatSQL/xtrabackup_info
220725 17:26:52 [01]        ...done
220725 17:26:52 completed OK!
```

## 4. Clone备份恢复

MySQL 8.0.17中开始引入Clone Plugin插件。

利用Clone可以很方便的对MySQL中的InnoDB表（不支持非InnoDB表）执行物理备份，主要应用于几个场景：

1. 物理备份。
2. 主从复制架构中新增从节点。
3. MGR架构中新增节点。

使用Clone Plugin前，要先启用。有两种方法：

1. 在 `my.cnf` 文件的 `[mysqld]` 部分添加一行 `plugin-load-add=mysql_clone.so`，下次重启后即可生效。
2. 在mysql客户端中执行 `INSTALL PLUGIN clone SONAME 'mysql_clone.so';` 即可在线动态加载该Plugin。

此外，运行Clone的账号需要至少授予 `BACKUP_ADMIN` 权限：
```
mysql> grant BACKUP_ADMIN on *.* to backup_user;
```

### 4.1 Clone备份到本地
```
mysql> CLONE LOCAL DATA DIRECTORY = '/backup/GreatSQL/full/20220725/';
Query OK, 0 rows affected (0.17 sec)
```
这就完成了，是不是非常简单。

当然了，目标目录 `/backup/GreatSQL/full/20220725` 对 mysqld 进程运行的属主用户要有写入权限才行。

### 4.2 从远程主机Clone备份

Clone Plugin还支持从远程节点直接备份数据到本地，不过有几个前提条件：

1. 提供数据的远程实例需要至少授予 BACKUP_ADMIN 权限。
2. 接收数据的本地实例需要至少授予 CLONE_ADMIN 权限。
3. 提供和接收方必须是相同操作系统。
4. 同样地，只支持InnoDB表。

从远程主机Clone备份通常是在需要扩展主从复制或MGR新节点时使用，或者临时构建测试环境等。

首先，启动一个刚安装完毕的空实例，并对备份账户授予必要的权限：
```
# 先登入本地实例
$ mysql -h127.0.0.1 -ubackup_user -pXXX
...
# 开始Clone前，要设置 doner 节点
mysql> SET GLOBAL clone_valid_donor_list = '172.16.16.10:3306';

# 开始Clone
mysql> clone INSTANCE FROM backup_user@172.16.16.10:3306 IDENTIFIED BY 'Backup-For@GreatSQL';

# Clone完成后，会将本地数据全部覆盖，并且自动重启
...
ERROR 2013 (HY000): Lost connection to MySQL server during query
No connection. Trying to reconnect...
...
```
再次重连本地实例即可看到已经完成数据备份到当前实例了。

## 小结

MySQL的备份方式有多种多样，既有原生的mysqldump/mysqlpump/clone，也有第三方的xtrabackup/mydumper，周边生态非常完善，可根据实际情况及个人喜好自己选择趁手的工具。

**参考资料：**

- [The Clone Plugin](https://dev.mysql.com/doc/refman/8.0/en/clone-plugin.html)
- [mysqldump](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html)
- [mysqlpump](https://dev.mysql.com/doc/refman/8.0/en/mysqlpump.html)
- [mydumper](https://github.com/mydumper/mydumper)
- [如何从mysqldump全量备份中抽取部分库表用于恢复](https://imysql.com/2010/06/01/mysql-faq-how-to-extract-data-from-dumpfile.html)
- [XtraBackup](https://docs.percona.com/percona-xtrabackup/latest/manual.html)


**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
