#利用Ansible安装GreatSQL并构建MGR集群

本次介绍如何利用ansible一键安装GreatSQL并完成MGR部署。

本文介绍的运行环境是CentOS 7.9：
```
[root@greatsql ~]# cat /etc/redhat-release
CentOS Linux release 7.9.2009 (Core)

[root@greatsql ~]# uname -a
Linux greatsql 3.10.0-1160.11.1.el7.x86_64 #1 SMP Fri Dec 18 16:34:56 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
```

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
**提醒**
- 请填内网IP地址，因为MGR初始化时，默认使用用内网IP地址
- 所以，如果同时还要安装到本机，也请填写内网IP地址

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

第一步，**修改 /etc/hosts 设置正确的主机名**

修改几个服务器上的 /etc/hosts 文件，加入正确的主机名配置：
```
[root@greatsql ~]# cat /etc/hosts

172.16.16.10 mgr1
172.16.16.11 mgr2
172.16.16.12 mgr3
```

第二步，**下载GreatSQL-ansible安装包，解压缩**

打开GreatSQL-Ansible项目主页：[https://gitee.com/GreatSQL/GreatSQL-Ansible](https://gitee.com/GreatSQL/GreatSQL-Ansible)

找到页面右侧“发行版”，进入，选择 " GreatSQL-8.0.23-14-Linux.x86_64-ansible-v0.1-alpha.tar.xz" 这个二进制包下载到服务器上：

```
[root@greatsql ~]# cd /opt/greatsql/; wget -c "https://gitee.com/xxx/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal-centos7-ansible.tar.xz"

[root@greatsql ~]# tar zxf GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal-centos7-ansible.tar.xz
```

解压缩后，能看到除了 *GreatSQL-8.0.23-14-Linux.x86_64.tar.xz* 安装包之外，还有GreatSQL-ansible一键安装相关文件：
```
[root@greatsql ~]# cd /opt/greatsql/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal-centos7-ansible
[root@greatsql ~]# ls -la
-rw------- 1 root  root       333 Aug 11 15:22 check_mysql.yml
-rw------- 1 root  root  41817748 Aug 24 22:05 GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal.tar.xz
-rw------- 1 root  root        91 Aug 25 10:43 GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal.tar.xz.md5
-rw------- 1 root  root      5348 Aug 11 16:14 greatsql.yml
drwxr-xr-x 3 root  root      4096 Aug 25 10:43 mysql-support-files
-rw------- 1 root  root       394 Aug 25 11:03 vars.yml
```
几个文件作用分别介绍下：
- GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal.tar.xz，GreatSQL二进制安装包。
- greatsql.yml，ansible一键安装脚本。
- check_mysql.yml，MySQL进程、端口预检查脚本。
- vars.yml，定义一些变量的脚本，里面的变量名有些需要修改以适应各自不同的安装环境。

第三步，**利用ansible安装GreatSQL**

开始执行前，需要确认 *vars.yml* 文件中下面这些相关参数是否要调整：
```
work_dir: /opt/greatsql/GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal-centos7-ansible
extract_dir: /usr/local
data_dir: /data/GreatSQL
file_name: GreatSQL-8.0.23-14-Linux.x86_64.tar.xz
base_dir: /usr/local/GreatSQL-8.0.23-14-Linux.x86_64
my_cnf: /etc/my.cnf
mysql_user: mysql
mysql_port: 3306
mgr_user: repl
mgr_user_pwd: repl4MGR
mgr_seeds: '172.16.16.7:33061,172.16.16.10:33061,172.16.16.16:33061'
wait_for_start: 60
```
下面是关于这些参数的解释

|参数名 | 默认值 | 用途 |
|--- | --- | --- |
|work_dir|/opt/greatsql|工作目录，将下载的安装包放在本目录，可根据需要自行调整|
|extract_dir|/usr/local|GreatSQL二进制包解压缩后放在 /usr/local下，【不建议调整】|
|data_dir|/data/GreatSQL|GreatSQL运行时的datadir，【不建议调整】|
|file_name|GreatSQL-8.0.23-14-Linux.x86_64.tar.xz|GreatSQL二进制包文件名，【不建议调整】|
|base_dir|/usr/local/GreatSQL-8.0.23-14-Linux.x86_64|GreatSQL的basedir，【不建议调整】|
|my_cnf|/etc/my.cnf|my.cnf配置文件路径，【不建议调整】|
|mysql_user|mysql|运行GreatSQL对应的user、group，【不建议调整】|
|mysql_port|3306|GreatSQL运行时的监听端口，【不建议调整】|
|mgr_user|repl|MGR账户|
|mgr_user_pwd|repl4MGR|MGR账户密码|
|mgr_seeds|172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061|定义MGR运行时各节点的IP+端口列表，【需要自行调整】|
|wait_for_start|60|初次启动时，要先进行一系列数据文件初始化等工作，后面的MGR初始化工作要等待前面的先完成，如果第一安装失败，可以将这个时间加长|

**提醒：**除了修改work_dir和mgr_seeds参数外，其他的都请不要修改，否则可能会提示找不到文件目录等错误。

执行下面的命令一键完成GreatSQL的安装、初始化，加入systemd服务、以及MGR初始化等所有工作：
```
[root@greatsql ~]# ansible-playbook ./greatsql.yml
```

第四步，**检查运行过程输出**

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
172.16.16.10               : ok=26   changed=13   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
172.16.16.11               : ok=26   changed=13   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
172.16.16.12               : ok=26   changed=13   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

第五步，**检查安装结果**

有 **ok** 以及 **skipped=0** 字样，这就表示都被正常被执行了，此时应该已经安装成功了，检查一下：
```
[root@greatsql ~]# systemctl status greatsql
● greatsql.service - GreatSQL Server
   Loaded: loaded (/usr/lib/systemd/system/greatsql.service; disabled; vendor preset: disabled)
   Active: active (running) since Tue 2021-07-06 20:55:33 CST; 45s ago
     Docs: man:mysqld(8)
           http://dev.mysql.com/doc/refman/en/using-systemd.html
  Process: 31320 ExecStartPre=/usr/local/GreatSQL-8.0.23-14-Linux.x86_64/bin/mysqld_pre_systemd (code=exited, status=0/SUCCESS)
 Main PID: 31348 (mysqld)
   Status: "Server is operational"
   CGroup: /system.slice/greatsql.service
           └─31348 /usr/local/GreatSQL-8.0.23-14-Linux.x86_64/bin/mysqld

Jul 06 20:55:31 greatsql systemd[1]: Starting GreatSQL Server...
Jul 06 20:55:33 greatsql systemd[1]: Started GreatSQL Server.
```

检查MGR服务运行状态：
```
[root@GreatSQL][(none)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | ac24eab8-def4-11eb-a5e8-525400e802e2 |      mgr3   |        3306 | ONLINE       | SECONDARY   | 8.0.23         |
| group_replication_applier | ac275d97-def4-11eb-9e49-525400fb993a |      mgr2   |        3306 | ONLINE       | SECONDARY   | 8.0.23         |
| group_replication_applier | ac383458-def4-11eb-bf1a-5254002eb6d6 |      mgr1   |        3306 | ONLINE       | PRIMARY     | 8.0.23         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
```
至此，安装完成。

## 写在后面
本文描述的是利用ansible安装GreatSQL minimal版本。minimal版本是在完整版本的基础上，做了strip操作，所以文件尺寸较小，功能上没本质区别，仅是不支持gdb debug功能，可以放心使用。
P.S，实际上，您也可以利用这份ansible脚本安装完整版本，只需要自己手动调整 vars.yml 配置文件中的 file_name, base_dir 等参数。
类似地，如果您想自定义安装路径，也请相应修改 extract_dir, data_dir 等参数，不过 mysql-support-files 目录下的几个文件中的目录也自行修改。
