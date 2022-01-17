# 9. 利用Docker快速构建MGR | 深入浅出MGR

[toc]

为了方面社区用户体验GreatSQL，我们同时还提供Docker镜像，本文详细介绍如何在Docker中部署GreatSQL，并且构建一个MGR集群。

本文涉及的运行环境如下：
```
[root@greatsql]# cat /etc/redhat-release
CentOS Linux release 7.9.2009 (Core)

[root@greatsql]# uname -a
Linux GreatSQL 3.10.0-1160.11.1.el7.x86_64 #1 SMP Fri Dec 18 16:34:56 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
```

## 1、安装Docker
直接用yum安装docker，非常省事
```
[root@greatsql]# yum install -y docker
```

之后启动 docker 服务，并设置开机自启动
```
[root@greatsql]# systemctl enable docker
[root@greatsql]# systemctl start docker
```

## 2、拉取GreatSQL镜像，并创建容器
### 2.1 拉取镜像
拉取GreatSQL官方镜像
```
[root@greatsql]# docker pull greatsql/greatsql
docker pull greatsql/greatsql
Using default tag: latest
Trying to pull repository docker.io/greatsql/greatsql ...
latest: Pulling from docker.io/greatsql/greatsql
...
Digest: sha256:e3c7b3dcebcbb6e2a1ab60993f0999c9ce7e1c85e4a87ab4022d2c1351840f6f
Status: Downloaded newer image for docker.io/greatsql/greatsql:latest
```
检查是否成功
```
[root@greatsql]# docker images
REPOSITORY                    TAG                 IMAGE ID            CREATED             SIZE
docker.io/greatsql/greatsql   latest              1130a28e310b        3 days ago          570 MB
```

### 2.2 创建新容器
之后，就可以直接创建一个新的容器了，先用常规方式
```
[root@greatsql]# docker run -d \
--name mgr1 --hostname=mgr1 \
-p 3306:3306 -p 33060:33060 -p 33061:33061 \
-e MYSQL_ALLOW_EMPTY_PASSWORD=1 \
-e MYSQL_IBP=1G \
-e MYSQL_MGR_NAME='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1' \
-e MYSQL_MGR_LOCAL='172.17.0.2:33061' \
-e MYSQL_MGR_SEEDS='172.17.0.2:33061,172.17.0.3:33061,172.17.0.4:33061' \
-e MYSQL_INIT_MGR=1 \
-e MYSQL_MGR_USER='repl' \
-e MYSQL_MGR_USER_PWD='repl' \
-e MYSQL_SID=330602
greatsql/greatsql
```

几个参数分别解释如下

| 参数 | 必选/可选 | 默认值 | 解释 |
|---|---|---|---|
|-d| 必选 | 无 | 声明以daemon守护进程方式运行，而不是一次性运行 |
| --name mgr1| 可选 | 随机生成 | 指定容器名，方便后面调用 |
| --hostname mgr1| 可选| 容器ID | 指定容器内的主机名，否则会用容器ID作为主机名|
| -p 3306:3306| 可选| 无 | 指定容器要暴露的端口号，方便用TCP方式远程连接 |
| -e MYSQL_ALLOW_EMPTY_PASSWORD=1| 必选 | 无 | 允许root使用空密码（本案中启用该选项，为了方便），也可以指定密码，或者使用随机密码，下面介绍 |
| -e MYSQL_IBP=1G| 可选| 128M| 设置 innodb_buffer_pool_size 的值  |
|-e MYSQL_MGR_NAME='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1'|可选|aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1|设置MGR集群名
|-e MYSQL_MGR_LOCAL='172.17.0.2:33061'|可选| 172.17.0.2:33061|设置MGR本地节点IP+PORT|
|-e MYSQL_MGR_SEEDS='172.17.0.2:33061,<br/>172.17.0.3:33061,<br/>172.17.0.4:33061'|可选| 172.17.0.2:33061,172.17.0.3:33061|设置MGR集群各节点列表
|-e MYSQL_INIT_MGR=1|可选|0|自动初始化MGR相关工作|
|-e MYSQL_MGR_USER='repl'|可选|repl|设置MGR服务账户名|
|-e MYSQL_MGR_USER_PWD='repl'|可选| repl4MGR |设置MGR服务账户密码|
|-e MYSQL_SID|可选|3306+3位随机数|设置MySQL的server_id，利用MySQL Shell接管MGR时，要求每个实例的server_id要设置为不同值。如果不手动指定，则会自动生成随机数值|

