# 深入浅出MGR

## 缘起
《实战MGR》视频课程已经完成并上线了，碍于PPT内容比较精简，直接放出来对大家帮助也不大，所以就打算新开个坑，整理一个《深入浅出MGR》的专栏，以在线连载的方式发布，后面如果有条件，在整理成电子书也是可以的。

## 内容结构
本专栏打算由以下几块内容构成：
1.  **MGR概要** ，介绍什么是MGR，具备哪些技术特点。
2.  **MGR实战** ，介绍用各种方式构建MGR集群，包括手工、MySQL Shell、Docker、Ansible等多种方式。
3.  **MGR原理** ，介绍MGR工作的底层技术细节。
4.  **MGR架构及最佳实践** ，介绍基于MGR的架构方案，以及MGR的最佳实践经验。
5.  **GreatSQL特性** ，介绍GreatSQL的技术特性，包括对MGR的改进内容，以及InnoDB并行查询特性等。
6.  **FAQ** ，罗列了关于MGR及GreatSQL常见的一些问题。

## 专栏目录
- [1. MGR简介](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-01.md)
- [2. 组复制技术架构](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-02.md)
- [3. 安装部署MGR集群](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-03.md)
- [4. 利用MySQL Shell安装部署MGR集群](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-04.md)
- [5. MGR管理维护](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-05.md)
- [6. MGR状态监控](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-06.md)
- [7. 利用MySQL Router构建读写分离MGR集群](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-07.md)
- [8. 利用Ansible快速构建MGR](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-08.md)
- [9. 利用Docker快速构建MGR](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-09.md)
- [10. 选主算法、多版本兼容性及滚动升级](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-10.md)
- [11. MGR技术架构及数据同步、认证机制](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-11.md)
- [12. 新节点加入过程解读](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-12.md)
- [13. 分布式恢复](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-13.md)
- [14. 流量控制（流控）](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-14.md)
- [15. 故障检测与网络分区](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-15.md)
- [16. 数据一致性、安全性保障](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-16.md)
- [17. MGR性能优化](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-17.md)
- [18. 最佳实践参考](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-18.md)
- [19. GreatSQL特性](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/deep-dive-mgr/deep-dive-mgr-18.md)


## 读者群体
本专栏适合以下读者群体：
- DBA
- 开发工程师
- 架构师
- 技术主管&经理
- 其他爱好者

## 已知在用MGR的企业
- 多家国有大型银行、大型股份制银行、地方城商行
- 某知名互联网大厂
- 某知名生活服务平台
- 某知名社交网络平台
- 某在线旅游平台
- 某知名新能源充电网络企业
- 某中国领先的汽车平台网
- 某知名在线教育平台
- 某知名数字零售联合云
- 某电信集成运营服务商

## 参考资料、文档
- [MySQL 8.0 Reference Manual](https://dev.mysql.com/doc/refman/8.0/en/group-replication.html) 
- [数据库内核开发 - 温正湖](https://www.zhihu.com/column/c_206071340)
- [Group Replication原理 - 宋利兵](https://mp.weixin.qq.com/s/LFJtdpISVi45qv9Wksv19Q)

## 免责声明
因个人水平有限，专栏中难免存在错漏之处，请勿直接复制文档中的命令、方法直接应用于线上生产环境。请读者们务必先充分理解并在测试环境验证通过后方可正式实施，避免造成生产环境的破坏或损害。

## 加入团队
如果您有兴趣一起加入协作，欢迎联系我们，可直接提交PR，或者将内容以markdown的格式发送到邮箱：greatsql@greatdb.com。

亦可通过微信、QQ联系我们。

![Contact Us](../docs/contact-us.png)
