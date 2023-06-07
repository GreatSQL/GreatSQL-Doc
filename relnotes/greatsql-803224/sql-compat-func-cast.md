# SQL兼容性 - CAST()函数
---
[toc]

## 1. 语法

```sql
CAST(expr AS VARCHAR(N))
```

## 2. 定义和用法
在原生 `CAST()` 函数的基础上，增加对 `VARCHAR(N)` 类型的支持。


## 3. 示例
```
greatsql> SELECT CAST('greatsql' AS VARCHAR(10)), CAST('greatsql' AS VARCHAR(5));
+---------------------------------+--------------------------------+
| CAST('greatsql' AS VARCHAR(10)) | CAST('greatsql' AS VARCHAR(5)) |
+---------------------------------+--------------------------------+
| greatsql                        | great                          |
+---------------------------------+--------------------------------+
1 row in set, 1 warning (0.00 sec)

greatsql> show warnings;
+---------+------+-----------------------------------------------+
| Level   | Code | Message                                       |
+---------+------+-----------------------------------------------+
| Warning | 1292 | Truncated incorrect CHAR(5) value: 'greatsql' |
+---------+------+-----------------------------------------------+
```