`greatsql/greatsql`，是镜像名，也可以指定为镜像的ID，例如 `1130a28e310b`。

如果不想让 root 账户使用空密码，可以把 `MYSQL_ALLOW_EMPTY_PASSWORD=1` 参数替换成诸如 `MYSQL_ROOT_PASSWORD='GreatSQL3#)^'` 或者指定随机密码 `MYSQL_RANDOM_ROOT_PASSWORD=1` 即可。

当启用选项 `MYSQL_INIT_MGR=1` 时，会自动创建MGR所需的账户，并执行 `CHANGE MASTER TO` 指定MGR复制通道。若没有同时指定 `MYSQL_MGR_USER` 或 `MYSQL_MGR_USER_PWD` 的话，则采用各自的默认值创建MGR账户。

这就成功创建一个新的容器了，并且会自动完成GreatSQL的初始化并启动。

### 2.3 容器管理
先确认容器的状态
```
[root@greatsql]# docker ps -a
CONTAINER ID        IMAGE                    COMMAND                  CREATED             STATUS              PORTS                       NAMES
2e277c852f52        greatsql/greatsql        "/docker-entrypoin..."   4 minutes ago       Up 12 minutes        3306/tcp, 33060-33061/tcp   mgr1
```
看到容器状态是Up的，表示已正常启动了。

再进入容器查看
```
[root@greatsql]# docker exec -it mgr1 /bin/bash
[root@mgr1 ~]# mysqladmin ver
...
Server version:         8.0.25-15 GreatSQL, Release 15, Revision c7feae175e0
Protocol version	10
Connection		Localhost via UNIX socket
UNIX socket		/data/GreatSQL/mysql.sock
Uptime:			11 min 19 sec

Threads: 2  Questions: 2  Slow queries: 0  Opens: 120  Flush tables: 3  Open tables: 36  Queries per second avg: 0.002
```
看到容器已经完成初始化，并且可以直接无密码登入。

查看MGR账户及相应复制通道
```
[root@GreatSQL][(none)]> show grants for repl;
+----------------------------------------------+
| Grants for repl@%                            |
+----------------------------------------------+
| GRANT REPLICATION SLAVE ON *.* TO `repl`@`%` |
| GRANT BACKUP_ADMIN ON *.* TO `repl`@`%`      |
+----------------------------------------------+

[root@GreatSQL][none]> select * from performance_schema.replication_group_members;
+---------------------------+-----------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+-----------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier |           |             |        NULL | OFFLINE      |             |                |
+---------------------------+-----------+-------------+-------------+--------------+-------------+----------------+
```

## 3、构建MGR集群
跨宿主机之间的docker容器网络通信相对麻烦一些，为了简单起见，本次先在单机环境下构建由3个docker容器组成的MGR集群。

### 3.1 创建专用子网
首先创建一个用于MGR集群的网络：
```
[root@greatsql]# docker network create mgr-net

[root@greatsql]# docker network ls
NETWORK ID          NAME                DRIVER              SCOPE
70c3ac08c7a9        bridge              bridge              local
3a480a3ec570        host                host                local
191d6d902b26        mgr-net             bridge              local
1e3e6267dcda        none                null                local
```

查看这个子网的配置信息：
```
[root@greatsql]# docker inspect  mgr-net
[
    {
        "Name": "mgr-net",
...
                    "Subnet": "172.18.0.0/16",   <-- 网段
                    "Gateway": "172.18.0.1"   <-- 网关
...
```

