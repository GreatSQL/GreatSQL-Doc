# Ansible安装
---

本次介绍如何利用ansible快速安装GreatSQL并构建包含仲裁节点的MGR集群。

## 1. 安装准备

### 1.1 安装ansible

首先利用dnf/yum安装ansible：
```
$ yum install -y ansible
```

### 1.2 配置ansible

修改 `/etc/ansible/hosts` 文件，把要安装GreatSQL的服务器IP加进去，例如：
```
[greatsql_dbs:children]
greatsql_mgr_primary
greatsql_mgr_secondary
greatsql_mgr_arbitrator

[greatsql_mgr_primary]
172.16.16.10
[greatsql_mgr_secondary]
172.16.16.11
[greatsql_mgr_arbitrator]
172.16.16.12
```
**提醒**
- 请填内网IP地址，因为MGR初始化时，默认使用用内网IP地址
- 所以，如果同时还要安装到本机，也请填写内网IP地址，或者回环地址(127.0.0.1)

上面这个主机列表，分为三个组，一个是选择作为MGR PRIMARY节点的组 **greatsql_mgr_primary**；另一组选择作为SECONDARY节点 **greatsql_mgr_secondary**，有两个主机；还有个选择作为ARBITRATOR节点的组**greatsql_mgr_arbitrator**。

三个组最后合并一起，成为一个新的组 **greatsql_dbs**。

### 1.3 建立ssh信任
为了简单起见，直接建立ssh信任，方便ansible一键安装。

首先生成ssh key
```
$ ssh-keygen
```
使用缺省值，提示输入passphrase时，敲回车使用空的passphrase。

将ssh key复制到目标服务器上：
```
$ ssh-copy-id root@172.16.16.10
```
按提示输入口令，完成后测试使用ssh登录不再提示输入口令。如果是在本机安装，那么ssh-copy-id也要对本机执行一遍。或者手动将ssh key复制到远程主机上，写到 ~/.ssh/authorized_keys 文件中（注意不要折行、断行）。

### 1.4 测试ansible
随意执行一个指令，测试ansibile可连接远程主机：
```
$ ansible greatsql_dbs -a "uptime"
172.16.16.10 | CHANGED | rc=0 >>
 15:29:46 up 250 days, 19:40,  2 users,  load average: 0.04, 0.08, 0.07
172.16.16.11 | CHANGED | rc=0 >>
 15:29:46 up 303 days, 17:57,  3 users,  load average: 0.10, 0.13, 0.13
172.16.16.12 | CHANGED | rc=0 >>
 15:29:47 up 194 days, 18:08,  2 users,  load average: 0.07, 0.13, 0.10
```
这就表示可以正常运行了。

### 1.5 下载GreatSQL-Ansible安装包

