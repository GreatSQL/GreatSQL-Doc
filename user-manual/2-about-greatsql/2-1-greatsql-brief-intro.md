# GreatSQL简介
---

GreatSQL开源数据库是适用于金融级应用的国内自主MySQL版本，专注于提升MGR可靠性及性能，支持InnoDB并行查询等特性，可以作为MySQL或Percona Server的可选替换，用于线上生产环境，且完全免费并兼容MySQL或Percona Server。

GreatSQL除了提升MGR性能及可靠性，还引入InnoDB事务锁优化及并行查询优化等特性，以及众多BUG修复。

## 版本特性
---

相较于MySQL/Percona Server，GreatSQL主要增加几个特性：
1. **地理标签**
1. **仲裁节点**
1. **快速单主**
1. **智能选主**
1. **并行查询**

选用GreatSQL主要有以下几点优势：

- 专注于提升MGR可靠性及性能，支持InnoDB并行查询特性
- 是适用于金融级应用的MySQL分支版本
- 地理标签，提升多机房架构数据可靠性
- 仲裁节点，用更低的服务器成本实现更高可用
- 单主模式下更快，选主机制更完善
- InnoDB表也支持并行查询，让CPU资源不再浪费
- 全新流控机制，让MGR运行更流畅不频繁抖动
- 相对官方社区版，MGR运行更稳定、可靠
- 其他...


**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
