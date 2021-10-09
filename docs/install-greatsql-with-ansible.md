# How to install GreatSQL and deploy MGR with Ansible

---

In this article we will introduce how to install GreatSQL and deploy MGR with Ansible.

Install and run GreatSQL in CentOS 7.9:
```
[root@greatsql ~]# cat /etc/redhat-release
CentOS Linux release 7.9.2009 (Core)

[root@greatsql ~]# uname -a
Linux greatsql 3.10.0-1160.11.1.el7.x86_64 #1 SMP Fri Dec 18 16:34:56 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
```

## 1. Install Ansbile
You can install Ansible with yum:
```
[root@greatsql ~]# yum install -y ansible
```

Check the version and confirm that the installation is successful:
```
[root@greatsql ~]# ansible --version
ansible 2.9.21
  config file = /etc/ansible/ansible.cfg
  configured module search path = [u'/root/.ansible/plugins/modules', u'/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/lib/python2.7/site-packages/ansible
  executable location = /usr/bin/ansible
  python version = 2.7.5 (default, Apr 2 2020, 13:16:51) [GCC 4.8.5 20150623 (Red Hat 4.8.5-39)]
```
This is OK.

## 2. Configure Ansible
Modify the `/etc/ansible/hosts` file to add the IP of the servers where GreatSQL is to be installed, for example:
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
If you are installing on the localhost, you can fill in the server’s intranet IP address or loopback address (127.0.0.1).

The above host list is divided into two groups, one is the group **greatsql_mgr_primary** selected as the MGR PRIMARY node, and there is only one host. The other group is chosen as the SECONDARY node **greatsql_mgr_secondary**, with two hosts. Two groups can also be merged together to form a new group **greatsql_dbs**.

## 3. Establish ssh trust
For the sake of simplicity, establish ssh trust for installation of Ansible.

First generate ssh key
```
[root@greatsql ~]# ssh-keygen
```

Use the default value. When prompted to enter a passphrase, press Enter to use an empty passphrase.

Copy the ssh key to the target server:
```
[root@greatsql ~]# ssh-copy-id root@172.16.16.10
```
Enter the password as prompted.

After the test is completed, use ssh to login and no longer prompt for the password.

If it is installed on the localhost, then ssh-copy-id should also be executed on the localhost. Or manually copy the ssh key to the remote host and write it to the ~/.ssh/authorized_keys file (be careful not to break or break lines).

## 4. Test Ansible
Execute an command to test that ansibile can connect to the remote host:
```
[root@greatsql ~]# ansible greatsql_dbs -a "uptime"
172.16.16.10 | CHANGED | rc=0 >>
 15:29:46 up 250 days, 19:40, 2 users, load average: 0.04, 0.08, 0.07
172.16.16.11 | CHANGED | rc=0 >>
 15:29:46 up 303 days, 17:57, 3 users, load average: 0.10, 0.13, 0.13
172.16.16.12 | CHANGED | rc=0 >>
 15:29:47 up 194 days, 18:08, 2 users, load average: 0.07, 0.13, 0.10
```
This is ok.

## 5. Use Ansible to automatically install GreatSQL

First, **modify /etc/hosts to set the correct hostname**

Modify the /etc/hosts files on several servers and add the correct hostname configuration:
```
[root@greatsql ~]# cat /etc/hosts

172.16.16.10 mgr1
172.16.16.11 mgr2
172.16.16.12 mgr3
```

Second, **download the GreatSQL-ansible installation package, unzip it**

