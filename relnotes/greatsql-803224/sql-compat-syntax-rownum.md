# SQL兼容性 - ROWNUM语法
---

[toc]

## 1.语法

`ROWNUM`是一个伪列，主要用来实现分布功能，类似于`LIMIT` 用法。使用方式如下：

```sql
greatsql> SELECT * FROM employees WHERE ROWNUM < 11;

greatsql> select * from (select rownum rn, x from t1) t1 where t1.rn between 3 and 5;
```

## 2.语义描述

```sql
greatsql> SELECT * FROM employees WHERE ROWNUM > 1;
```

解释：对获取到的第一行记录，其 `rownum` 编号为1， 而 `where rownum > 1` 不满足条件（1>1 为 false），跳过；第二行记录，它的编号仍然为1，还是不满足条件（`rownum >1` 为false），所以该查询结果永远为空。

```sql
greatsql> select * from t1;
+------+------+
| ida  | age  |
+------+------+
|    1 |    2 |
|    2 |    3 |
|    3 |    0 |
+------+------+

greatsql> select rownum, ida from t1 order by age;
+--------+------+
| rownum | ida  |
+--------+------+
|      3 |    3 |
|      1 |    1 |
|      2 |    2 |
+--------+------+
```

**解释**：因为 `order by` 操作是在最后步骤完成的，此时可能会对 `rownum` 的最终显示顺序有影响。

### 2.1 对rownum值的限制
假定WHERE条件中，`rownum` 设定的值为N，则对N的要求是：

1. 条件值N必须是大于等于1的正整数，否则查询结果是空集。
2. 条件 `rownum > N` 返回结果是空集。因为对于取到的第一行记录，`rownum` 编号为1， 不符合条件（`rownum > N`），则该行被丢弃。第二行记录，依然编号为1，也不满足， 依次类推，结果集为空。上面的例子已有演示。
3. 当条件为 `rownum >= 1` 时，只可以返回第一行记录。


### 2.2 执行顺序说明
```sql
greatsql> select * from t1 where c1=? and c2=? and rownum <= N;
```
上述SQL语句中包含多个过滤条件，`rownum` 过滤条件会放在最后判断执行。

## 3. 其他使用限制说明

### 3.1 对JOIN的支持不同
在外连接语法中，不支持 `rownum` 作为 `join key` 使用，而内连接可以。因为在外边接中使用 `rownum` 会导致语义不明确。

```sql
greatsql> select * from t1 left join t2 on t1.ida = rownum;
ERROR 1235 (42000): This version of MySQL doesn't yet support 'ROWNUM occur in outer join on conditions.'

greatsql> select * from t1 join t2 on t1.ida = rownum;
+------+------+----+------------+-------+---------------------+
| ida  | age  | id | name       | other | created             |
+------+------+----+------------+-------+---------------------+
|    1 |    2 |  5 | Fifth Name | 55555 | 2004-04-04 04:04:04 |
|    2 |    3 |  5 | Fifth Name | 55555 | 2004-04-04 04:04:04 |
|    3 |    0 |  5 | Fifth Name | 55555 | 2004-04-04 04:04:04 |
+------+------+----+------------+-------+---------------------+
```

### 3.2 对子查询的限制
1. 支持 `FROM` 后子查询使用 `rownum`。
2. 支持非相关标量子查询中使用 `rownum`。对 `in/any/all/some`子查询， 无论相关非相关都不支持使用 `rownum`，主要原因是在 `nested loop join` 的时候，存在执行顺序问题，可能导致结果不一样。这时候报错如下：
```
ERROR 1235 (42000): This version of MySQL doesn't yet support 'ROWNUM & IN/ALL/ANY/SOME subquery';
```

### 3.3 查询结果与Oracle可能不一样
1. 因数据输出顺序不一致，在此基础上做 `rownum` 过滤，会导致最终显示结果可能也不一样。
2. 优化行为不一致，可能导致输出结果不同。例如下面几个案例：
```sql
-- 下面这个SQL，GreatSQL和Oracle的结果一样
greatsql> select * from t1 left join t2 on t1.r1=t2.r1; 

-- 下面这个SQL，GreatSQL按照原语句，对join结果集作了rownum<t1.r1 过滤
greatsql> select * from t1 left join t2 on t1.r1=t2.r1 where rownum < t1.r1;

-- 下面这个SQL，Oracle按照 join key进行了过滤的推导，推导出一个rownum < t2.r1的过滤，这样，就将最终结果集中t2表产生的null行都过滤掉了
- 这并不符合原始语义
greatsql> select * from t1 left join t2 on t1.r1=t2.r1 where rownum < t1.r1;
```
