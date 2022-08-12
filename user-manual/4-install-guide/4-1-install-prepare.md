# 安装准备
---

本文档描述安装 GreatSQL 之前需要先准备的运行环境说明。

GreatSQL 可以很好地部署和运行在 Intel 架构服务器环境、ARM 架构的服务器环境及主流虚拟化环境，并支持绝大多数的主流硬件网络。

GreatSQL 支持以下几种安装方式：
- RPM包
- 二进制包
- Docker
- Ansible
- 源码编译

支持X86和ARM、龙芯等多种CPU架构平台。

支持CentOS、Ubuntu、openEuler、麒麟等多种常见操作系统。

本章节文档若无特别说明，所有安装环境均是指 **CentOS 8.x x86_64 环境**。

## 1. 硬件环境

GreatSQL 支持部署和运行在 Intel x86_64 架构的 64 位通用硬件服务器平台或者 ARM 架构的硬件服务器平台。

对于开发、测试及生产环境的服务器硬件配置有以下要求和建议：

**开发及测试环境**

| 配置 | 要求 |
| --- | --- |
| CPU | 1 cores+ |
| 内存 | 1 GB+ |
| 磁盘 | 10 GB+ |
| 网络 | 百兆网络 |

**生产环境**

| 配置 | 要求 |
| --- | --- |
| CPU | 8 cores+ |
| 内存 | 8 GB+ |
| 磁盘 | 100 GB+ |
| 网络 | 千兆网络 |

## 2. 系统环境

GreatSQL 支持主流的 Linux 操作系统环境。

| Linux 操作系统    | 版本 |
| --- | --- |
| Red Hat Enterprise Linux    | 7.x 及以上的版本 |
| CentOS    | 7.x 及以上的版本 |
| Oracle Enterprise Linux    | 7.x 及以上的版本 |
| Ubuntu LTS    | 16.04 及以上的版本 |
| openEuler | 20.03 及以上的版本 |
| Kylin Linux | V10 及以上的版本 |

## 3. 挂载数据库专用分区
建议采用XFS文件系统的分区来存储 GreatSQL 数据库文件，其综合性能、可靠性、安全性、稳定性已经在大量线上场景中得到证实。

以 /dev/nvme0n1 数据盘为例，具体操作步骤如下：

1. **将整个分区都格式化为xfs文件系统**
```
$ mkfs.xfs -f -L /data /dev/nvme0n1
```

2. **修改 `/etc/fstab` 系统文件，增加数据库专用分区**
```
$ vim /etc/fstab
...
LABEL=/data /data    xfs     defaults,noatime,nodiratime,inode64 0 0
```
3. **创建 `/data` 目录，挂载分区**
```
$ mkdir -p /data && mount /data
```

4. **检查分区挂载结果**
```
$ mount | grep /data
...
/dev/nvme0n1 on /data type xfs (rw,noatime,nodiratime,attr2,inode64,logbufs=8,logbsize=32k,noquota)
```

## 4. 关闭防火墙及selinux

数据库服务器通常运行在内部网络，此外部署MGR时也需要对内网开放多个TCP端口，因此可以关闭防火墙及selinux设置。

**提醒：** 虽然数据部署在内部网络，但也要时刻警惕数据泄漏的风险，做好必要的安全防护措施。

1. **关闭防火墙服务**
```
$ systemctl stop firewalld ; systemctl disable firewalld
```

2. **关闭selinux**
```
$ setenforce 0
$ sed -i '/^SELINUX=/c'SELINUX=disabled /etc/selinux/config
```

## 5. 关闭swap

运行 GreatSQL 建议配置足够的物理内存。如果内存不足，不建议使用 swap 作为缓冲，因为这会降低性能。建议永久关闭系统 swap。
```
$ echo "vm.swappiness = 0">> /etc/sysctl.conf
$ swapoff -a && swapon -a
$ sysctl -p
```

## 6. 检查和配置操作系统优化参数

1. **修改数据库分区的 I/O Scheduler 设置为 noop / deadline**

