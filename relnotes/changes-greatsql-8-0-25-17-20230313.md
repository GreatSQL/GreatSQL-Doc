# Changes in GreatSQL 8.0.25-17（2023-3-13）
**GreatSQL 8.0.25-17** is a slightly improved version that mainly fixes the issue of InnoDB parallel queries in GreatSQL that may cause queries to hang or even crash. Other aspects are the same as GreatSQL 8.0.25-16.

This [**reference for my.cnf**](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/docs/my.cnf-example-greatsql-8.0.25-17) is recommended.

## 1. New features

## 2. Stability improvement

## 3. Other adjustments

## 4. Bug fix
01. Fix a problem where InnoDB parallel queries in GreatSQL may cause queries to hang or even crash.

## 5. GreatSQL VS MySQL Community Edition

| Features | GreatSQL 8.0.25-16| MySQL 8.0.25 Community Server |
|---| --- | --- |
| Arbitration Node/Voting Node | ✅ | ❎ |
| Single primary fast mode | ✅ | ❎ |
| Geo tag | ✅ | ❎ |
| New flow control algorithm | ✅ | ❎ |
| InnoDB Parallel Query Optimization | ✅ | ❎ |
| Thread Pool | ✅ | ❎ |
|Audit | ✅ | ❎ |
| InnoDB transaction lock optimization | ✅ | ❎ |
|SEQUENCE_TABLE(N) function|✅ | ❎ |
|InnoDB table corruption exception handling|✅ | ❎ |
|Forced to use only InnoDB engine tables|✅ | ❎ |
|Kill idle transactions and avoid long lock waits|✅ | ❎ |
|Data Masking (data masking/coding)|✅ | ❎ |
|InnoDB fragmented page statistics enhancement|✅ | ❎ |
|Support MyRocks engine|✅ | ❎ |
| InnoDB I/O performance improvements | ⭐️⭐️⭐️⭐️⭐️ | ⭐️⭐️ |
| Network Partition Abnormal Response | ⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| Improve node exception exit handling | ⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| Consistent Read Performance | ⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| Improve MGR throughput |⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| Statistics Enhancements |⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| slow log enhancement | ⭐️⭐️⭐️⭐️⭐️ | ⭐️ |
| Big Transaction | ⭐️⭐️⭐️⭐️ | ⭐️ |
| Fix the risk of data loss in multi-write mode | ⭐️⭐️⭐️⭐️⭐️ | / |
| Fix the risk of losing data in single-master mode | ⭐️⭐️⭐️⭐️⭐️ | / |
| MGR cluster startup efficiency improved | ⭐️⭐️⭐️⭐️⭐️ | / |
| Cluster node disk full processing | ⭐️⭐️⭐️⭐️⭐️ | / |
| Fix TCP self-connect issue | ⭐️⭐️⭐️⭐️⭐️ | / |
| PROCESSLIST Enhancement | ⭐️⭐️⭐️⭐️⭐️ | / |

## 6. GreatSQL Release Notes
- [Changes in GreatSQL 8.0.25-16 (2022-5-16)](https://github.com/GreatSQL/GreatSQL-Doc/blob/main/relnotes/changes-greatsql-8-0-25-16-20220516.md)
- [Changes in GreatSQL 8.0.25-15 (2021-8-26)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-8-0-25-20210826.md)
- [Changes in GreatSQL 5.7.36-39 (2022-4-7)](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/changes-greatsql-5-7-36-20220407.md)
