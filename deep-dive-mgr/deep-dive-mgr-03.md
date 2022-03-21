# 3. 安装部署MGR集群 | 深入浅出MGR

[toc]

本文介绍如何利用GreatSQL 8.0.25构建一个三节点的MGR集群。

## 1. 安装准备
准备好下面三台服务器：

| IP | 端口 | 角色 | 
| --- | --- | --- |
| 172.16.16.10 | 3306 | mgr1 | 
| 172.16.16.11 | 3306 | mgr2 | 
| 172.16.16.12 | 3306 | mgr3 | 

确保三个节点间的网络是可以互通的，并且没有针对3306和33061端口的防火墙拦截规则。

下载GreatSQL二进制文件包，下载地址：*https://gitee.com/GreatSQL/GreatSQL/releases* 。

本文以 CentOS x86_64 环境为例，下载的二进制包名为： `GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64.tar.xz`，放在 `/usr/local` 目录下并解压缩：
```
$ cd /usr/local
$ tar xf GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64.tar.xz
$ cd GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64
$ ls
bin    COPYING-jemalloc  include  LICENSE         LICENSE-test  mysqlrouter-log-rotate  README.router  run    support-files
cmake  docs              lib      LICENSE.router  man           README                  README-test    share  var
```

## 2. 初始化MySQL Server
首先准备好 */etc/my.cnf* 配置文件：
```
#/etc/my.cnf
[mysqld]
user = mysql
basedir=/usr/local/GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64
datadir=/data/GreatSQL
port=3306
server_id=103306
log-bin
log_slave_updates=1
gtid_mode=ON
enforce_gtid_consistency=ON
```
本文仅以能正常启动MySQL Server和部署MGR为目的，所以这份配置文件极为简单，如果想要在正式场合使用，可以参考[这份配置文件](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example)。

先初始化MySQL Server：
```
$ mkdir -p /data/GreatSQL && chown -R mysql:mysql /data/GreatSQL
$ /usr/local/GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64/bin/mysqld --defaults-file=/etc/my.cnf --initialize-insecure
```
**注意**：不要在生产环境中使用 `--initialize-insecure` 选项进行初始化安装，因为这么做的话，超级管理员root账号默认是空密码，任何人都可以使用该账号登录数据库，存在安全风险，本文中只是为了演示方便才这么做。

启动MySQL Server：
```
$ /usr/local/GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64/bin/mysqld --defaults-file=/etc/my.cnf &
```
如果不出意外，则能正常启动MySQL Server。用同样的方法也完成对另外两个节点的初始化。

