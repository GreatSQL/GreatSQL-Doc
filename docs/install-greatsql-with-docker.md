# Deploy GreatSQL and build MGR cluster in Docker

In this article we will introduce how to deploy GreatSQL and build an MGR cluster in Docker.

Install and run GreatSQL in CentOS 7.9:
```
[root@greatsql]# cat /etc/redhat-release
CentOS Linux release 7.9.2009 (Core)

[root@greatsql]# uname -a
Linux GreatSQL 3.10.0-1160.11.1.el7.x86_64 #1 SMP Fri Dec 18 16:34:56 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
```

## 1. Install Docker
Install docker directly with yum
```
[root@greatsql]# yum install -y docker
```

Then start the docker service, and set the boot to start automatically
```
[root@greatsql]# systemctl enable docker
[root@greatsql]# systemctl start docker
```

## 2. Pull the GreatSQL image and create a container
### 2.1 Pull Mirror
Pull the GreatSQL image
```
[root@greatsql]# docker pull greatsql/greatsql
docker pull greatsql/greatsql
Using default tag: latest
Trying to pull repository docker.io/greatsql/greatsql ...
latest: Pulling from docker.io/greatsql/greatsql
...
Digest: sha256:63eff1b099a75bb4e96b2c5bc7144889f6b3634a6163b56642a71a189183966c
Status: Downloaded newer image for docker.io/greatsql/greatsql:latest
```

Check if it is successful
```
[root@greatsql]# docker images
REPOSITORY TAG IMAGE ID CREATED SIZE
docker.io/greatsql/greatsql latest d1963ef0c403 3 days ago 582 MB
```

### 2.2 Create a new container
After that, you can create a new container directly, first in the usual way
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
greatsql/greatsql
```

Several variables are explained as follows

| Parameters | Required/Optional | Default Value | Explanation |
|---|---|---|---|
|-d| Required | None | run as a daemon |
| --name mgr1| Optional | Randomly generated | Specify the container name, which is convenient for later calling |
| --hostname mgr1| Optional | Container ID | Specify the hostname in the container, otherwise the container ID will be used as the hostname |
| -p 3306:3306| Optional | None | Specify the port number to be exposed by the container, which is convenient for remote connection via TCP |
| -e MYSQL_ALLOW_EMPTY_PASSWORD=1| Required | None | Allow root to use an empty password, you can also specify a password, or use a random password, as described below |
| -e MYSQL_IBP=1G| Optional| 128M| Set the value of innodb_buffer_pool_size |
|-e MYSQL_MGR_NAME='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1'|Optional|aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1|Set MGR cluster name |
|-e MYSQL_MGR_LOCAL='172.17.0.2:33061'|Optional| 172.17.0.2:33061|Set MGR local node IP+PORT|
|-e MYSQL_MGR_SEEDS='172.17.0.2:33061,<br/>172.17.0.3:33061,<br/>172.17.0.4:33061'|Optional| 172.17.0.2:33061,172.17.0.3:33061|Set MGR List of nodes in the cluster |
|-e MYSQL_INIT_MGR=1|Optional|0|Initialize MGR automatically|
|-e MYSQL_MGR_USER='repl'|Optional|repl|Set user account name for MGR|
|-e MYSQL_MGR_USER_PWD='repl'|Optional| repl4MGR |Set user password for MGR|

`greatsql/greatsql` is the name of the image, or it can be specified as the ID of the image, for example, `d1963ef0c403`.

If you don't want the root account to use empty password, you can replace the `MYSQL_ALLOW_EMPTY_PASSWORD=1` option with `MYSQL_ROOT_PASSWORD='GreatSQL3#)^'` or specify a random password `MYSQL_RANDOM_ROOT_PASSWORD=1`.

When the option `MYSQL_INIT_MGR=1` is enabled, the account required by MGR is automatically created, and `CHANGE MASTER TO` is executed to specify the MGR replication channel. If `MYSQL_MGR_USER` or `MYSQL_MGR_USER_PWD` are not specified at the same time, the respective default values will be used to create the MGR account.

A new container is created, and GreatSQL will be initialized and started automatically.

### 2.3 Container Management
Check the status of the container
```
[root@greatsql]# docker ps -a
CONTAINER ID IMAGE COMMAND CREATED STATUS PORTS NAMES
2e277c852f52 d1963ef0c403 "/docker-entrypoin..." 4 minutes ago Up 12 minutes 3306/tcp, 33060-33061/tcp mgr1
```
The container is Up, it means that it has started normally.

Enter the container
```
[root@greatsql]# docker exec -it mgr1 /bin/bash
[root@mgr1 ~]# mysqladmin ver
mysqladmin Ver 8.0.23-14 for Linux on x86_64 (GreatSQL (GPL), Release 14, Revision)
...
Server version 8.0.23-14
Protocol version 10
Connection Localhost via UNIX socket
UNIX socket /data/GreatSQL/mysql.sock
Uptime: 11 min 19 sec

