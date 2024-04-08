# 8. 利用Ansible快速构建MGR | 深入浅出MGR

本次介绍如何利用ansible一键安装GreatSQL并完成MGR部署。

**提示**：从GreatSQL 8.0.32-25版本开始，我们不再更新发布GreatSQL Ansible安装包。若有需要采用Ansbile安装GreatSQL，可以选择使用 [芬达老师的dbops](https://gitee.com/fanderchan/dbops) 进行安装。

本文介绍的运行环境是CentOS 7.9：
```
[root@greatsql ~]# cat /etc/redhat-release
CentOS Linux release 7.9.2009 (Core)

[root@greatsql ~]# uname -a
Linux greatsql 3.10.0-1160.11.1.el7.x86_64 #1 SMP Fri Dec 18 16:34:56 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
```

准备好下面三台服务器：

| IP | 端口 | 角色 | 
| --- | --- | --- |
| 172.16.16.10 | 3306 | Primary | 
| 172.16.16.11 | 3306 | Secondary | 
| 172.16.16.12 | 3306 | Secondary | 

## 1. 安装ansbile  
直接用yum安装ansible即可：
```
[root@greatsql ~]# yum install -y ansible
```

查看版本号，确认安装成功：
```
[root@greatsql ~]# ansible --version
ansible 2.9.21
  config file = /etc/ansible/ansible.cfg
  configured module search path = [u'/root/.ansible/plugins/modules', u'/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/lib/python2.7/site-packages/ansible
  executable location = /usr/bin/ansible
  python version = 2.7.5 (default, Apr  2 2020, 13:16:51) [GCC 4.8.5 20150623 (Red Hat 4.8.5-39)]
```
这就OK了。

## 2. 配置ansible
修改 `/etc/ansible/hosts` 文件，把要安装GreatSQL的服务器IP加进去，例如：
```
[greatsql_dbs:children]
greatsql_mgr_primary
greatsql_mgr_secondary

[greatsql_mgr_primary]
172.16.16.10
[greatsql_mgr_secondary]
172.16.16.11
172.16.16.12
```
如果是在本机安装，直接填写本机的内网IP地址或回环地址（127.0.0.1）均可。

上面这个主机列表，分为两个组，一个是选择作为MGR PRIMARY节点的组 **greatsql_mgr_primary**，只有一个主机。另一组选择作为SECONDARY节点 **greatsql_mgr_secondary**，有两个主机。两个组也可以合并一起，成为一个新的组 **greatsql_dbs**。

## 3. 建立ssh信任
为了简单起见，直接建立ssh信任，方便ansible一键安装。

首先生成ssh key
```
[root@greatsql ~]# ssh-keygen
```
使用缺省值，提示输入passphrase时，敲回车使用空的passphrase。

将ssh key复制到目标服务器上：
```
[root@greatsql ~]# ssh-copy-id root@172.16.16.10
```
按提示输入口令，完成后测试使用ssh登录不再提示输入口令。如果是在本机安装，那么ssh-copy-id也要对本机执行一遍。或者手动将ssh key复制到远程主机上，写到 ~/.ssh/authorized_keys 文件中（注意不要折行、断行）。

## 4. 测试ansible
随意执行一个指令，测试ansibile可连接远程主机：
```
[root@greatsql ~]# ansible greatsql_dbs -a "uptime"
172.16.16.10 | CHANGED | rc=0 >>
 15:29:46 up 250 days, 19:40,  2 users,  load average: 0.04, 0.08, 0.07
172.16.16.11 | CHANGED | rc=0 >>
 15:29:46 up 303 days, 17:57,  3 users,  load average: 0.10, 0.13, 0.13
172.16.16.12 | CHANGED | rc=0 >>
 15:29:47 up 194 days, 18:08,  2 users,  load average: 0.07, 0.13, 0.10
```
这就表示可以正常运行了。

## 5. 使用ansible自动安装GreatSQL

### 5.1 修改 /etc/hosts 设置正确的主机名

修改几个服务器上的 /etc/hosts 文件，加入正确的主机名配置：
```
[root@greatsql ~]# cat /etc/hosts

172.16.16.10 mgr1
172.16.16.11 mgr2
172.16.16.12 mgr3
```

### 5.2 下载GreatSQL-ansible安装包，解压缩

打开GreatSQL-Ansible项目主页：[https://gitee.com/GreatSQL/GreatSQL-Ansible](https://gitee.com/GreatSQL/GreatSQL-Ansible)

找到页面右侧“发行版”，进入，选择 *GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal-centos7-ansible.tar.xz* 这个二进制包下载到服务器上：

```
[root@greatsql ~]# cd /opt/greatsql/
[root@greatsql ~]# tar xf GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal-centos7-ansible.tar.xz
```

解压缩后，能看到除了 *GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal.tar.xz* 安装包之外，还有GreatSQL-ansible一键安装相关文件：
```
[root@greatsql ~]# ls -la
-rw-------. 1 root root      333 Aug 11 15:22 check_mysql.yml
-rw-------. 1 root root 41817748 Aug 24 22:05 GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal.tar.xz
-rw-------. 1 root root       91 Aug 25 10:43 GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal.tar.xz.md5
-rw-------. 1 root root     5348 Aug 11 16:14 greatsql.yml
drwxr-xr-x. 3 root root      103 Aug 25 10:43 mysql-support-files
-rw-------. 1 root root      394 Aug 25 10:43 vars.yml
```
几个目录文件作用分别介绍下：
- GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal.tar.xz，GreatSQL二进制安装包。
- greatsql.yml，ansible一键安装脚本。
- check_mysql.yml，MySQL进程、端口预检查脚本。
- vars.yml，定义一些变量的脚本，里面的变量名有些需要修改以适应各自不同的安装环境。
- mysql-support-files，存放my.cnf模板，systemd服务文件等多个文件。

### 5.3 利用ansible安装GreatSQL

开始执行前，需要确认 *vars.yml* 文件中下面这些相关参数是否要调整：
```
work_dir: /opt/greatsql
extract_dir: /usr/local
data_dir: /data/GreatSQL
file_name: GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal.tar.xz
base_dir: /usr/local/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal
my_cnf: /etc/my.cnf
mysql_user: mysql
mysql_port: 3306
mgr_user: repl
mgr_user_pwd: repl4MGR
mgr_seeds: '172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061'
wait_for_start: 60
```
下面是关于这些参数的解释

|参数名 | 默认值 | 用途 |
|--- | --- | --- |
|work_dir|/opt/greatsql|工作目录，将下载的安装包放在本目录，可根据需要自行调整|
|extract_dir|/usr/local|GreatSQL二进制包解压缩后放在 /usr/local下，【不建议调整】|
|data_dir|/data/GreatSQL|GreatSQL运行时的datadir，【不建议调整】|
|file_name|GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal.tar.xz|GreatSQL二进制包文件名，【不建议调整】|
|base_dir|/usr/local/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal|GreatSQL的basedir，【不建议调整】|
|my_cnf|/etc/my.cnf|my.cnf配置文件路径，【不建议调整】|
|mysql_user|mysql|运行GreatSQL对应的user、group，【不建议调整】|
|mysql_port|3306|GreatSQL运行时的监听端口，【不建议调整】|
|mgr_user|repl|MGR账户|
|mgr_user_pwd|repl4MGR|MGR账户密码|
|mgr_seeds|172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061|定义MGR运行时各节点的IP+端口列表，【需要自行调整】|
|wait_for_start|60|初次启动时，要先进行一系列数据文件初始化等工作，后面的MGR初始化工作要等待前面的先完成，如果因为等待的时间不够导致安装失败，可以将这个时间加长|

执行下面的命令一键完成GreatSQL的安装、初始化，加入systemd服务、以及MGR初始化等所有工作：
```
[root@greatsql ~]# ansible-playbook ./greatsql.yml
```

### 5.4 检查Ansible运行过程输出

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
172.16.16.10               : ok=27   changed=14   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
172.16.16.11               : ok=27   changed=14   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
172.16.16.12               : ok=27   changed=14   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### 5.5 检查GreatSQL安装结果

有 **ok** 以及 **skipped=0** 字样，这就表示都被正常被执行了，此时应该已经安装成功了，检查一下：
```
[root@greatsql ~]# systemctl status greatsql
● greatsql.service - GreatSQL Server
   Loaded: loaded (/usr/lib/systemd/system/greatsql.service; disabled; vendor preset: disabled)
   Active: active (running) since Tue 2021-07-06 20:55:33 CST; 45s ago
     Docs: man:mysqld(8)
           http://dev.mysql.com/doc/refman/en/using-systemd.html
  Process: 31320 ExecStartPre=/usr/local/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal/bin/mysqld_pre_systemd (code=exited, status=0/SUCCESS)
 Main PID: 31348 (mysqld)
   Status: "Server is operational"
   CGroup: /system.slice/greatsql.service
           └─31348 /usr/local/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal/bin/mysqld

Jul 06 20:55:31 greatsql systemd[1]: Starting GreatSQL Server...
Jul 06 20:55:33 greatsql systemd[1]: Started GreatSQL Server.
```

检查MGR服务运行状态：
```
[root@GreatSQL][(none)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | ac24eab8-def4-11eb-a5e8-525400e802e2 |      mgr3   |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | ac275d97-def4-11eb-9e49-525400fb993a |      mgr2   |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | ac383458-def4-11eb-bf1a-5254002eb6d6 |      mgr1   |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
```
这就完成MGR集群的构建了。

## 6. 小结
本问介绍了如何利用Ansible快速安装GreatSQL并构建MGR集群，以上ansible脚本已上传到gitee仓库中，详见：[https://gitee.com/GreatSQL/GreatSQL-Ansible](https://gitee.com/GreatSQL/GreatSQL-Ansible) ，欢迎大家提出更多改进建议。

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