### 3.2 创建3个新容器
分别启动三个docker容器：
```
[root@greatsql]# docker run -d \
--name mgr1 --hostname=mgr1 --net=mgr-net \
-e MYSQL_ALLOW_EMPTY_PASSWORD=1 \
-e MYSQL_MGR_LOCAL='172.18.0.2:33061' \
-e MYSQL_MGR_SEEDS='172.18.0.2:33061,172.18.0.3:33061,172.18.0.4:33061' \
-e MYSQL_INIT_MGR=1 \
greatsql/greatsql
```
后面的两个实例，只把 --name 和 --hostname 参数中的mgr1改成mgr2、mgr3，并且把 `-e MYSQL_MGR_LOCAL='172.18.0.2:33061'` 参数的的IP地址递增，例如 `-e MYSQL_MGR_LOCAL='172.18.0.3:33061'`。

查看容器运行状态：
```
[root@greatsql]# docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                       NAMES
1bcd23c6f378        1130a28e310b        "/docker-entrypoin..."   2 minutes ago       Up 2 minutes        3306/tcp, 33060-33061/tcp   mgr3
9d12ab273d81        1130a28e310b        "/docker-entrypoin..."   2 minutes ago       Up 2 minutes        3306/tcp, 33060-33061/tcp   mgr2
56fd564a1789        1130a28e310b        "/docker-entrypoin..."   4 minutes ago       Up 4 minutes        3306/tcp, 33060-33061/tcp   mgr1
```

分别查看3个容器的IP地址：
```
[root@greatsql]# docker inspect mgr1 | grep IPAddress
            "SecondaryIPAddresses": null,
            "IPAddress": "172.18.0.2",
                    "IPAddress": "172.18.0.2",
```
第一个容器的IP地址是 *172.18.0.2*，另外两个容器分别是 *172.18.0.3*、*172.18.0.4*（递增关系）。因为我启动容器时指定的新创建的网络 *mgr-net*，所以是 *172.18.0.0/24* 网段。如果不指定新创建的网络，则默认应该是 *172.17.0.0/24* 网段，注意区别。

编辑三个容器下的 `/etc/hosts` 文件，加入所有节点的hostname配置：
```
172.18.0.2	mgr1
172.18.0.3	mgr2
172.18.0.4	mgr3
```
**提醒**：docker容器重启后，容器里的 /etc/hosts 文件内容会重置，所以建议用映射volumes的方式挂进来。

在宿主机上编辑好一个文件 */data/docker/hosts*：
```
[root@greatsql]# cat /data/docker/hosts

127.0.0.1 localhost.localdomain localhost
127.0.0.1 localhost4.localdomain4 localhost4

::1 localhost.localdomain localhost
::1 localhost6.localdomain6 localhost6

172.18.0.2	mgr1
172.18.0.3	mgr2
172.18.0.4	mgr3
```

在创建docker容器时映射挂载到容器的 */etc/hosts* 文件：
```
[root@greatsql]# docker run -d \
...
-v /data/docker/hosts:/etc/hosts \
...
greatsql/greatsql
```

也可以在创建容器时，直接用 `--add-host` 指定，例如：
```
[root@greatsql]# docker run -d \
...
--add-host "mgr1:172.18.0.2" --add-host "mgr2:172.18.0.3" --add-host "mgr3:172.18.0.4"\
...
greatsql/greatsql
```

### 3.3 初始化MGR集群
接下来准备初始化MGR集群。

选择第一个容器 **mgr1** 作为 **PRIMARY节点**，设置该容器的MGR的引导，然后启动MGR服务：
```
[root@greatsql]# docker exec -it mgr1 /bin/bash
[root@mgr1 ~]# mysql -S/data/GreatSQL/mysql.sock
...
#设置本节点为MGR引导启动节点，【注意】其他节点无需执行本操作
SET GLOBAL group_replication_bootstrap_group=ON;

#启动MGR服务
START GROUP_REPLICATION;

#启动完MGR服务后，关闭引导参数
SET GLOBAL group_replication_bootstrap_group=OFF;
```
因为在创建容器时已经完成了创建账户及授权等操作，所以可以直接启动MGR服务。如果在创建容器时未指定 `-e MYSQL_INIT_MGR=1` 选项，则还需要手动执行下面的命令创建账户，授权，并创建MGR复制通道：
```
SET SQL_LOG_BIN=0;
CREATE USER repl IDENTIFIED with mysql_native_password BY 'repl4MGR';
GRANT REPLICATION SLAVE, BACKUP_ADMIN ON *.* TO repl;
CHANGE MASTER TO MASTER_USER='repl', MASTER_PASSWORD='repl4MGR' FOR CHANNEL 'group_replication_recovery';
```

