# 硬件、操作系统优化
---

本文档主要介绍从硬件、操作系统等多层次优化参考。

## 1. 服务器配置及优化

如果是在物理机上运行GreatSQL数据库，建议至少采用如下配置等级：

| 配置 | 要求 |
| --- | --- |
| CPU | 8 cores+ |
| 内存 | 8 GB+ |
| 磁盘 | 100 GB+ |
| 网络 | 千兆网络 |

如果想要支撑更高数据库服务能力，应当进一步提升服务器配置，包括且不仅限以下几点：

1. 配置更高性能的CPU，不仅是核数越多越好，处理主频也是越高越好。
2. 配置更大物理内存。
3. 配置更高物理IOPS性能的设备，例如用NVMe SSD。使用更好的物理I/O设备，相比提升物理内存综合成本通常更低。
4. 如果是X86架构的CPU，通常建议关闭NUMA；如果是ARM架构，则可以开启NUMA。MySQL/GreatSQL数据库是单进程多线程模式，如果是是运行单实例的场景下，没必要开启NUMA；如果是运行多实例，则可以开启NUMA以提升性能。
5. 调整CPU设置，修改为最大性能模式。
6. 如果计划构建MGR集群，则通常要使用不低于千兆网络的条件，如果有条件甚至可以使用万兆网络，或者InfiniBand网络。

详情参考文档：[安装准备](/user-manual/4-install-guide/4-1-install-prepare.md#1-硬件环境)。

## 2. 操作系统层优化

1. 采用XFS文件系统，以保证在高I/O负载情况下IOPS的性能及稳定性。
2. 修改数据库分区的I/O Scheduler，设置为 noop / deadline。
3. 关闭SWAP。运行数据库服务建议配置足够的物理内存。如果内存不足，不建议使用SWAP作为缓冲，因为这会降低性能。建议永久关闭系统SWAP。
4. 关闭透明大页（Transparent Huge Pages / THP）。OLTP型数据库内存访问模式通常是稀疏的而非连续的。当高阶内存碎片化比较严重时，分配 THP 页面会出现较高的延迟，反而影响性能。
5. 调整mysql用户使用资源上限，避免报告文件数不够等限制错误。
6. 其他内核参数优化。

详情参考文档：[安装准备](/user-manual/4-install-guide/4-1-install-prepare.md#2-系统环境)。

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
