# 在CentOS环境下源码编译安装GreatSQL

## 写在前面
开始之前，请先了解 [GreatSQL Build Docker镜像](https://gitee.com/GreatSQL/GreatSQL-Docker/tree/master/GreatSQL-Build)，使用它可以实现自动化完成GreatSQL源码编译工作，本文则是全手工操作方式。

本次介绍如何利用Docker来将GreatSQL源码编译成二进制文件。

本文介绍的运行环境是CentOS 8：
```
[root@c8ci ~]# cat /etc/redhat-release
CentOS Linux release 8.3.2011

[root@c8ci ~]# uname -a
Linux c8ci 4.18.0-305.19.1.el8_4.x86_64 #1 SMP Wed Sep 15 15:39:39 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux
```

## 1、准备工作
### 1.1、配置yum源
开始编译之前，建议先配置好yum源，方便安装一些工具。

以阿里云主机为例，可以这样配置：
```shell
# 直接替换yum源文件，并替换部分资源
[root@c8ci ~]# curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-vault-8.5.2111.repo
[root@c8ci ~]# sed -i -e '/mirrors.cloud.aliyuncs.com/d' -e '/mirrors.aliyuncs.com/d' /etc/yum.repos.d/CentOS-Base.repo

# 删除其他无用的yum源文件
[root@c8ci ~]# rm -f /etc/yum.repos.d/CentOS-Linux-*

#替换完后，更新缓存
[root@c8ci ~]# yum clean all
[root@c8ci ~]# yum makecache
```
### 1.2、安装docker
安装docker，并启动docker进程。
```shell
[root@c8ci]# yum install -y docker
[root@c8ci]# systemctl start docker
```

### 1.3、构建docker镜像
用下面这份Dockerfile构建镜像，这里以CentOS 8为例：
```
FROM centos:8
ENV LANG en_US.utf8

LABEL maintainer="greatsql.cn" \
email="greatsql@greatdb.com" \
forum="https://greatsql.cn/forum.php" \
gitee="https://gitee.com/GreatSQL/GreatSQL-Docker"

ARG MYSQL_UID=3306 \
MYSQL_USER=mysql \
OPT_DIR=/opt \
BOOST_SRC_DOWNLOAD_URL="https://boostorg.jfrog.io/artifactory/main/release/1.77.0/source" \
GREATSQL_BUILD_DOWNLOAD_URL="https://gitee.com/GreatSQL/GreatSQL-Docker/raw/master/GreatSQL-Build" \
GREATSQL_SRC_DOWNLOAD_URL="https://product.greatdb.com/GreatSQL-8.0.32-25" \
GREATSQL_MAKESH="greatsql-automake.sh" \
ENTRYPOINT="docker-entrypoint.sh" \
GREATSQL="greatsql-8.0.32-25.tar.xz" \
PATCHELF="patchelf-0.14.5" \
BOOST="boost_1_77_0.tar.gz" \
RPCGEN="rpcgen-1.3.1-4.el8.x86_64.rpm" \
DEPS="autoconf automake binutils bison cmake cyrus-sasl-devel cyrus-sasl-scram gcc-c++ \
gcc-toolset-11 gcc-toolset-11-annobin-plugin-gcc jemalloc jemalloc-devel krb5-devel libaio-devel \
libcurl-devel libtirpc-devel libudev-devel m4 make ncurses-devel numactl-devel openldap-devel \
openssl openssl-devel pam-devel readline-devel zlib-devel wget"

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f /lib/systemd/system/multi-user.target.wants/*;\
rm -f /etc/systemd/system/*.wants/*;\
rm -f /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*;\
rm -f /lib/systemd/system/anaconda.target.wants/*; \
rm -f /etc/yum.repos.d/CentOS-Linux-* ; \
curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-vault-8.5.2111.repo > /dev/null 2>&1 && \
sed -i -e '/mirrors.cloud.aliyuncs.com/d' -e '/mirrors.aliyuncs.com/d' /etc/yum.repos.d/CentOS-Base.repo > /dev/null 2>&1 && \
rm -f /etc/yum.repos.d/CentOS-Linux-* ; \
dnf clean all > /dev/null 2>&1 && \
dnf makecache > /dev/null 2>&1 && \
dnf update -y > /dev/null 2>&1 && \
rm -f /etc/yum.repos.d/CentOS-Linux-* ; \
dnf install -y epel-release > /dev/null 2>&1 && \
dnf install -y ${DEPS} > /dev/null 2>&1 && \
source /opt/rh/gcc-toolset-11/enable > /dev/null 2>&1 && \
echo 'source /opt/rh/gcc-toolset-11/enable' >> /root/.bash_profile; \
/usr/sbin/groupadd -g ${MYSQL_UID} ${MYSQL_USER} && \
/usr/sbin/useradd -u ${MYSQL_UID} -g ${MYSQL_UID} -s /sbin/nologin ${MYSQL_USER} && \
dnf install -y ${GREATSQL_BUILD_DOWNLOAD_URL}/${RPCGEN} > /dev/null 2>&1 && \
curl -o ${OPT_DIR}/${GREATSQL_MAKESH} ${GREATSQL_BUILD_DOWNLOAD_URL}/${GREATSQL_MAKESH} > /dev/null 2>&1 && \
curl -o /${ENTRYPOINT} ${GREATSQL_BUILD_DOWNLOAD_URL}/${ENTRYPOINT} > /dev/null 2>&1 && \
chmod +x ${OPT_DIR}/${GREATSQL_MAKESH} /${ENTRYPOINT} > /dev/null 2>&1 && \
curl -o ${OPT_DIR}/${PATCHELF}.tar.gz ${GREATSQL_BUILD_DOWNLOAD_URL}/${PATCHELF}.tar.gz > /dev/null 2>&1 && \
tar xf ${OPT_DIR}/${PATCHELF}.tar.gz -C ${OPT_DIR} > /dev/null 2>&1 && \
wget -c -O ${OPT_DIR}/${BOOST} ${BOOST_SRC_DOWNLOAD_URL}/${BOOST} > /dev/null 2>&1 && \
tar xf ${OPT_DIR}/${BOOST} -C /opt > /dev/null 2>&1 && \
curl -o ${OPT_DIR}/${GREATSQL} ${GREATSQL_SRC_DOWNLOAD_URL}/${GREATSQL} > /dev/null 2>&1 && \
tar xf ${OPT_DIR}/${GREATSQL} -C /opt > /dev/null 2>&1 && \
chown -R ${MYSQL_USER}:${MYSQL_USER} ${OPT_DIR} > /dev/null 2>&1 && \
chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["bash"]
```

开始构建docker镜像
```shell
[root@c8ci ~]# docker build -t greatsql/greatsql_build .
```

创建一个新Docker容器，即可自动完成GreatSQL源码编译工作：
```shell
[root@c8ci ~]# docker run -itd --name greatsql_build --hostname=greatsql_build greatsql/greatsql_build bash
```

查看自动编译进展
```shell
[root@c8ci ~]# docker logs greatsql_build

1. compile patchelf
2. entering greatsql automake
3. greatsql automake completed
drwxrwxr-x 13 mysql mysql       293 Feb 18 08:29 GreatSQL-8.0.32-25-centos-glibc2.28-x86_64
/opt/GreatSQL-8.0.32-25-centos-glibc2.28-x86_64/bin/mysqld  Ver 8.0.32-25 for Linux on x86_64 (GreatSQL, Release 25, Revision 79f57097e3f)
4. entering /bin/bash
```
这就自动完成GreatSQL源码编译工作了。

如果需要自定义编译参数，可以下载 `greatsql-automake.sh` 脚本自行修改，然后删除 `Dockerfile`第50行附近，在最后改成 `COPY` 方式，把在本地修改后的文件拷贝到Docker容器中，类似下面这样：
```
FROM centos:8
ENV LANG en_US.utf8

...
dnf install -y ${GREATSQL_BUILD_DOWNLOAD_URL}/${RPCGEN} > /dev/null 2>&1 && \
curl -o /${ENTRYPOINT} ${GREATSQL_BUILD_DOWNLOAD_URL}/${ENTRYPOINT} > /dev/null 2>&1 && \
...
chmod +x /docker-entrypoint.sh

#删除curl下载greatsql-automake.sh脚本工作，改成COPY
COPY ${GREATSQL_MAKESH} ${OPT_DIR}

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["bash"]
```

## 延伸阅读
- [玩转MySQL 8.0源码编译](https://mp.weixin.qq.com/s/Lrx-YYYWtHHaxLfY_UZ8GQ)
- [将GreatSQL添加到系统systemd服务](https://mp.weixin.qq.com/s/tSA-DrWT13GN45Csq2tQoA)
- [利用GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/gLaLybt46PqXlV4qWFfyng)
- [InnoDB Cluster+GreatSQL部署MGR集群](https://mp.weixin.qq.com/s/1QUt-rK_5L_UnaLClyve1w)
- [在Docker中部署GreatSQL并构建MGR集群](https://mp.weixin.qq.com/s/CfrYEQD54EXD9mLJJPGs-A)

全文完。

Enjoy GreatSQL :)
