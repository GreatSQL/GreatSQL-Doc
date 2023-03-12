# Changes in GreatSQL 8.0.25-17（2023-3-13）

**GreatSQL 8.0.25-17** 是一个微小改进版本，主要是修复GreatSQL中InnoDB并行查询可能导致查询hang住，甚至crash的问题，其他方面和GreatSQL 8.0.25-16版本是一样的。

推荐使用这份[**my.cnf配置参考**](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example-greatsql-8.0.25-17)。

## 1.新增特性

## 2.稳定性提升

## 3.其他调整


## 4.bug修复
01. 修复GreatSQL中InnoDB并行查询可能导致查询hang住，甚至crash的问题。

## 5. GreatSQL VS MySQL社区版

| 特性 | GreatSQL 8.0.25-17| MySQL 8.0.25 社区版 |
|---| --- | --- |
| 投票节点/仲裁节点 | ✅ | ❎ |
| 快速单主模式 | ✅ | ❎ |
| 地理标签 | ✅ | ❎ |
| 全新流控算法 | ✅ | ❎ |
| InnoDB并行查询优化 | ✅ | ❎ |
| 线程池（Thread Pool） | ✅ | ❎ |
|审计| ✅ | ❎ |
| InnoDB事务锁优化 | ✅ | ❎ |
|SEQUENCE_TABLE(N)函数|✅ | ❎ |
|InnoDB表损坏异常处理|✅ | ❎ |
|强制只能使用InnoDB引擎表|✅ | ❎ |
|杀掉空闲事务，避免长时间锁等待|✅ | ❎ |
|Data Masking（数据脱敏/打码）|✅ | ❎ |
|InnoDB碎片页统计增强|✅ | ❎ |
|支持MyRocks引擎|✅ | ❎ |
| InnoDB I/O性能提升 |  ⭐️⭐️⭐️⭐️⭐️ | ⭐️⭐️ | 
| 网络分区异常应对 |  ⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 完善节点异常退出处理 |   ⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 一致性读性能 |   ⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 提升MGR吞吐量 |⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 统计信息增强 |⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| slow log增强 |⭐️⭐️⭐️⭐️⭐️ | ⭐️ | 
| 大事务处理 |   ⭐️⭐️⭐️⭐️ | ⭐️ | 
| 修复多写模式下可能丢数据风险 | ⭐️⭐️⭐️⭐️⭐️ | /  | 
| 修复单主模式下切主丢数据风险 | ⭐️⭐️⭐️⭐️⭐️ | / | 
| MGR集群启动效率提升 | ⭐️⭐️⭐️⭐️⭐️ |  / | 
| 集群节点磁盘满处理 |   ⭐️⭐️⭐️⭐️⭐️ | /  | 
| 修复TCP self-connect问题| ⭐️⭐️⭐️⭐️⭐️ | / | 
| PROCESSLIST增强 | ⭐️⭐️⭐️⭐️⭐️ | /  | 

## 6. GreatSQL Release Notes
- [Changes in GreatSQL 8.0.25-16 (2022-5-16)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-16-20220516.md)
- [Changes in GreatSQL 8.0.25-15 (2021-8-26)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-20210820.md)
- [Changes in GreatSQL 5.7.36-39 (2022-4-7)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-5-7-36-20220407.md)
