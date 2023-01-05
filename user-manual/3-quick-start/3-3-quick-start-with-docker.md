# 容器化安装
---

本文档主要介绍如何用Docker方式安装GreatSQL数据库，假定本次安装是在CentOS 8.x x86_64环境中安装，并且是以root用户身份执行安装操作。

## 环境准备

Docker安装GreatSQL与宿主机的操作系统无关，只要能够运行Docker的操作系统均可支持，比如Linux，Windows，macOS。在此之前，您需要先确认已经安装好Docker并能正常使用。

Docker是一个开源的应用容器引擎，基于Go语言并遵从Apache2.0协议开源。Docker可以让开发者打包他们的应用以及依赖包到一个轻量级、可移植的容器中，然后发布到任何流行的Linux机器上，也可以实现虚拟化。

GreatSQL的Docker镜像仓库主页：[https://hub.docker.com/repository/docker/greatsql/greatsql](https://hub.docker.com/repository/docker/greatsql/greatsql)。

## 安装步骤
1. 启动Docker服务
```
$ systemctl start docker
```

2. 搜索、拉取GreatSQL镜像
```
$ docker search greatsql
NAME                DESCRIPTION   STARS     OFFICIAL   AUTOMATED
greatsql/greatsql                 4

$ docker pull greatsql
Using default tag: latest
latest: Pulling from greatsql/greatsql
a1d0c7532777: Already exists
0689c7a54f49: Pull complete
...
Digest: sha256:03969daaaaaeb0f51dde0c9e92ef327302607cdde3afbe5c2b071098000c52c1
Status: Downloaded newer image for greatsql/greatsql:latest
docker.io/greatsql/greatsql:latest
```

3. 创建一个新容器，容器中会安装并启动GreatSQL数据库
```
$ docker run -d --name greatsql --hostname=greatsql -e MYSQL_ALLOW_EMPTY_PASSWORD=1 greatsql/greatsql

4f351e22cea990b177589970ac5374f4b3366d2c0f69e923475f82c51da4b934
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

4. 进入容器
```
$ docker exec -it greatsql bash
[root@greatsql /]# cd /data/GreatSQL/
[root@greatsql GreatSQL]# ls
'#ib_16384_0.dblwr'   binlog.000001   ca-key.pem        error.log     ibdata1       mysql.ibd         performance_schema   server-key.pem   undo_002
'#ib_16384_1.dblwr'   binlog.000002   ca.pem            ib_buffer_pool     ibtmp1           mysql.pid         private_key.pem      slow.log
'#innodb_temp'          binlog.000003   client-cert.pem   ib_logfile0     innodb_status.1   mysql.sock         public_key.pem      sys
 auto.cnf          binlog.index    client-key.pem    ib_logfile1     mysql           mysql.sock.lock   server-cert.pem      undo_001
```
可以看到，GreatSQL已经安装并初始化完毕。

在容器中登入GreatSQL数据库：
```
[root@greatsql GreatSQL]# mysql -uroot
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 8
...
Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

(Wed Jul  6 14:42:39 2022)[root@GreatSQL][(none)]>\s
--------------
...
Server version:        8.0.25-16 GreatSQL (GPL), Release 16, Revision 8bb0e5af297
...
Threads: 2  Questions: 6  Slow queries: 0  Opens: 119  Flush tables: 3  Open tables: 36  Queries per second avg: 0.017
```

至此，在Docker中安装GreatSQL数据库完成。


**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