Threads: 2 Questions: 2 Slow queries: 0 Opens: 120 Flush tables: 3 Open tables: 36 Queries per second avg: 0.002
```

The container has been initialized, and you can login directly without a password.

Check MGR user account
```
[root@GreatSQL][(none)]> show grants for repl;
+----------------------------------------------+
| Grants for repl@% |
+----------------------------------------------+
| GRANT REPLICATION SLAVE ON *.* TO `repl`@`%` |
| GRANT BACKUP_ADMIN ON *.* TO `repl`@`%` |
+----------------------------------------------+

[root@GreatSQL][none]> select * from performance_schema.replication_group_members;
+---------------------------+-----------+--------- ----+-------------+--------------+-------------+-- --------------+
| CHANNEL_NAME | MEMBER_ID | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+-----------+--------- ----+-------------+--------------+-------------+-- --------------+
| group_replication_applier | | | NULL | OFFLINE | | |
+---------------------------+-----------+--------- ----+-------------+--------------+-------------+-- --------------+
```

## 3. Build MGR cluster
The docker container network communication between cross-hosts is a little troublesome. The MGR cluster composed of three docker containers is built in the same host for convenience.

### 3.1 Create a dedicated subnet
Create a network for the MGR cluster firstly:
```
[root@greatsql]# docker network create mgr-net

