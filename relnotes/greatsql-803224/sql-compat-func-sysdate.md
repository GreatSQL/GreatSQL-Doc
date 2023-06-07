# SQL兼容性 - SYSDATE()函数
---
[toc]
## 1. 语法
```sql
SYSDATE()
-- or
SYSDATE
```
调用时，可以不带上表示函数的括号。

## 2. 定义和用法

`SYSDATE` 作为系统关键字实现，在 oracle mode 中，等价`NOW(6)`，在非 oracle mode 下就是 `SYSDATE()`。

## 3. 示例

```sql
greatsql> set sql_mode = default; select sysdate, sysdate() from dual;
Query OK, 0 rows affected (0.00 sec)

+---------------------+---------------------+
| sysdate             | sysdate()           |
+---------------------+---------------------+
| 2023-05-11 14:43:52 | 2023-05-11 14:43:52 |
+---------------------+---------------------+

greatsql> set sql_mode = oracle; select sysdate, sysdate() from dual;
Query OK, 0 rows affected (0.00 sec)

+----------------------------+----------------------------+
| sysdate                    | sysdate()                  |
+----------------------------+----------------------------+
| 2023-05-11 14:43:52.865664 | 2023-05-11 14:43:52.865664 |
+----------------------------+----------------------------+
```
可以看到在不同sql mode下输出结果不同，在oracle mode下输出的精度更高。