[点击此处](https://gitee.com/GreatSQL/GreatSQL/releases/)下载最新的二进制安装包，可从下面几个任选一个：

- GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64-minimal.tar.xz
- GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64.tar.xz

再[点击此处](https://gitee.com/GreatSQL/GreatSQL-Ansible)下载Ansbile安装脚本及配置文件，包括以下文件/目录：

- mysql-support-files #内含my.cnf模板及systemd服务文件等
- greatsql.yml #ansible一键安装脚本。
- check_mysql.yml #MySQL进程、端口预检查脚本。
- vars.yml #定义一些变量的脚本，里面的变量名有些需要修改以适应各自不同的安装环境。


把这些下载的文件都放在 `/opt/greatsql` 目录下。

## 2. 安装GreatSQL并构建MGR集群

### 2.1 配置Ansible安装剧本

在开始安装前，要先修改 `vars.yml` 这个Ansbile安装剧本中的几个配置选项：
```
work_dir: /opt/greatsql/
extract_dir: /usr/local
data_dir: /data/GreatSQL
file_name: GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64-minimal.tar.xz
base_dir: /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64-minimal
my_cnf: /etc/my.cnf
mysql_user: mysql
mysql_port: 3306
mgr_user: GreatSQL
mgr_user_pwd: GreatSQL@2022
mgr_seeds: '172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061'
wait_for_start: 60
```
下面是关于这些参数的解释

|参数名 | 默认值 | 用途 |
|--- | --- | --- |
|work_dir|/opt/greatsql|工作目录，将下载的安装包放在本目录，可根据需要自行调整|
|extract_dir|/usr/local|GreatSQL二进制包解压缩后放在 /usr/local下，【不建议调整】|
|data_dir|/data/GreatSQL|GreatSQL运行时的datadir，【不建议调整】|
|file_name|GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64-minimal.tar.xz|GreatSQL二进制包文件名，【不建议调整】|
|base_dir|/usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64-minimal|GreatSQL的basedir，【不建议调整】|
|my_cnf|/etc/my.cnf|my.cnf配置文件路径，【不建议调整】|
|mysql_user|mysql|运行GreatSQL对应的user、group，【不建议调整】|
|mysql_port|3306|GreatSQL运行时的监听端口，【不建议调整】|
|mgr_user|repl|MGR账户|
|mgr_user_pwd|repl4MGR|MGR账户密码|
|mgr_seeds|172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061|定义MGR运行时各节点的IP+端口列表，【需要自行调整】|
|wait_for_start|60|初次启动时，要先进行一系列数据文件初始化等工作，后面的MGR初始化工作要等待前面的先完成，如果第一安装失败，可以将这个时间加长|

### 2.2 开始ansible安装

执行下面的命令一键完成GreatSQL的安装、初始化，加入systemd服务、以及MGR初始化等所有工作：
```
$ cd /opt/greatsql
$ ls
check_mysql.yml                                           GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64-minimal.tar.xz.md5  mysql-support-files
GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64-minimal.tar.xz  greatsql.yml                                                  vars.yml

$ ansible-playbook ./greatsql.yml
```

### 2.3 检查ansible执行过程输出

安装时会先行检查是否已有mysqld进程在运行，或者3306端口上是否已有其他服务，如果是的话，则输出内容可能会是这样的：
```
PLAY [install GreatSQL] *****************************************************************************************************************************

TASK [Gathering Facts] ******************************************************************************************************************************
ok: [172.16.16.10]
ok: [172.16.16.11]
ok: [172.16.16.12]

TASK [check mysql port] *****************************************************************************************************************************
changed: [172.16.16.10]
changed: [172.16.16.11]
changed: [172.16.16.12]

TASK [check mysql processor] ************************************************************************************************************************
changed: [172.16.16.10]
changed: [172.16.16.11]
changed: [172.16.16.12]

TASK [modify selinux config file] *******************************************************************************************************************
skipping: [172.16.16.10]
skipping: [172.16.16.11]
skipping: [172.16.16.12]
```

看到有 **skipping** 以及 **skipped=N** 字样。而如果是正常安装，则会输出类似下面的内容：
```
PLAY [install GreatSQL] *****************************************************************************************************************************

TASK [Gathering Facts] ******************************************************************************************************************************
ok: [172.16.16.10]
ok: [172.16.16.11]
ok: [172.16.16.12]

TASK [check mysql port] *****************************************************************************************************************************
changed: [172.16.16.10]
changed: [172.16.16.11]
changed: [172.16.16.12]
...
PLAY RECAP ******************************************************************************************************************************************
172.16.16.10               : ok=31   changed=20   unreachable=0    failed=0    skipped=0    rescued=0    ignored=2
172.16.16.11               : ok=31   changed=20   unreachable=0    failed=0    skipped=0    rescued=0    ignored=2
172.16.16.12               : ok=31   changed=20   unreachable=0    failed=0    skipped=0    rescued=0    ignored=2
```
有 **ok** 以及 **skipped=0** 字样，这就表示都被正常被执行了，此时应该已经安装成功了，检查一下：
```
$ systemctl status greatsql
● greatsql.service - GreatSQL Server
   Loaded: loaded (/usr/lib/systemd/system/greatsql.service; disabled; vendor preset: disabled)
   Active: active (running) since Wed 2022-07-13 15:46:21 CST; 4min 24s ago
     Docs: man:mysqld(8)
           http://dev.mysql.com/doc/refman/en/using-systemd.html
  Process: 77972 ExecStartPre=/usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64-minimal/bin/mysqld_pre_systemd (code=exited, status=0/SUCCESS)
 Main PID: 78043 (mysqld)
   Status: "Server is operational"
    Tasks: 38 (limit: 149064)
   Memory: 367.7M
   CGroup: /system.slice/greatsql.service
           └─78043 /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64-minimal/bin/mysqld

Jul 13 15:46:17 GreatSQL-01 systemd[1]: Starting GreatSQL Server...
Jul 13 15:46:21 GreatSQL-01 systemd[1]: Started GreatSQL Server.
```

检查MGR服务运行状态：
```
[root@GreatSQL][(none)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | ac24eab8-def4-11eb-a5e8-525400e802e2 | GreatSQL-03 |        3306 | ONLINE       | ARBITRATOR  | 8.0.25         |
| group_replication_applier | ac275d97-def4-11eb-9e49-525400fb993a | GreatSQL-02 |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | ac383458-def4-11eb-bf1a-5254002eb6d6 | GreatSQL-01 |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
```
至此，安装完成。


**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
