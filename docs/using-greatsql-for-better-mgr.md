# Use GreatSQL to play MGR more at ease

> With GreatSQL, you can be more at ease on MGR!

At the "3306π" community alon in Chengdu on March 20, Lou Shuai, CTO of GreatDB, made a theme sharing "The Road to MGR Bug Repair".

Lou Shuai pointed out that due to the complexity of MGR itself and it is more difficult to reproduce BUG scenarios, BUG repair work for MySQL MGR is usually slow and piles up. This has also caused community users to be afraid to use MySQL MGR, worrying about encountering various uncontrollable bugs, and even more serious thread, transaction hang and other problems, and they still feel that they are not so reliable.

The core R&D team of GreatDB has conducted in-depth research on the MGR architecture, and has summarized a complete and smooth BUG repair process in the continuous BUG repair practice. The defects of MGR are divided into BUG and performance categories, and a total of 16 types of BUG and Performance defect issues.
![enter image description here](https://images.gitee.com/uploads/images/2021/0401/094924_1e6384fc_8779455.jpeg "1. GreatSQL, to create a better MGR ecology-20210401.jpg")

After careful preparation for a period of time, the R&D team of Wanli Database decided to release the first stable version ```GreatSQL 8.0.25-15```, which is based on ```Percona Server 8.0.25-15```The source code is compiled. The reason for choosing the branch version of Percona is that it has already carried out optimization work such as functional additions and performance enhancements on the basis of the official version, and it can be regarded as "standing on the shoulders of giants".

The version released this time mainly has the following improvements and enhancements:

### 1. Stability improvement
- Improve the stability of large transactions
- Optimize the garbage collect mechanism of the MGR queue, improve the flow control algorithm, and reduce the amount of data sent each time to avoid performance jitter
- Solved the problem of error-prone problems when nodes join the cluster in AFTER mode
- In AFTER mode, strong consistency adopts the majority principle to adapt to the scene of network partition
- When the MGR node crashes, the abnormal state of the node can be found faster, effectively reducing the waiting time for the switchover and abnormal nodes
- Optimize the MGR DEBUG log output format

### 2. bug fix
- Fixed the problem of large-scale performance jitter of MGR when the node is abnormal
- Fixed the problem that the transfer of big data may lead to an infinite loop of logic judgments
- Fixed the issue of inefficient waiting during startup
- Fixed the problem of abnormal throughput caused by full disk
- Fixed the problem that data may be lost in multi-write mode / data loss in single master mode
- Fixed TCP self-connect problem

With the progress of the code review work, we will continue to keep the version updated and release new versions to enjoy the community friends. We also welcome everyone to try the experience together, and submit issues on gitee (submission address: https://github.com/GreatSQL/GreatSQL/issues), and we will give feedback and reply as soon as possible.

Thank you again for your support to GreatSQL and let us build a better MySQL community ecology together.

Enjoy MGR & GreatSQL :)
