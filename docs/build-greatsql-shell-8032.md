# MySQL Shell 8.0.32 for GreatSQL编译二进制包

> 构建MySQL Shell 8.0.32 for GreatSQL

## 0. 写在前面
之前已经写过一篇前传 [MySQL Shell 8.0.32 for GreatSQL编译安装](https://mp.weixin.qq.com/s/TzR-Szitdd2ocOqwJaaqEQ)，最近再次编译MySQL Shell二进制包时，发现了一些新问题，因此重新整理更新本文档。

## 1. 几处新问题

这次编译MySQL Shell发现几个新问题，下面一一列举。

1. MySQL Shell要求配套的antlr4版本必须是4.10.0，配套的protobuf必须是3.19.4，其他版本都不行。

2. 部分包需要科学上网才能下载，有些环境下就没那么方便了，因此我都下载到本地并打包好了。

3. 在编译antlr4时还要再下载googletest依赖包，这个下载地址也是要科学上网的，在内网环境中会失败，因此我antlr4源码包微调了下，把googletest依赖包也打进去了，也可以通过微调代码略过该步骤，这样就可以避免编译问题。

针对这些情况，为了方便社区用户，我直接将整个二进制包编译工作打包成Docker镜像，有需要的直接拉取镜像创建容器，只需耐心等上几分钟即可得到MySQL Shell for GreatSQL二进制包了。

使用方法很简单，类似下面这样即可：
```
# 前面略过Docker的安装过程
# 直接拉取镜像并创建新容器
$ docker run -itd --hostname greatsqlsh --name greatsqlsh greatsql/greatsql_shell_build bash

# 查看容器日志，大概要等几分钟才能编译完成，取决于服务器性能
# 如果看到类似下面的结果，就表明二进制包已编译完成
$ docker logs greatsqlsh | tail
1. extracting tarballs
2. compiling antlr4
3. compiling antlr4
4. compiling rpcsvc-proto
5. compiling protobuf
6. compiling greatsql shell
/opt/greatsql-shell-8.0.32-25-centos-glibc2.28-x86_64/bin/mysqlsh   Ver 8.0.32 for Linux on x86_64 - for MySQL 8.0.32 (Source distribution)
7. MySQL Shell 8.0.32-25 for GreatSQL build completed! TARBALL is:
-rw-r--r-- 1 root root 20343832 Jan 20 21:41 greatsql-shell-8.0.32-25-centos-glibc2.28-x86_64.tar.xz
```

接下来回退到宿主机，将容器中的二进制包拷贝出来
```
$ docker cp greatsqlsh:/opt/greatsql-shell-8.0.32-25-centos-glibc2.28-x86_64.tar.gz /usr/local/
```
然后解压缩，就可以在宿主机环境下使用了。

说完用Docker容器构建二进制包的方法，再说下手动编译全过程，有兴趣的同学也可以跟着自己动手做一遍，增加体感。

## 2. 手动编译过程

### 2.1 准备Docker环境
参考编译环境要求参考 [GreatSQL-Shell Dockerfile](https://gitee.com/GreatSQL/GreatSQL-Shell-Docker/blob/master/Dockerfile) ，构建好一个Docker镜像环境，基本上照着做就行，这里不赘述。

### 2.2 下载源码包

先下载准备好下列几个源码包：

- antlr4-4.10.0.tar.gz, [https://github.com/antlr/antlr4/archive/refs/tags/4.10.tar.gz](https://github.com/antlr/antlr4/archive/refs/tags/4.10.tar.gz)
- boost_1_77_0.tar.gz, [https://boostorg.jfrog.io/artifactory/main/release/1.77.0/source/boost_1_77_0.tar.gz](https://boostorg.jfrog.io/artifactory/main/release/1.77.0/source/boost_1_77_0.tar.gz)
- mysql-8.0.32.tar.gz, [https://downloads.mysql.com/archives/get/p/23/file/mysql-8.0.32.tar.gz](https://downloads.mysql.com/archives/get/p/23/file/mysql-8.0.32.tar.gz)
- mysql-shell-8.0.32-src.tar.gz, [https://downloads.mysql.com/archives/get/p/43/file/mysql-shell-8.0.32-src.tar.gz](https://downloads.mysql.com/archives/get/p/43/file/mysql-shell-8.0.32-src.tar.gz)
- patchelf-0.14.5.tar.gz, [https://github.com/NixOS/patchelf/releases/download/0.14.5/patchelf-0.14.5.tar.gz](https://github.com/NixOS/patchelf/releases/download/0.14.5/patchelf-0.14.5.tar.gz)
- protobuf-all-3.19.4.tar.gz, [https://github.com/protocolbuffers/protobuf/releases/download/v3.19.4/protobuf-all-3.19.4.tar.gz](https://github.com/protocolbuffers/protobuf/releases/download/v3.19.4/protobuf-all-3.19.4.tar.gz)
- rpcsvc-proto-1.4.tar.gz, [https://github.com/thkukuk/rpcsvc-proto/releases/download/v1.4/rpcsvc-proto-1.4.tar.gz](https://github.com/thkukuk/rpcsvc-proto/releases/download/v1.4/rpcsvc-proto-1.4.tar.gz)

下载完后都放在 `/opt/` 目录下，并解压缩。

### 2.3 修改MySQL Shell源码包
打开链接：[https://gitee.com/GreatSQL/GreatSQL-Shell-Docker/blob/master/mysqlsh-for-greatsql-8.0.32.patch](https://gitee.com/GreatSQL/GreatSQL-Shell-Docker/blob/master/mysqlsh-for-greatsql-8.0.32.patch)，下载GreatSQL补丁包文件 **mysqlsh-for-greatsql-8.0.32.patch**。

为了让MySQL Shell支持GreatSQL仲裁节点（**ARBITRATOR**）特性，需要打上补丁包：
```
$ cd /opt/mysql-shell-8.0.32-src
$ patch -p1 -f < /opt/mysqlsh-for-greatsql-8.0.32.patch

patching file mysqlshdk/libs/mysql/group_replication.cc
patching file mysqlshdk/libs/mysql/group_replication.h
```

### 2.4 编译相关软件包
#### 1.43.1 antlr4-4.10
编译antlr4：

```
$ cd /opt/antlr4-4.10/runtime/Cpp/
$ mkdir bld && cd bld
$ cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local/antlr4 && make -j16 && make -j16 install
```

如果你的网络环境无法直接从github上下载二进制包，则先自行下载二进制包 [https://github.com/google/googletest/archive/e2239ee6043f73722e7aa812a459f54a28552929.zip](https://github.com/google/googletest/archive/e2239ee6043f73722e7aa812a459f54a28552929.zip)，并放到antlr4代码包中相应位置，再修改antlr4代码，略过下载步骤，详见下面的做法：

```
$ cd /opt/antlr4-4.10/runtime/Cpp/
# 新建目录，并将下载的googletest压缩包放在该目录下
$ mkdir -p bld/_deps/googletest-subbuild/googletest-populate-prefix/src/
$ mv PATH/e2239ee6043f73722e7aa812a459f54a28552929.zip bld/_deps/googletest-subbuild/googletest-populate-prefix/src/

# 修改下面文件，注释掉第一行
$ vim runtime/CMakeLists.txt
#option(ANTLR_BUILD_CPP_TESTS "Build C++ tests." ON)
```
之后就可以用上面的方法进行编译，而不会在下载二进制包环节卡住不动。

#### 2.4.2 patchelf-0.14.5
```
$ cd /opt/patchelf-0.14.5
$ ./bootstrap.sh && ./configure && make -j16 && make -j16 install
```

#### 2.4.3 protobuf-3.19.4
```
$ cd /opt/protobuf-3.19.4
$ ./configure && make -j16 && make -j16 install
```

#### 2.4.4 rpcsvc-proto-1.4
```
$ cd /opt/rpcsvc-proto-1.4
$ ./configure && make -j16 && make -j16 install
```

### 3. 编译MySQL Shell
#### 3.1 编译MySQL 8.0.32
在MySQL 8.0.32源码目录中，编译生成MySQL客户端相关依赖库，这是编译MySQL Shell之前要先做的事：
```
$ cd /opt/mysql-8.0.32
$ mkdir bld && cd bld
$ cmake .. -DBOOST_INCLUDE_DIR=/opt/boost_1_77_0 \
-DLOCAL_BOOST_DIR=/opt/boost_1_77_0 \
-DWITH_SSL=system && \
cmake --build . --target mysqlclient -- -j16; \
cmake --build . --target mysqlxclient -- -j16
```

#### 3.2 编译MySQL Shell 8.0.32 for GreatSQL
编译完MySQL 8.0.32后，切换到MySQL Shell源码目录下，准备继续编译：

```
$ cd /opt/mysql-shell-8.0.32-src/
$ mkdir bld && cd bld
$ cmake .. \
-DCMAKE_INSTALL_PREFIX=/usr/local/greatsql-shell-8.0.32-25-Linux-glibc2.28-x86_64 \
-DMYSQL_SOURCE_DIR=/opt/mysql-8.0.32 \
-DMYSQL_BUILD_DIR=/opt/mysql-8.0.32/bld/ \
-DHAVE_PYTHON=1 \
-DWITH_PROTOBUF=bundled \
-DBUILD_SOURCE_PACKAGE=0 \
-DBUNDLED_ANTLR_DIR=/usr/local/antlr4/ \
-DPYTHON_LIBRARIES=/usr/lib64/python3.8 -DPYTHON_INCLUDE_DIRS=/usr/include/python3.8/ \
&& make && make install
```

编译完成后，会把二进制文件安装到  `/usr/local/greatsql-shell-8.0.32-25-Linux-glibc2.28-x86_64` 目录下。

#### 3.3 运行测试
运行 `mysqlsh`测试前，还要先将`libprotobuf.so`动态库文件拷贝放到MySQL Shell目录下，再运行测试：
```
$ cp /usr/local/lib/libprotobuf.so.30 /usr/local/greatsql-shell-8.0.32-25-Linux-glibc2.28-x86_64/lib/mysqlsh/
$ /usr/local/greatsql-shell-8.0.32-25-Linux-glibc2.28-x86_64/bin/mysqlsh
MySQL Shell 8.0.32
...
Type '\help' or '\?' for help; '\quit' to exit.
 MySQL  Py > \q
Bye!
```

好了，开始感受GreatSQL 8.0.32-25新版本特性，以及MGR仲裁节点的魅力吧 O(∩_∩)O哈哈~

## 延伸阅读
- [MySQL Shell 8.0.32 for GreatSQL编译安装](https://mp.weixin.qq.com/s/TzR-Szitdd2ocOqwJaaqEQ)
- [GreatSQL 8.0.32-25来了](https://mp.weixin.qq.com/s/HsqG4K8lV6QwW0XOJsIYGA)
- [图文结合丨玩转MySQL Shell for GreatSQL](https://mp.weixin.qq.com/s/9VQKLxGASbnA1qG39ZIzig)
- [**利用MySQL Shell安装部署MGR集群**](https://mp.weixin.qq.com/s/51ESDPgeuXqsgib6wb87iQ)
- [在CentOS环境下编译GreatSQL RPM包](https://mp.weixin.qq.com/s/IBliENob9nJ594PuAamL9A)

本文完。

Enjoy GreatSQL :)