此外，建议把GreatSQL加入系统systemd服务中，方便管理。具体方法可以参考这篇文章：[将GreatSQL添加到系统systemd服务](https://mp.weixin.qq.com/s/tSA-DrWT13GN45Csq2tQoA)。

## 3. 初始化MGR第一个节点
接下来准备初始化MGR的第一个节点，也称之为 **引导节点**。

修改 */etc/my.cnf* ，增加以下几行和MGR相关的配置参数：
```
plugin_load_add='group_replication.so'
group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"
group_replication_local_address= "172.16.16.10:33061"
group_replication_group_seeds= "172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061"
report-host=172.16.16.10
```
选项 `report-host` 的作用是向MGR其他节点报告本节点使用的地址，避免某个服务器上有多个主机名时，可能无法正确找到对应关系而使得MGR无法启动的问题。此外，设置了 `report-host` 后，修改 `/etc/hosts` 系统文件加入各节点的地址及主机名这个步骤就不是必须的了。

另外，注意上面配置的端口写的是 **33061** 而不是 **3306**，这是为MGR服务指定专用的通信端口，区别于MySQL正常的读写服务端口。这里的 33061 端口号可以自定义，例如写成 12345 也可以，注意该端口不能被防火墙拦截。

利用这份配置文件，重启MySQL Server，之后就应该能看到已经成功加载 `group_replicaiton` 插件了：
```
mysql> show plugins;
...
+---------------------------------+----------+--------------------+----------------------+---------+
| Name                            | Status   | Type               | Library              | License |
+---------------------------------+----------+--------------------+----------------------+---------+
...
| group_replication               | ACTIVE   | GROUP REPLICATION  | group_replication.so | GPL     |
...
```

如果没正确加载，也可以登入MySQL Server自行手动加载这个plugin：
```
myqsl> install plugin group_replication soname 'group_replication.so';
```

接下来，创建MGR服务专用账户，并准备配置MGR服务通道：
```
#每个节点都要单独创建用户，因此这个操作没必要记录binlog并复制到其他节点
mysql> set session sql_log_bin=0;
mysql> create user repl@'%' identified by 'repl';
mysql> GRANT BACKUP_ADMIN, REPLICATION SLAVE ON *.* TO `repl`@`%`;
#创建完用户后继续启用binlog记录
mysql> set session sql_log_bin=1;

#配置MGR服务通道
#通道名字 group_replication_recovery 是固定的，不能修改
mysql> CHANGE MASTER TO MASTER_USER='repl', MASTER_PASSWORD='repl' FOR CHANNEL 'group_replication_recovery';
```

接着执行下面的命令，将其设置为MGR的引导节点（只有第一个节点需要这么做）后即可直接启动MGR服务：
```
mysql> set global group_replication_bootstrap_group=ON;

mysql> start group_replication;
```
**提醒**：当整个MGR集群重启时，第一个启动的节点也要先设置为引导模式，然后再启动其他节点。除此外，请勿设置引导模式。

而后，查看MGR服务状态：
```
mysql> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST  | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 4ebd3504-11d9-11ec-8f92-70b5e873a570 | 172.16.16.10 |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
好了，第一个节点初始化完成。

## 4. 继续设置另外两个节点
继续使用下面这份 */etc/my.cnf* 配置文件模板：
```
#my.cnf
[mysqld]
user = mysql
basedir=/usr/local/GreatSQL-8.0.25-15-Linux-glibc2.28-x86_64
datadir=/data/GreatSQL
port=3306
server_id=113306
log-bin
log_slave_updates=1
gtid_mode=ON
enforce_gtid_consistency=ON

#mgr
plugin_load_add='group_replication.so'
group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"
group_replication_local_address= "172.16.16.11:33061"
group_replication_group_seeds= "172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061"
report-host=172.16.16.11
```
**提醒**：上面的几个选项中，`server_id`、`group_replication_local_address` 和 `report_host` 这三个选项要修改为正确的值。在一个MGR集群中，各节点设置的 `server_id` 和 `server_uuid` 要是唯一的，但是 `group_replication_group_name` 的值要一样，这是该MGR集群的唯一标识。

重启MySQL Server实例后（`report-host` 是只读选项，需要重启才能生效），创建MGR服务专用账号及配置MGR服务通道：
```
mysql> set session sql_log_bin=0;
mysql> create user repl@'%' identified by 'repl';
mysql> GRANT BACKUP_ADMIN, REPLICATION SLAVE ON *.* TO `repl`@`%`;
mysql> set session sql_log_bin=1;

mysql> CHANGE MASTER TO MASTER_USER='repl', MASTER_PASSWORD='repl' FOR CHANNEL 'group_replication_recovery';
```

接下来即可直接启动MGR服务（除了第一个节点外，其余节点都不需要再设置引导模式）：
```
mysql> start group_replication;
```
再次查看MGR节点状态：
```
mysql> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST  | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 4ebd3504-11d9-11ec-8f92-70b5e873a570 | 172.16.16.10 |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | 549b92bf-11d9-11ec-88e1-70b5e873a570 | 172.16.16.11 |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | 5596116c-11d9-11ec-8624-70b5e873a570 | 172.16.16.12 |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+--------------+-------------+--------------+-------------+----------------+
```
看到上面这个集群共有3个节点处于ONLINE状态，其中 *172.16.16.10* 是 **PRIMARY** 节点，其余两个都是 **SECONDARY** 节点，也就是说当前这个集群采用 **单主** 模式。如果采用多主模式，则所有节点的角色都是 **PRIMARY**。

## 5. 向MGR集群中写入数据
接下来我们连接到 **PRIMARY** 节点，创建测试库表并写入数据：
```
$mysql -h172.16.16.10 -uroot -Spath/mysql.sock
mysql> create database mgr;
mysql> use mgr;
mysql> create table t1(c1 int unsigned not null primary key);
mysql> insert into t1 select rand()*10240;
mysql> select * from t1;
+------+
| c1   |
+------+
| 8078 |
+------+
```
再连接到其中一个 **SECONDARY** 节点，查看刚刚在 **PRIMARY** 写入的数据是否可以看到：
```
$mysql -h172.16.16.11 -uroot -Spath/mysql.sock
mysql> use mgr;
mysql> select * from t1;
+------+
| c1   |
+------+
| 8078 |
+------+
```
确认可以读取到该数据。

到这里，就完成了三节点MGR集群的安装部署。


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