### 3.4 启动MGR服务
在另外的两个docker容器里，记住不要设置 `group_replication_bootstrap_group=ON`，直接启动 MGR服务即可。查看所有节点都启动后的MGR服务状态：
```
[root@GreatSQL][(none)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 63b55594-da80-11eb-94bf-0242ac120003 | mgr2        |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | 6d33eb83-da80-11eb-91ed-0242ac120004 | mgr3        |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | 7b1e33b1-da7f-11eb-8157-0242ac120002 | mgr1        |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
```

在这个阶段，MGR服务无法启动常见原因有：
- 没有在 /etc/hosts中正确设置各节点的 hostname，会提示无法连接远程主机。
- 利用docker创建的子网超过了RFC 1918定义的保留私有网络地址范围（A 类：10.0.0.0～10.255.255.255，B 类：172.16.0.0～172.31.255.255，C 类：192.168.0.0～192.168.255.255）。
- 除去在选择作为PRIMARY节点上设置 `group_replication_bootstrap_group=ON` 外，其他节点上也设置了，会造成启动一个新的PRIMARY节点。
- 各节点创建MGR账号后，会产生BINLOG，因此要执行 `SET SQL_LOG_BIN=0` 或者创建账号后再执行 `RESET MASTER`，否则会提示本地节点比远程节点的事务数更多，无法加入集群。

上述几种场景我都遇到过，可能还有其他更多情况，欢迎补充。

### 3.5 写入测试数据
这就构建完毕了，可以尝试在 **PRIMARY节点** 中创建库表并写入测试数据：
```
#提醒：从这里开始要重新启动binlog记录
[root@GreatSQL][(none)]> SET SQL_LOG_BIN=1;
[root@GreatSQL][(none)]> create database mymgr;
[root@GreatSQL][(none)]> use mymgr;
[root@GreatSQL][(mymgr)]> create table t1(id int primary key);
[root@GreatSQL][(mymgr)]> insert into t1 select rand()*10240;
[root@GreatSQL][mymgr]>select * from t1;
+------+
| id   |
+------+
| 3786 |
+------+
```

## 4、利用Docker-compose创建Docker容器
如果觉得手工管理麻烦，也可以选用 `docker-compose` ，它可以更方便的管理docker容器。

先用yum安装docker-compose，并确认版本号
```
[root@greatsql]# yum install -y docker-compose

[root@greatsql]# docker-compose --version
docker-compose version 1.18.0, build 8dd22a9
```

