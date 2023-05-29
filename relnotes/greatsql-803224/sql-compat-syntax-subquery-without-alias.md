# SQL兼容性 - 子查询无别名
---
[toc]
## 1. 语法

```sql
greatsql> SELECT * FROM (SELECT 1 FROM DUAL), (SELECT 2 FROM DUAL);
```

即在子查询SQL语句中，无需加上别名而不会报语法错误。

## 2. 示例

```sql
greatsql>  SELECT * FROM (SELECT 1 FROM DUAL), (SELECT 2 FROM DUAL);
+---+---+
| 1 | 2 |
+---+---+
| 1 | 2 |
+---+---+
```

这个SQL请求如果是放在MySQL中执行，则会报告错误：
```
greatsql> SELECT * FROM (SELECT 1 FROM DUAL), (SELECT 2 FROM DUAL);
ERROR 1248 (42000): Every derived table must have its own alias
```
