# 性能测试
---

本文档主要介绍如何对GreatSQL进行性能测试。

## 1. 压测工具

优先推荐使用 [sysbench工具](https://github.com/akopytov/sysbench) 进行性能测试。

如果想要测试GreatSQL的InnoDB并行查询特性，则可以使用 [tpch工具](https://www.tpc.org/tpch/)。

本文以侧重OLTP场景下的性能测试为例，因此推荐使用sysbench工具。

## 2. 压测模式

sysbench默认支持以下几种OLTP测试方案：

- oltp_delete
- oltp_insert
- oltp_point_select
- oltp_read_only
- oltp_read_write
- oltp_update_index
- oltp_update_non_index
- oltp_write_only

如果有条件，可以把这几种方案全部跑一遍。

## 3. 压测参数及建议

压测的目的通常是想找到数据库运行时的性能瓶颈，以及在不断摸索调整参数选项，采用何种设置模式下其性能表现最好。

只有个别时候的压测是为了找到服务器硬件或者数据库的运行极限值，看看在什么情况下能把硬件或数据库"压死"。

不同服务器配置等级，对应不同的压力测试值。

对于压测参数，有几个建议：

1. 并发线程数，可以分别是逻辑CPU数的1/8、1/4、1/2以及跑满。
2. 数据库的`innodb_buffer_pool_size`通常设置不超过物理内存的50%。
3. 测试表个数通常不低于逻辑CPU数的1/2。
4. 测试数据库物理大小通常不低于`innodb_buffer_pool_size`，因为生产环境中的业务数据量基本上都是大于物理内存的。
5. 如果本意就是想测试数据库在非物理I/O为瓶颈场景下的性能表现，则可以减少测试数据量，让数据尽可能加载到buffer pool中。
6. 运行sysbench压测客户机和数据库服务器分开，不要在同一个物理环境内，避免因为sysbench本身也产生性能损耗而影响数据库的性能表现。
7. 单轮测试时长通常不低于10分钟。
8. 每轮测试结束后，预留足够间隔时长，让数据库将所有脏数据、日志都有充分时间刷到磁盘，服务器趋于空负载后再次下一轮压测。
9. 每轮测试开始前，最好能先进行数据预热，即先运行一小段时间压测，让热点数据都加载到buffer pool中之后再正式开始压测。
10. 每轮测试结束后，最好清空所有数据，在下一轮新的测试开始前，重新初始化填充数据。

下面是我常用的sysbench压测参数供参考：
```
sysbench /usr/local/share/sysbench/oltp_read_write.lua \
...
  --tables=64 \
  --table_size= 10000000 \
  --threads=128 \
  --rand-type=uniform \
  --report-interval=1 \
  --db-ps-mode=disable \
  --mysql-ignore-errors=all \
  --time=900 run
```

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
