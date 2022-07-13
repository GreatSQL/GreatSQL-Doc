# 容器化安装
---

本文详细介绍如何在Docker中部署GreatSQL，并且构建一个MGR集群。

## 1. 安装Docker
直接用yum/dnf安装docker，非常省事
```
$ yum install -y docker
```

之后启动 docker 服务，并设置开机自启动
```
$ systemctl enable docker
$ systemctl start docker
```

## 2. 拉取GreatSQL镜像，并创建容器
### 2.1 拉取镜像
拉取GreatSQL官方镜像
```
$ docker pull greatsql/greatsql
docker pull greatsql/greatsql
Using default tag: latest
Trying to pull repository docker.io/greatsql/greatsql ...
latest: Pulling from docker.io/greatsql/greatsql
...
Digest: sha256:03969daaaaaeb0f51dde0c9e92ef327302607cdde3afbe5c2b071098000c52c1
Status: Downloaded newer image for greatsql/greatsql:latest
docker.io/greatsql/greatsql:latest
```

检查是否成功
```
$ docker images
REPOSITORY                    TAG                 IMAGE ID            CREATED             SIZE
docker.io/greatsql/greatsql   latest              a930afc72d88        8 weeks ago         923 MB
```

### 2.2 创建新容器
之后，就可以直接创建一个新的容器了，先用常规方式
```
$ docker run -d --name greatsql --hostname=greatsql -e MYSQL_ALLOW_EMPTY_PASSWORD=1 greatsql/greatsql
```

容器的命名和容器内主机名均为greatsql。

确认容器状态：
```
$ docker ps -a | grep greatsql
...
4f351e22cea9   greatsql/greatsql     "/docker-entrypoint.…"   About a minute ago   Up About a minute          3306/tcp, 33060-33061/tcp   greatsql
...
```
看到容器状态是Up的，表示已正常启动了。

### 2.3 容器管理

进入容器查看
```
$ docker exec -it greatsql /bin/bash
[root@greatsql /]# mysql
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 12
Server version: 8.0.25-16 GreatSQL (GPL), Release 16, Revision 8bb0e5af297
...
Server version:        8.0.25-16 GreatSQL (GPL), Release 16, Revision 8bb0e5af297
...

Threads: 2  Questions: 18  Slow queries: 0  Opens: 119  Flush tables: 3  Open tables: 36  Queries per second avg: 0.243
```

看到容器已经完成初始化，并且可以直接无密码登入。

## 3. 利用Docker-compose创建Docker容器并构建MGR集群

手工管理Docker比较麻烦，建议采用 `docker-compose` ，它可以更方便的管理docker容器。

先用yum安装docker-compose，并确认版本号
```
$ yum install -y docker-compose

$ docker-compose --version
docker-compose version 1.29.2, build 5becea4c
```

