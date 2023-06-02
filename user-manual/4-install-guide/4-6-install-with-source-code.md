# 编译源码安装
---

本次介绍如何利用Docker来编译GreatSQL源码。

## 1. 下载GreatSQL源码及Docker压缩包

### 1.1 下载Docker编译环境压缩包

[戳此下载](https://product.greatdb.com/GreatSQL/greatsql_docker_build.tar.xz)GreatSQL Docker编译环境压缩包[greatsql_docker_build.tar.xz](https://product.greatdb.com/GreatSQL/greatsql_docker_build.tar.xz)。

将压缩包放在 `/opt/` 目录下：
```
$ cd /opt/
$ tar xf greatsql_docker_build.tar.xz
$ cd greatsql_docker_build
$ ls
Dockerfile  greatsql-automake.sh  greatsql-docker-build.sh  patchelf-0.12.tar.gz  rpcsvc-proto-1.4.tar.gz
```

下载 boost_1_73_0 源码包：
```
$ pwd
/opt/greatsql_docker_build
$ curl -o boost_1_73_0.tar.gz https://nchc.dl.sourceforge.net/project/boost/boost/1.73.0/boost_1_73_0.tar.gz
$ ls
boost_1_73_0.tar.gz  Dockerfile  greatsql-automake.sh  greatsql-docker-build.sh  patchelf-0.12.tar.gz  rpcsvc-proto-1.4.tar.gz
```

### 1.2 下载GreatSQL源码

[戳此下载](https://gitee.com/GreatSQL/GreatSQL/releases/)GreatSQL源码压缩包，解压缩后放在 `/opt` 目录下。

或者也可以直接用git下载，将源码放在 `/opt/` 目录下：
```
$ cd /opt/
$ git clone https://gitee.com/GreatSQL/GreatSQL.git
$ mv greatsql greatsql-8.0.25-16
```

## 2. 构建Docker编译环境

执行脚本 `greatsql_docker_build.sh` 开始构建Docker编译环境：
```
$ cd /opt/greatsql_docker_build
$ sh ./greatsql_docker_build.sh /opt/greatsql-8.0.25-16
```

执行脚本后面带的参数 `/opt/greatsql-8.0.25-16` 是指GreatSQL源码所在目录。
之后就会自动开始构建Docker环境了：
```
$ sh ./greatsql_docker_build.sh /opt/greatsql-8.0.25-16
Sending build context to Docker daemon  411.9MB
Step 1/14 : FROM centos
 ---> 5d0da3dc9764
Step 2/14 : ENV container docker
 ---> Using cache
 ---> 49a38409329a
...
Step 14/14 : COPY boost_1_73_0.tar.gz /opt/
 ---> 55a506d50850
Successfully built 55a506d50850
Successfully tagged greatsql_build_env:latest
Docker build success!you can run it:

docker run -d -v /opt/greatsql-8.0.25-16:/opt/greatsql-8.0.25-16 greatsql_build_env
```

## 3. 进入Docker容器编译GreatSQL

根据上面的提示，创建一个新容器用于编译GreatSQL：
```
$ docker run -d -v /opt/greatsql-8.0.25-16:/opt/greatsql-8.0.25-16 greatsql_build_env
cc6500484dad5c905f00167e274f833bb722eff83269a51a2eb058013aaccfb4
```

找到正确的容器ID，进入该容器，准备开始编译：
```
$ docker ps -a | grep greatsql_build
cc6500484dad   greatsql_build_env    "/usr/sbin/init"         2 minutes ago   Up 2 minutes                                           strange_borg

$ docker exec -it cc6500484dad bash
[root@cc6500484dad /]#
[root@cc6500484dad /]# cd /opt
[root@cc6500484dad opt]# ls
boost_1_73_0.tar.gz  greatsql-8.0.25-16  greatsql-automake.sh  rh
[root@cc6500484dad opt]# tar zxf boost_1_73_0.tar.gz
```

编辑 `/opt/greatsql_docker_build/greatsql-automake.sh` 脚本，确认其中文件目录、版本号等信息是否正确：
```
#!/bin/bash
MAJOR_VERSION=8
MINOR_VERSION=0
PATCH_VERSION=25
RELEASE=16
REVISION=8bb0e5af297
GLIBC=2.28
ARCH=x86_64
MYSQL=GreatSQL
PKG_NAME=${MYSQL}-${MAJOR_VERSION}.${MINOR_VERSION}.${PATCH_VERSION}-${RELEASE}-Linux-glibc${GLIBC}-${ARCH}
BASE_DIR=/usr/local/${PKG_NAME}
BOOST_VERSION=1_73_0
SOURCE_DIR=greatsql-8.0.25-16
...
```

确认都没问题的话，就可以执行该脚本开始编译源码了：
```
# 记得执行这步，切换到gcc 10编译环境下
$ source ~/.bash_profile
$ time sh /opt/greatsql_docker_build/greatsql-automake.sh

-- Running cmake version 3.20.2
-- Found Git: /usr/bin/git (found version "2.27.0")
CMake Deprecation Warning at cmake/cmake_policies.cmake:54 (CMAKE_POLICY):
  The OLD behavior for policy CMP0075 will be removed from a future version
  of CMake.
...
-- Up-to-date: /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/man/man8/mysqld.8
-- Up-to-date: /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/man/man1/mysqlrouter.1
-- Up-to-date: /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/man/man1/mysqlrouter_passwd.1
-- Up-to-date: /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64/man/man1/mysqlrouter_plugin_info.1
```

编译过程中如果没问题，就会在 `/usr/local` 目录下生成GreatSQL二进制安装文件，例如：
```
$ ls /usr/local/GreatSQL-8.0.25-16-Linux-glibc2.28-x86_64
bin    docs     lib      LICENSE.router  man                     mysql-test  README.md-test  run    support-files  var
cmake  include  LICENSE  LICENSE-test    mysqlrouter-log-rotate  README.md   README.router   share  usr
```
至此，GreatSQL二进制安装包就编译成功了，接下来可以参考文档[二进制包安装并构建MGR集群](./4-3-install-with-tarball.md)继续进行数据库的初始化，以及MGR集群构建等工作，这里不赘述。

## 4. 相关资源
`greatsql_docker_build` 最新版本详见：[https://gitee.com/GreatSQL/GreatSQL-Doc/tree/master/greatsql_docker_build](https://gitee.com/GreatSQL/GreatSQL-Doc/tree/master/greatsql_docker_build)。

**延伸阅读**
- [在Linux下源码编译安装GreatSQL](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/build-greatsql-with-source.md)
- [麒麟OS+龙芯环境编译GreatSQL](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/build-greatsql-with-source-under-kylin-and-loongson.md)
- [openEuler、龙蜥Anolis、统信UOS系统下编译GreatSQL二进制包](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/build-greatsql-under-openeuler-anolis-uos.md)

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
