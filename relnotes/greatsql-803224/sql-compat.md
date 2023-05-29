# SQL兼容性

为了方便现存业务中部分非标语法，GreatSQL从8.0.32-24版本起持续扩展SQL兼容性，以降低迁移改造成本和工作量，方便业务方更快改造适配。SQL兼容性列举如下。

## 1. 数据类型
- CLOB，这是LONGTEXT的同义词，直接使用即可。
- VARCHAR2，这是VARCHAR的同义词，直接使用即可。

示例：
```
greatsql> create table t1(
id int unsigned not null auto_increment primary key, 
c1 clob not null default '', 
c2 varchar2(30) not null default '');
ERROR 1101 (42000): BLOB, TEXT, GEOMETRY or JSON column 'c1' can't have a default value

greatsql> create table t1(
id int unsigned not null auto_increment primary key, 
c1 clob not null, 
c2 varchar2(30) not null default '');
Query OK, 0 rows affected (0.25 sec)

greatsql>show create table t1\G
*************************** 1. row ***************************
       Table: t1
Create Table: CREATE TABLE `t1` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `c1` longtext NOT NULL,
  `c2` varchar(30) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
1 row in set (0.01 sec)
```

## 2. SQL语法
- DATETIME 加减运算
- ROWNUM语法
- 子查询无别名

## 3. 函数
- [ADD_MONTHS()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-addmonths.md)
- [DECODE()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-decode.md)
- [INSTR()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-instr.md)
- [LENGTH()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-length.md)
- [LENGTHB()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-lengthb.md)
- [MONTHS_BETWEEN()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-monthsbetween.md)
- [NVL()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-nvl.md)
- [SUBSTRB()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-substrb.md)
- [SYSDATE()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-sysdate.md)
- [TO_CHAR()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-tochar.md)
- [TO_DATE()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-todate.md)
- [TO_NUMBER()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-tonumber.md)
- [TO_TIMESTAMP()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-totimestamp.md)
- [TRANSLATE()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-translate.md)
- [TRUNC()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-trunc.md)
- [SYS_GUID()](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-sysguid.md)