编辑一个yaml文件，准备部署包含仲裁节点的三节点MGR集群：
```
$ mkdir -p /data/docker-compose
$ cat /data/docker-compose/mgr-3nodes.yml
version: '2'

services:
  mgr2:
    image: greatsql/greatsql         #指定镜像
    container_name: mgr2    #设定容器名字
    hostname: mgr2          #设定容器中的主机名
    networks:               #指定容器使用哪个专用网络
      mgr_net:
        ipv4_address: 172.18.0.2    #设置容器使用固定IP地址，避免重启后IP变化
    restart: unless-stopped         #设定重启策略
    environment:                    #设置多个环境变量
      TZ: Asia/Shanghai             #时区
      MYSQL_ALLOW_EMPTY_PASSWORD: 1                 #允许root账户空密码
      MYSQL_INIT_MGR: 1                             #初始化MGR集群
      MYSQL_MGR_LOCAL: '172.18.0.2:33061'           #当前MGR节点的local_address
      MYSQL_MGR_SEEDS: '172.18.0.2:33061,172.18.0.3:33061,172.18.0.4:33061'     #MGR集群seeds
      MYSQL_MGR_START_AS_PRIMARY: 1                 #指定当前MGR节点为Primary角色
      MYSQL_MGR_ARBITRATOR: 0
      #MYSQL_MGR_VIEWID: "aaaaaaaa-bbbb-bbbb-aaaa-aaaaaaaaaaa1"
  mgr3:
    image: greatsql/greatsql
    container_name: mgr3
    hostname: mgr3
    networks:
      mgr_net:
        ipv4_address: 172.18.0.3
    restart: unless-stopped
    depends_on:
      - "mgr2"
    environment:
      TZ: Asia/Shanghai
      MYSQL_ALLOW_EMPTY_PASSWORD: 1
      MYSQL_INIT_MGR: 1
      MYSQL_MGR_LOCAL: '172.18.0.3:33061'
      MYSQL_MGR_SEEDS: '172.18.0.2:33061,172.18.0.3:33061,172.18.0.4:33061'
      MYSQL_MGR_START_AS_PRIMARY: 0
      MYSQL_MGR_ARBITRATOR: 0                       #既非Primary，也非Arbitrator，那么就是Secondary角色了
      #MYSQL_MGR_VIEWID: "aaaaaaaa-bbbb-bbbb-aaaa-aaaaaaaaaaa1"
  mgr4:
    image: greatsql/greatsql
    container_name: mgr4
    hostname: mgr4
    networks:
      mgr_net:
        ipv4_address: 172.18.0.4
    restart: unless-stopped
    depends_on:
      - "mgr3"
    environment:
      TZ: Asia/Shanghai
      MYSQL_ALLOW_EMPTY_PASSWORD: 1
      MYSQL_INIT_MGR: 1
      MYSQL_MGR_LOCAL: '172.18.0.4:33061'
      MYSQL_MGR_SEEDS: '172.18.0.2:33061,172.18.0.3:33061,172.18.0.4:33061'
      MYSQL_MGR_START_AS_PRIMARY: 0
      MYSQL_MGR_ARBITRATOR: 1                   #指定当前MGR节点为Arbitrator角色，此时不能同时指定其为Primary/Secondary角色
      #MYSQL_MGR_VIEWID: "aaaaaaaa-bbbb-bbbb-aaaa-aaaaaaaaaaa1"
networks:
  mgr_net:  #创建独立MGR专属网络
    ipam:
      config:
        - subnet: 172.18.0.0/24
```
关于GreatSQL容器启动选项说明，详见[GreatSQL For Docker文档](https://hub.docker.com/r/greatsql/greatsql)。

如果不想要仲裁节点，则可以修改最后一个节点的属性 `MYSQL_MGR_ARBITRATOR: 0` 就行了。

另外，利用 docker-compose 方式暂时无法构建多主模式的MGR集群，需要手动部署。

启动三个实例：
```
$ docker-compose -f /data/docker-compose/mgr-3nodes.yml up -d
Creating network "docker-compose_mgr_net" with the default driver
Creating mgr2 ... done
Creating mgr3 ... done
Creating mgr4 ... done
```

查看运行状态：
```
$ docker-compose -f /data/docker-compose/mgr-3nodes.yml up -d
Name             Command              State               Ports
----------------------------------------------------------------------------
mgr2   /docker-entrypoint.sh mysqld   Up      3306/tcp, 33060/tcp, 33061/tcp
mgr3   /docker-entrypoint.sh mysqld   Up      3306/tcp, 33060/tcp, 33061/tcp
mgr4   /docker-entrypoint.sh mysqld   Up      3306/tcp, 33060/tcp, 33061/tcp
```
容器刚创建完还需要过一小段时间才能完成GreatSQL的初始化以及MGR集群自动构建，视服务器性能不同而定，一般需要30秒至四分钟左右。

进入被选为PRIMARY节点的容器mgr2，查看MGR集群状态：
```
$ docker exec -it mgr2 bash
[root@mgr2 /]# mysql
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 30
Server version: 8.0.25-16 GreatSQL (GPL), Release 16, Revision 8bb0e5af297
...
Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

(Tue Jul 12 14:28:00 2022)[root@GreatSQL][(none)]>\s
--------------
mysql  Ver 8.0.25-16 for Linux on x86_64 (GreatSQL (GPL), Release 16, Revision 8bb0e5af297)
...
Uptime:            1 min 38 sec

Threads: 11  Questions: 52  Slow queries: 0  Opens: 145  Flush tables: 3  Open tables: 62  Queries per second avg: 0.530
--------------

(Tue Jul 12 14:28:05 2022)[root@GreatSQL][(none)]>select * from performance_schema.replication_group_members;
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
| group_replication_applier | 396465ad-01ab-11ed-9c1a-0242ac120002 | 172.18.0.2  |        3306 | ONLINE       | PRIMARY     | 8.0.25         |
| group_replication_applier | 3a4eabbd-01ab-11ed-a7ea-0242ac120003 | 172.18.0.3  |        3306 | ONLINE       | SECONDARY   | 8.0.25         |
| group_replication_applier | 3c707b56-01ab-11ed-969b-0242ac120004 | 172.18.0.4  |        3306 | ONLINE       | ARBITRATOR  | 8.0.25         |
+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+
3 rows in set (0.01 sec)
```
可以看到，包含仲裁节点的三节点MGR集群已自动构建完毕。

如果想在Docker环境下逐个节点手动构建MGR集群，可以参考这篇文档[在Docker中部署GreatSQL并构建MGR集群](/docs/install-greatsql-with-docker.md)。

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
