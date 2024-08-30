[![](https://img.shields.io/badge/GreatSQL-官网-orange.svg)](https://greatsql.cn/)
[![](https://img.shields.io/badge/GreatSQL-论坛-brightgreen.svg)](https://greatsql.cn/forum.php)
[![](https://img.shields.io/badge/GreatSQL-博客-brightgreen.svg)](https://greatsql.cn/home.php?mod=space&uid=10&do=blog&view=me&from=space)
[![](https://img.shields.io/badge/License-GPL_v2.0-blue.svg)](https://gitee.com/GreatSQL/GreatSQL/blob/master/LICENSE)
[![](https://img.shields.io/badge/release-8.0.32_25-blue.svg)](https://gitee.com/GreatSQL/GreatSQL/releases/tag/GreatSQL-8.0.32-25)

# GreatSQL文档
---
GreatSQL相关文档、专栏内容、视频等资源汇总，主要包含以下内容：

## GreatSQL用户手册
- [GreatSQL用户手册](https://gitee.com/GreatSQL/GreatSQL-Manual)，最新版本GreatSQL用户手册

## GreatSQL新版本发布会视频
- [GreatSQL新版本发布会](https://greatsql.cn/smx_course-lesson.html?op=video&ids=9)，历次GreatSQL新版本发布会视频内容

## GreatSQL管理运维使用相关
- [GCA认证课程学习视频](https://greatsql.cn/smx_course-lesson.html?op=video&ids=10)，GreatSQL认证数据库专员培训视频课程
- [实战MGR专栏视频](https://greatsql.cn/smx_course-lesson.html?op=video&ids=5)，适合新手入门的MGR学习实操视频内容
- [深入浅出MGR专栏文章](./deep-dive-mgr)，深入浅出MGR相关知识点、运维管理实操
- [深入浅出MGR专栏视频](https://greatsql.cn/smx_course-lesson.html?op=video&ids=6)，深入浅出MGR相关知识点、运维管理实操视频内容

## GreatSQL编译构建相关
- [在Docker中编译GreatSQL](https://gitee.com/GreatSQL/GreatSQL-Docker/tree/master/GreatSQL-Build)
- [在Docker中编译GreatSQL Shell](https://gitee.com/GreatSQL/GreatSQL-Docker/tree/master/GreatSQL-Shell-Build)
- [用于编译GreatSQL RPM包的Spec文件](./build-gs/greatsql.spec)
- [在CentOS环境下源码编译安装GreatSQL](./docs/build-greatsql-with-source.md)
- [在麒麟OS+龙芯环境下源码编译安装GreatSQL](./docs/build-greatsql-with-source-under-kylin-and-loongson.md)
- [在openEuler、龙蜥Anolis、统信UOS系统下编译GreatSQL二进制包](./docs/build-greatsql-under-openeuler-anolis-uos.md)

## my.cnf参考模板
- [my.cnf参考模板](https://greatsql.cn/docs/3-quick-start/3-4-quick-start-with-cnf.html)

## 其他
- [GreatSQL-Docker](https://gitee.com/GreatSQL/GreatSQL-Docker)，在Docker中运行GreatSQL
- [在GreatSQL中进行TPC-H测试相关资源](./tpch)
- [在GreatSQL中进行BenchmarkSQL测试相关资源](./benchmarksql-5.0)
- [历次公开分享PPT](./Presentations)

# 关于 GreatSQL
--- 

GreatSQL数据库是一款**开源免费**数据库，可在普通硬件上满足金融级应用场景，具有**高可用**、**高性能**、**高兼容**、**高安全**等特性，可作为MySQL或Percona Server for MySQL的理想可选替换。

![GreatSQL LOGO](/GreatSQL-logo-01.png "GreatSQL LOGO")

# 核心特性

## 高可用

针对MGR进行了大量改进和提升工作，新增支持**地理标签**、**仲裁节点**、**读写节点可绑定动态IP**、**快速单主模式**、**智能选主**，并针对**流控算法**、**事务认证队列清理算法**、**节点加入&退出机制**、**recovery机制**等多项MGR底层工作机制算法进行深度优化，进一步提升优化了MGR的高可用保障及性能稳定性。

更多信息详见文档：[高可用](https://greatsql.cn/docs/8032-25/user-manual/5-enhance/5-2-ha.html)。

## 高性能

相对MySQL及Percona Server For MySQL的性能表现更稳定优异，支持**高性能的内存查询加速AP引擎**、**InnoDB并行查询**、**并行LOAD DATA**、**事务无锁化**、**线程池等**特性，在TPC-C测试中相对MySQL性能提升超过30%，在TPC-H测试中的性能表现是MySQL的十几倍甚至上百倍。

更多信息详见文档：[高性能](https://greatsql.cn/docs/8032-25/user-manual/5-enhance/5-1-highperf.html)。

## 高兼容

支持大多数常见Oracle用法，包括数据类型、函数、SQL语法、存储程序等兼容性用法。

更多信息详见文档：[高兼容](https://greatsql.cn/docs/8032-25/user-manual/5-enhance/5-3-easyuse.html)。

## 高安全

支持逻辑备份加密、CLONE备份加密、审计日志入表、表空间国密加密等多个安全提升特性，进一步保障业务数据安全，更适用于金融级应用场景。

更多信息详见文档：[高安全](https://greatsql.cn/docs/8032-25/user-manual/5-enhance/5-4-security.html)。

# 下载GreatSQL
---

## GreatSQL 8.0
- [GreatSQL 8.0.32-25](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.32-25)
- [GreatSQL 8.0.32-24](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.32-24)
- [GreatSQL 8.0.25-17](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-17)
- [GreatSQL 8.0.25-16](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-16)
- [GreatSQL 8.0.25-15](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-8.0.25-15)

## GreatSQL 5.7
- [GreatSQL 5.7.36](https://gitee.com/GreatSQL/GreatSQL/releases/GreatSQL-5.7.36-39)

# 版本历史
---
## GreatSQL 8.0
- [Changes in GreatSQL 8.0.32-25 (2023-12-28)](https://greatsql.cn/docs/8032-25/user-manual/1-docs-intro/relnotes/changes-greatsql-8-0-32-25-20231228.html)
- [Changes in GreatSQL 8.0.32-24 (2023-6-5)](https://greatsql.cn/docs/8032-25/user-manual/1-docs-intro/relnotes/changes-greatsql-8-0-32-24-20230605.html)
- [Changes in GreatSQL 8.0.25-17 (2023-3-13)](https://greatsql.cn/docs/8032-25/user-manual/1-docs-intro/relnotes/changes-greatsql-8-0-25-17-20230313.html)
- [Changes in GreatSQL 8.0.25-16 (2022-5-16)](https://greatsql.cn/docs/8032-25/user-manual/1-docs-intro/relnotes/changes-greatsql-8-0-25-16-20220516.html)
- [Changes in GreatSQL 8.0.25-15 (2021-8-26)](https://greatsql.cn/docs/8032-25/user-manual/1-docs-intro/relnotes/changes-greatsql-8-0-25-20210820.html)

## GreatSQL 5.7
- [Changes in GreatSQL 5.7.36-39 (2022-4-7)](https://greatsql.cn/docs/8032-25/user-manual/1-docs-intro/relnotes/changes-greatsql-5-7-36-20220407.html)

# 问题反馈
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)

# 提示
---
[如果您使用了GreatSQL，请告诉我们。有机会获得精美礼品一份和免费技术支持](https://wj.qq.com/s2/11543483/9e09/)

# 联系我们
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