[root@greatsql]# docker network ls
NETWORK ID NAME DRIVER SCOPE
70c3ac08c7a9 bridge bridge local
3a480a3ec570 host host local
191d6d902b26 mgr-net bridge local
1e3e6267dcda none null local
```

Check the subnet:
```
[root@greatsql]# docker inspect mgr-net
[
    {
        "Name": "mgr-net",
...
                    "Subnet": "172.18.0.0/16", <-- network segment
                    "Gateway": "172.18.0.1" <-- Gateway
...
```

### 3.2 Create three new containers
Start three docker containers separately:
```
[root@greatsql]# docker run -d \
--name mgr1 --hostname=mgr1 --net=mgr-net \
-e MYSQL_ALLOW_EMPTY_PASSWORD=1 \
-e MYSQL_MGR_LOCAL='172.18.0.2:33061' \
-e MYSQL_MGR_SEEDS='172.18.0.2:33061,172.18.0.3:33061,172.18.0.4:33061' \
-e MYSQL_INIT_MGR=1 \
greatsql/greatsql
```

In the following two containers, only the mgr1 in the --name and --hostname options are changed to mgr2 and mgr3, and the IP address of the `-e MYSQL_MGR_LOCAL='172.18.0.2:33061'` option is incremented, for example, `- e MYSQL_MGR_LOCAL='172.18.0.3:33061'`.

Check the status of the container:
```
[root@greatsql]# docker ps -a
CONTAINER ID IMAGE COMMAND CREATED STATUS PORTS NAMES
1bcd23c6f378 d1963ef0c403 "/docker-entrypoin..." 2 minutes ago Up 2 minutes 3306/tcp, 33060-33061/tcp mgr3
9d12ab273d81 d1963ef0c403 "/docker-entrypoin..." 2 minutes ago Up 2 minutes 3306/tcp, 33060-33061/tcp mgr2
56fd564a1789 d1963ef0c403 "/docker-entrypoin..." 4 minutes ago Up 4 minutes 3306/tcp, 33060-33061/tcp mgr1
```

Check the IP addresses of the three containers:
```
[root@greatsql]# docker inspect mgr1 | grep IPAddress
            "SecondaryIPAddresses": null,
            "IPAddress": "172.18.0.2",
                    "IPAddress": "172.18.0.2",
```

The IP address of the first container is *172.18.0.2*, and the other two containers are *172.18.0.3* and *172.18.0.4* (incremental relationship). Because I specified the newly created network *mgr-net* when I started the container, it is the *172.18.0.0/24* subnet. If you do not specify the newly created network, the default should be *172.17.0.0/24* subnet, pay attention to the difference.

Edit the `/etc/hosts` files under the three containers and add the hostname configuration of all nodes:
```
172.18.0.2 mgr1
172.18.0.3 mgr2
172.18.0.4 mgr3
```
**Reminder**: After the docker container is restarted, the contents of the /etc/hosts file in the container will be reset, so it is recommended to hang in by mapping volumes.

Edit a file */data/docker/hosts* on the host machine:
```
[root@greatsql]# cat /data/docker/hosts

127.0.0.1 localhost.localdomain localhost
127.0.0.1 localhost4.localdomain4 localhost4

::1 localhost.localdomain localhost
::1 localhost6.localdomain6 localhost6

172.18.0.2 mgr1
172.18.0.3 mgr2
172.18.0.4 mgr3
```

When creating a docker container, map the */etc/hosts* file mounted to the container:
```
[root@greatsql]# docker run -d \
...
-v /data/docker/hosts:/etc/hosts \
...
greatsql/greatsql
```

You can also specify it directly with `--add-host` when creating the container, for example:
```
[root@greatsql]# docker run -d \
...
--add-host "mgr1:172.18.0.2" --add-host "mgr2:172.18.0.3" --add-host "mgr3:172.18.0.4"\
...
greatsql/greatsql
```

### 3.3 Initialize the MGR cluster
Next, we are ready to initialize the MGR cluster.

The first container **mgr1** is selected as the **PRIMARY node**, set the bootstrap of the container's MGR, and then start the MGR service:
```
[root@greatsql]# docker exec -it mgr1 /bin/bash
[root@mgr1 ~]# mysql -S/data/GreatSQL/mysql.sock
...
#Set this node as the MGR boot node, [Note] Other nodes do not need to perform this operation
SET GLOBAL group_replication_bootstrap_group=ON;

#Start MGR service
START GROUP_REPLICATION;

#After starting the MGR service, turn off the boot parameters
SET GLOBAL group_replication_bootstrap_group=OFF;
```

Because user account and grants have been completed when the container is created, the MGR service can be started directly. If the `-e MYSQL_INIT_MGR=1` option is not specified when creating the container, you also need to manually execute the following commands to create an account, grants, and create an MGR replication channel:
```
SET SQL_LOG_BIN=0;
CREATE USER repl IDENTIFIED with mysql_native_password BY'repl4MGR';
GRANT REPLICATION SLAVE, BACKUP_ADMIN ON *.* TO repl;
CHANGE MASTER TO MASTER_USER='repl', MASTER_PASSWORD='repl4MGR' FOR CHANNEL'group_replication_recovery';
```

### 3.4 Start MGR service
In the other two docker containers, remember not to set `group_replication_bootstrap_group=ON`, just start the MGR service directly. Check the MGR service status after all nodes are started:
```
[root@GreatSQL][(none)]> select * from performance_schema.replication_group_members;
+---------------------------+--------------------- -----------------+-------------+-------------+---- ----------+-------------+----------------+
| CHANNEL_NAME | MEMBER_ID | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------- -----------------+-------------+-------------+---- ----------+-------------+----------------+
| group_replication_applier | 63b55594-da80-11eb-94bf-0242ac120003 | mgr2 | 3306 | ONLINE | SECONDARY | 8.0.23 |
| group_replication_applier | 6d33eb83-da80-11eb-91ed-0242ac120004 | mgr3 | 3306 | ONLINE | SECONDARY | 8.0.23 |
| group_replication_applier | 7b1e33b1-da7f-11eb-8157-0242ac120002 | mgr1 | 3306 | ONLINE | PRIMARY | 8.0.23 |
+---------------------------+--------------------- -----------------+-------------+-------------+---- ----------+-------------+----------------+
```

At this stage, the common reasons why the MGR service cannot be started are:
- If the hostname of each node is not correctly set in /etc/hosts, it will prompt that the remote host cannot be connected.
- The subnet created with docker exceeds the reserved private network address range defined by RFC 1918 (Type A: 10.0.0.0～10.255.255.255, Type B: 172.16.0.0～172.31.255.255, Type C: 192.168.0.0～192.168. 255.255).
- Except for setting `group_replication_bootstrap_group=ON` on the selected PRIMARY node, it is also set on other nodes, which will cause a new PRIMARY node to be started.
- After each node creates an user account, it will generate BINLOG, so execute `SET SQL_LOG_BIN=0` or execute `RESET MASTER` after user creating, otherwise it will prompt that the local node has more transactions than the remote node and cannot join the cluster.

I have encountered all the above scenarios, there may be more situations, welcome to add.

## 4. Use Docker-compose to create a Docker container
You can also use `docker-compose` to build MGR cluser, which can manage docker containers more conveniently.

First install docker-compose with yum
```
[root@greatsql]# yum install -y docker-compose

[root@greatsql]# docker-compose --version
docker-compose version 1.18.0, build 8dd22a9
```

Editing the docker-compose configuration file, set the options for creating the docker container:
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
      -"mgr1:172.17.0.2"
      -"mgr2:172.17.0.3"
      -"mgr3:172.17.0.4"
  mgr2:
    image: greatsql/greatsql
    container_name: mgr2
    hostname: mgr2
    network_mode: bridge
    restart: unless-stopped
    depends_on:
      -"mgr1"
    environment:
      TZ: Asia/Shanghai
      MYSQL_ALLOW_EMPTY_PASSWORD: 1
      MYSQL_INIT_MGR: 1
      MYSQL_MGR_LOCAL: '172.17.0.3:33061'
      MYSQL_MGR_SEEDS: '172.17.0.2:33061,172.17.0.3:33061,172.17.0.4:33061'
    extra_hosts:
      -"mgr1:172.17.0.2"
      -"mgr2:172.17.0.3"
      -"mgr3:172.17.0.4"
  mgr3:
    image: greatsql/greatsql
    container_name: mgr3
    hostname: mgr3
    network_mode: bridge
    restart: unless-stopped
    depends_on:
      -"mgr2"
    environment:
      TZ: Asia/Shanghai
      MYSQL_ALLOW_EMPTY_PASSWORD: 1
      MYSQL_INIT_MGR: 1
      MYSQL_MGR_LOCAL: '172.17.0.4:33061'
      MYSQL_MGR_SEEDS: '172.17.0.2:33061,172.17.0.3:33061,172.17.0.4:33061'
    extra_hosts:
      -"mgr1:172.17.0.2"
      -"mgr2:172.17.0.3"
      -"mgr3:172.17.0.4"
```

Start three instances:
```
[root@greatsql]# docker-compose -f /data/docker-compose/compose-mgr.yml up -d
Name Command State Ports
Creating mgr1 ... done
Creating mgr2 ... done
Creating mgr3 ... done
Creating mgr2 ...
Creating mgr3 ...
```

Check the running status:
```
[root@greatsql]# docker-compose -f /data/docker-compose/compose-mgr.yml up -d
Name Command State Ports
-------------------------------------------------- --------------------------
mgr1 /docker-entrypoint.sh mysqld Up 3306/tcp, 33060/tcp, 33061/tcp
mgr2 /docker-entrypoint.sh mysqld Up 3306/tcp, 33060/tcp, 33061/tcp
mgr3 /docker-entrypoint.sh mysqld Up 3306/tcp, 33060/tcp, 33061/tcp
```

Enter the container mgr1 selected as the PRIMARY node and start the MGR service:
```
[root@greatsql]# docker exec -it mgr1 bash
[root@mgr1 /]# mysql
...
[root@GreatSQL][(none)]> set global group_replication_bootstrap_group=ON;
[root@GreatSQL][(none)]> start group_replication;
```

Enter the container of other SECONDARY nodes and start the MGR service directly:
```
[root@greatsql]# docker exec -it mgr2 bash
[root@mgr2 /]# mysql
...
[root@GreatSQL][(none)]> start group_replication;
Query OK, 0 rows affected (2.76 sec)

#View MGR service status
[root@GreatSQL][(none)]>select * from performance_schema.replication_group_members;
+---------------------------+--------------------- -----------------+-------------+-------------+---- ----------+-------------+----------------+
| CHANNEL_NAME | MEMBER_ID | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------- -----------------+-------------+-------------+---- ----------+-------------+----------------+
| group_replication_applier | f0bd73d4-dbcb-11eb-99ba-0242ac110002 | mgr1 | 3306 | ONLINE | PRIMARY | 8.0.23 |
| group_replication_applier | f1010499-dbcb-11eb-9194-0242ac110003 | mgr2 | 3306 | ONLINE | SECONDARY | 8.0.23 |
+---------------------------+--------------------- -----------------+-------------+-------------+---- ----------+-------------+----------------+
```
As usual, continue to start the mgr3 node, and a three-node MGR cluster is complete.
