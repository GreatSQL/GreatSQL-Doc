# 访问数据库
---

成功安装GreatSQL后，就可以登入连接GreatSQL数据库，并执行SQL语句来操作和管理数据库。

GreatSQL中除去少数新增的特性外，绝大多数语法和MySQL是完全一样的。

MySQL相关SQL语法详见手册：[SQL Statements](https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html)。

本文档中所有操作都采用命令行模式下的cli工具来演示。

**连接登入GreatSQL数据库**

有多种方式连入：
```
# 本机直接连入
$ mysql -uroot -p

# 本机指定socket文件连入
$ mysql -S/var/lib/mysql/mysql.sock -uroot -p

# 指定主机IP连入（假定本机IP地址是 172.17.0.3 ）
$ mysql -h172.17.0.3 -uroot -p
```

**修改root用户密码**
二进制及Docker方式快速安装GreatSQL后，数据库中的管理员用户root默认是空密码，安全起见，可以先修改密码：
```
# 先查看当前用户
mysql> select user();
+----------------+
| user()         |
+----------------+
| root@localhost |
+----------------+

# 修改密码
mysql> alter user user() identified by 'GreatSQL@2022';
Query OK, 0 rows affected (0.02 sec)
```
修改完成后，再次用root用户连入的话就可以用新密码了。

**创建新用户**
平时操作数据库时，尽量少用最高权限的root用户，避免误操作删除数据。最好创建新用户，并且只授予部分权限。
```
# 先以root用户登入
$ mysql -uroot 

# 创建新用户
mysql> CREATE USER GreatSQL@'172.17.0.0/16' IDENTIFIED BY 'GreatSQL-2022';


#创建一个新的用户库，并对GreatSQL用户授予读写权限
mysql> CREATE DATABASE GreatSQL;
mysql> GRANT ALL ON GreatSQL.* TO GreatSQL@'172.17.0.0/16';
```

切换到普通用户GreatSQL登入，创建测试表，写入数据：
```
$ mysql -h172.17.0.3 -uGreatSQL -p'GreatSQL-2022'
...
# 切换到GreatSQL数据库下
mysql> use GreatSQL;
Database changed

# 创建新表
mysql> CREATE TABLE t1(id INT PRIMARY KEY);
Query OK, 0 rows affected (0.07 sec)

# 查看都有哪些数据表
mysql> SHOW TABLES;
+--------------------+
| Tables_in_GreatSQL |
+--------------------+
| t1                 |
+--------------------+
1 row in set (0.00 sec)

# 写入测试数据
mysql> INSERT INTO t1 SELECT RAND()*1024;
Query OK, 1 row affected (0.05 sec)
Records: 1  Duplicates: 0  Warnings: 0

# 查询数据
mysql> SELECT * FROM t1;
+-----+
| id  |
+-----+
| 203 |
+-----+
1 row in set (0.00 sec)
```
成功。

更多相关SQL命令/语法详见手册：[SQL Statements](https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html)。

**问题反馈**
---
- [问题反馈 gitee](https://gitee.com/GreatSQL/GreatSQL-Doc/issues)


**联系我们**
---

扫码关注微信公众号

![输入图片说明](https://images.gitee.com/uploads/images/2021/0802/141935_2ea2c196_8779455.jpeg "greatsql社区-wx-qrcode-0.5m.jpg")
