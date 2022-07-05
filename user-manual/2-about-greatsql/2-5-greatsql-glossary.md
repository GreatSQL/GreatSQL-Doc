# 术语表
---

| 术语 | 解释 |
| --- | --- |
| MGR<br/>GR<br/>Group Replication | MySQL Group Replication，MySQL组复制的简称。MySQL官方推出的一种不同于主从复制、半同步复制的全新复制机制。|
| GCS | Group Communication System，组通信系统，MGR底层通信系统。|
| Xcom | Paxos算法在MGR中的具体实现，在MySQL里称之为XCom，由它充当MGR的通信引擎。|
| member | MGR成员，也称为节点。|
| primary | 称为主要节点，主节点，MGR节点角色之一。响应读写事务请求。|
| secondary | 称为辅助节点，从节点，MGR节点角色之一。只能响应只读事务请求。|
| consensus | 共识。在MGR中，一个事务发起后，要广播到各个节点，当多数派节点达成共识后，这个事务才可以被提交。所谓的多数派就是超过半数的节点达成一致，例如总共3个节点，则至少2个节点达成一致。|
| joiner | MGR中新加入的节点，称之为joiner。|
| donor | 新节点加入MGR时，为新节点提供数据传输的节点称为donor。|
| arbitrator | 仲裁节点/投标节点。GreatSQL 8.0.25-16版本中新增角色类型。该节点不存储用户数据，没有binlog，也不需要回放relay log，只参与MGR状态投票/仲裁。详情参考文档：[1.1 新增仲裁节点（投票节点）角色](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-16-20220516.md#11-%E6%96%B0%E5%A2%9E%E4%BB%B2%E8%A3%81%E8%8A%82%E7%82%B9%E6%8A%95%E7%A5%A8%E8%8A%82%E7%82%B9%E8%A7%92%E8%89%B2)。|
| zone id | 地理标签。可以对每个节点设置地理标签，主要用于解决多机房数据同步的问题。详情参考文档：[1.1 新增节点地理标签](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-20210820.md#11-%E6%96%B0%E5%A2%9E%E8%8A%82%E7%82%B9%E5%9C%B0%E7%90%86%E6%A0%87%E7%AD%BE)。|
| fast mode | 快速单主模式。在该模式下可以降低MGR事务代价，提升事务性能。详情参考文档：[1.2 新增快速单主模式](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-16-20220516.md#12-%E6%96%B0%E5%A2%9E%E5%BF%AB%E9%80%9F%E5%8D%95%E4%B8%BB%E6%A8%A1%E5%BC%8F)。|
| election mode | 选主策略。设置选项 `group_replication_primary_election_mode` 选择不同的选主策略。详情参考文档：[1.4 自定义选主模式](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-16-20220516.md#14-%E8%87%AA%E5%AE%9A%E4%B9%89%E9%80%89%E4%B8%BB%E6%A8%A1%E5%BC%8F)。|
| pq | parallel query（并行查询）的缩写。GreatSQL合并了华为鲲鹏计算团队贡献的Patch，实现了InnoDB并行查询特性。详情参考文档：[InnoDB并行查询优化参考](/docs/innodb-parallel-execute.md)|


**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