先查看当前设置
```
$ cat /sys/block/nvme0n1/queue/scheduler
none
```
这样没问题，如果不是 noop 或 deadline，可以动手修改：
```
$ echo 'noop' > /sys/block/nvme0n1/queue/scheduler
```
这样修改后立即生效，无需重启。

2. **确认CPU性能模式设置**

先检查当前的设置模式
```
$ cpupower frequency-info --policy
analyzing CPU 0:
  current policy: frequency should be within 800 MHz and 4.80 GHz.
                  The governor "performance" may decide which speed to use
```
> **注意**
> 如果输出内容不是 The governor "performance" 而是 The governor "powersave" 的话，则要注意了。
> The governor "powersave" 表示 cpufreq 的节能策略使用 powersave，需要调整为 performance 策略。
> 如果是虚拟机或者云主机，则不需要调整，命令输出通常为 Unable to determine current policy。

3. **关闭透明大页**

建议关闭透明大页（Transparent Huge Pages / THP）。OLTP型数据库内存访问模式通常是稀疏的而非连续的。当高阶内存碎片化比较严重时，分配 THP 页面会出现较高的延迟，反而影响性能。

先检查当前设置：
```
$ cat /sys/kernel/mm/transparent_hugepage/enabled
always madvise [never]
```
如果输出结果不是 **never** 的话，则需要执行下面的命令关闭：
```
$ echo never > /sys/kernel/mm/transparent_hugepage/enabled
$ echo never > /sys/kernel/mm/transparent_hugepage/defrag
```

4. **优化内核参数**
建议调整优化下面几个内核参数：
```
$ echo "fs.file-max = 1000000" >> /etc/sysctl.conf
$ echo "net.core.somaxconn = 32768" >> /etc/sysctl.conf
$ echo "net.ipv4.tcp_tw_recycle = 0" >> /etc/sysctl.conf
$ echo "net.ipv4.tcp_syncookies = 0" >> /etc/sysctl.conf
$ echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf
$ sysctl -p
```

5. *修改mysql用户使用资源上限**

修改 `/etc/security/limits.conf` 系统文件，调高mysql系统账户的上限：
```
$ vim /etc/security/limits.conf
...
mysql           soft    nofile         65535
mysql           hard    nofile         65535
mysql           soft    stack          32768
mysql           hard    stack          32768
mysql           soft    nproc          65535
mysql           hard    nproc          65535
```

## 7. 其他

7.1、**配置正确的YUM源，并提前安装一些依赖包**

要确认YUM源可用，因为安装GreatSQL时还要先安装其他依赖包，通过YUM安装最省事。

如果需要配置YUM源，可以参考[这篇文档](https://developer.aliyun.com/mirror/centos)。

安装GreatSQL RPM包时，要先安装这些相关依赖包。
```
$ yum install -y pkg-config perl libaio-devel numactl-devel numactl-libs net-tools openssl openssl-devel jemalloc jemalloc-devel
```
如果有更多依赖包需要安装，请自行添加。

添加/修改系统文件 `/etc/sysconfig/mysql`：
```
LD_PRELOAD=/usr/lib64/libjemalloc.so
THP_SETTING=never
```
确认文件 `/usr/lib64/libjemalloc.so` 是否存在（可能是个软链接文件）：
```
$ ls -la /usr/lib64/libjemalloc.so*
lrwxrwxrwx 1 root root     16 Oct  2  2019 /usr/lib64/libjemalloc.so -> libjemalloc.so.2
-rwxr-xr-x 1 root root 608096 Oct  2  2019 /usr/lib64/libjemalloc.so.2
```
这样在启动MySQL时就会加载 `jemalloc` 动态库了。

7.2、**配置正确的NTP服务**

构建MGR需要由多节点组成，各节点间要保证时间同步。

通常采用 NTP 服务来保证时间同步，具体解决方案可参考这篇文档：[How to configure NTP server on RHEL 8 / CentOS 8 Linux](https://linuxconfig.org/redhat-8-configure-ntp-server)。

7.3、**安装其他常用辅助工具包**

建议提前安装DBA常用的辅助工具包：
```
$ yum install -y net-tools perf sysstat iotop tmux
```

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