编辑docker-compose的配置文件，其实就是把创建docker容器的命令行参数固化到配置文件而已：
```
[root@greatsql]# mkdir -p /data/docker-compose
[root@greatsql]# vi /data/docker-compose/compose-mgr.yml
version: '3'

services:
  mgr1:
    image: greatsql/greatsql
    container_name: mgr1
    hostname: mgr1
    network_mode: bridge
    restart: unless-stopped
    environment:
      TZ: Asia/Shanghai
      MYSQL_ALLOW_EMPTY_PASSWORD: 1
      MYSQL_INIT_MGR: 1
      MYSQL_MGR_LOCAL: '172.17.0.2:33061'
      MYSQL_MGR_SEEDS: '172.17.0.2:33061,172.17.0.3:33061,172.17.0.4:33061'
    extra_hosts:
      - "mgr1:172.17.0.2"
      - "mgr2:172.17.0.3"
      - "mgr3:172.17.0.4"
  mgr2:
    image: greatsql/greatsql
    container_name: mgr2
    hostname: mgr2
    network_mode: bridge
    restart: unless-stopped
    depends_on:
      - "mgr1"
    environment:
      TZ: Asia/Shanghai
      MYSQL_ALLOW_EMPTY_PASSWORD: 1
      MYSQL_INIT_MGR: 1
      MYSQL_MGR_LOCAL: '172.17.0.3:33061'
      MYSQL_MGR_SEEDS: '172.17.0.2:33061,172.17.0.3:33061,172.17.0.4:33061'
    extra_hosts:
      - "mgr1:172.17.0.2"
      - "mgr2:172.17.0.3"
      - "mgr3:172.17.0.4"
  mgr3:
    image: greatsql/greatsql
    container_name: mgr3
    hostname: mgr3
    network_mode: bridge
    restart: unless-stopped
    depends_on:
      - "mgr2"
    environment:
      TZ: Asia/Shanghai
      MYSQL_ALLOW_EMPTY_PASSWORD: 1
      MYSQL_INIT_MGR: 1
      MYSQL_MGR_LOCAL: '172.17.0.4:33061'
      MYSQL_MGR_SEEDS: '172.17.0.2:33061,172.17.0.3:33061,172.17.0.4:33061'
    extra_hosts:
      - "mgr1:172.17.0.2"
      - "mgr2:172.17.0.3"
      - "mgr3:172.17.0.4"
```

启动三个实例：
```
[root@greatsql]# docker-compose -f /data/docker-compose/compose-mgr.yml up -d
Name   Command   State   Ports
Creating mgr1 ... done
Creating mgr2 ... done
Creating mgr3 ... done
Creating mgr2 ...
Creating mgr3 ...
```

查看运行状态：
```
[root@greatsql]# docker-compose -f /data/docker-compose/compose-mgr.yml up -d
Name             Command              State               Ports
----------------------------------------------------------------------------
mgr1   /docker-entrypoint.sh mysqld   Up      3306/tcp, 33060/tcp, 33061/tcp
mgr2   /docker-entrypoint.sh mysqld   Up      3306/tcp, 33060/tcp, 33061/tcp
mgr3   /docker-entrypoint.sh mysqld   Up      3306/tcp, 33060/tcp, 33061/tcp
```

进入被选为PRIMARY节点的容器mgr1，启动MGR服务：
```
[root@greatsql]# docker exec -it mgr1 bash
[root@mgr1 /]# mysql
...
[root@GreatSQL][(none)]> set global group_replication_bootstrap_group=ON;
[root@GreatSQL][(none)]> start group_replication;
```

进入其他SECONDARY节点的容器，直接启动MGR服务：
```
[root@greatsql]# docker exec -it mgr2 bash
[root@mgr2 /]# mysql
...
[root@GreatSQL][(none)]> start group_replication;
Query OK, 0 rows affected (2.76 sec)

#查看MGR服务状态
[root@GreatSQL][(none)]>select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | f0bd73d4-dbcb-11eb-99ba-0242ac110002 | mgr1        |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | f1010499-dbcb-11eb-9194-0242ac110003 | mgr2        |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
```
照旧，继续启动mgr3节点，一个三节点的MGR集群就完成了。

GreatSQL-Docker相关文档已经发布到 [https://gitee.com/GreatSQL/GreatSQL-Docker](https://gitee.com/GreatSQL/GreatSQL-Docker)，欢迎关注。

此外，GreatSQL Docker镜像文件也已发布到 [https://hub.docker.com/r/greatsql/greatsql](https://hub.docker.com/r/greatsql/greatsql) 欢迎下载体验。

## 5. 小结
本文介绍了如何在Docker下运行GreatSQL，以及构建MGR集群的方法，并且也介绍了利用docker-compose快速构建MGR集群的方法。现在生产环境中利用容器乃至在K8S环境中运行MySQL的场景越来越多了，有兴趣的同学也可以自行构建Docker镜像包。

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