Open the GreatSQL-Ansible project homepage: [https://github.com/GreatSQL/GreatSQL-Ansible](https://github.com/GreatSQL/GreatSQL-Ansible)

Find the "Release" on the right side of the page, enter, and select "GreatSQL-8.0.25-15-Linux-glibc2.17-x86_64-minimal-centos7-ansible.tar.xz" to download the binary package to the server:

```
[root@greatsql ~]# tar zxf GreatSQL-8.0.23-14-Linux.x86_64-ansible-v0.1-alpha.tar.xz
```

After unzipping, there are some files:
```
[root@greatsql ~]# ls -la
-rw-r--r-- 1 root root 327 Jul 13 11:26 check_mysql.yml
-rw-r--r-- 1 root root 15431496 Jul 13 12:00 GreatSQL-8.0.23-14-Linux.x86_64-ansible-v0.1-alpha.tar.xz
-rw-r--r-- 1 root root 15428212 Jul 7 12:43 GreatSQL-8.0.23-14-Linux.x86_64.tar.xz
-rw-r--r-- 1 root root 4393 Jul 7 15:33 greatsql.yml
-rw-r--r-- 1 root root 357 Jul 7 15:08 vars.yml
```

Some files:
-GreatSQL-8.0.23-14-Linux.x86_64.tar.xz, GreatSQL binary installation package.
-greatsql.yml, ansible playback script.
-check_mysql.yml, pre-check script.
-vars.yml, a script that defines some variables, some of the variable names inside need to be modified to adapt to different installation environments.

Third, **Using ansible to install GreatSQL**

Before running Ansible, you need to confirm whether the following variables in the *vars.yml* file need to be adjusted:
```
work_dir: /opt/greatsql
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

There is an explanation of these variables

|Variables name | Default value | Description |
| --- | --- | --- |
| work_dir | /opt/greatsql | Working directory, put the downloaded installation package in this directory, you can adjust it according to your needs |
|extract_dir|/usr/local|The GreatSQL binary package is decompressed and placed under /usr/local. [Adjustment is not recommended]|
|data_dir|/data/GreatSQL|Datadir when GreatSQL is running, [adjustment is not recommended]|
|file_name|GreatSQL-8.0.23-14-Linux.x86_64.tar.xz|GreatSQL binary package file name, [adjustment is not recommended]|
|base_dir|/usr/local/GreatSQL-8.0.23-14-Linux.x86_64|GreatSQL basedir, [adjustment not recommended]|
|my_cnf|/etc/my.cnf|my.cnf configuration file path, [adjustment is not recommended]|
|mysql_user|mysql|Run the user and group corresponding to GreatSQL, [adjustment is not recommended]|
|mysql_port|3306|The listening port when GreatSQL is running, [adjustment is not recommended]|
|mgr_user|repl|MGR account|
|mgr_user_pwd|repl4MGR|MGR account password|
|mgr_seeds|172.16.16.10:33061,172.16.16.11:33061,172.16.16.12:33061|Define the IP+port list of each node when MGR is running, [Need to adjust by yourself]|
|wait_for_start|60|When starting for the first time, a series of data file initialization and other tasks must be carried out. The subsequent MGR initialization work must wait for the previous completion first. If the first installation fails, this time can be lengthened|

Execute the following commands to complete the installation and initialization of GreatSQL, adding systemd services, and MGR initialization:
```
[root@greatsql ~]# ansible-playbook ./greatsql.yml
```

Fourth, **check the output of the running process**

During installation, it will first check whether there is a mysqld process running, or whether there are other services on port 3306. If so, the output may be like this:
```
PLAY [install GreatSQL] ********************************************* ************************************************** ******************************

TASK [Gathering Facts] ********************************************* ************************************************** *******************************
ok: [172.16.16.10]
ok: [172.16.16.11]
ok: [172.16.16.12]

TASK [check mysql port] ******************************************** ************************************************** *******************************
changed: [172.16.16.10]
changed: [172.16.16.11]
changed: [172.16.16.12]

TASK [check mysql processor] ******************************************** ************************************************** **************************
changed: [172.16.16.10]
changed: [172.16.16.11]
changed: [172.16.16.12]

TASK [modify selinux config file] ******************************************* ************************************************** **********************
skipping: [172.16.16.10]
skipping: [172.16.16.11]
skipping: [172.16.16.12]
```

You can see **skipping** and **skipped=N**. If it is installed successfully, it will output like following:
```
PLAY [install GreatSQL] ********************************************* ************************************************** ******************************

TASK [Gathering Facts] ********************************************* ************************************************** *******************************
ok: [172.16.16.10]
ok: [172.16.16.11]
ok: [172.16.16.12]

TASK [check mysql port] ******************************************** ************************************************** *******************************
changed: [172.16.16.10]
changed: [172.16.16.11]
changed: [172.16.16.12]
...
PLAY RECAP ************************************************ ************************************************** ****************************************
172.16.16.10: ok=26 changed=13 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
172.16.16.11: ok=26 changed=13 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
172.16.16.12: ok=26 changed=13 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

The fifth step, **check the installation result**

There are **ok** and **skipped=0**, which means that they have been executed successfully. At this time, the installation should have been successful. Check:
```
[root@greatsql ~]# systemctl status greatsql
● greatsql.service-GreatSQL Server
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

Check the running status of the MGR service:
```
[root@GreatSQL][(none)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------- -----------------+-------------+-------------+---- ----------+-------------+----------------+
| CHANNEL_NAME | MEMBER_ID | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------- -----------------+-------------+-------------+---- ----------+-------------+----------------+
| group_replication_applier | ac24eab8-def4-11eb-a5e8-525400e802e2 | mgr3 | 3306 | ONLINE | SECONDARY | 8.0.23 |
| group_replication_applier | ac275d97-def4-11eb-9e49-525400fb993a | mgr2 | 3306 | ONLINE | SECONDARY | 8.0.23 |
| group_replication_applier | ac383458-def4-11eb-bf1a-5254002eb6d6 | mgr1 | 3306 | ONLINE | PRIMARY | 8.0.23 |
+---------------------------+--------------------- -----------------+-------------+-------------+---- ----------+-------------+----------------+
```

At this point, the installation is complete.

## Others
This article describes the use of ansible to install the GreatSQL minimal package. The minimal package is stripped from the original package, so the file size is small and there is no essential difference in function. It just does not support the gdb debug function, so you can use it with confidence.

P.S. In fact, you can also use this ansible script to install the original package, you only need to manually change the file_name, base_dir and other variables in the vars.yml configuration file.

Similarly, if you want to customize the installation path, please change the extract_dir, data_dir and other variables accordingly, but the directories in the several files under the mysql-support-files directory should also be modified by yourself.
