# SQL兼容性 - DECODE()函数
---
[toc]
## 1. 语法

```sql
DECODE(
    expr,                   /* 字段或表达式 */
    search,                 /* 可能值 */
    result                  /* 返回值 */
    [, search, result ]...  /* 可选可能值/返回值对[允许多个] */
    [, default ]            /* 可选无匹配返回值 */
)
```

## 2. 定义和用法
顾名思义，`DECODE()` 函数的作用是根据表达式编码/输出相应的结果，比较`expr`和`search`的结果，如果一致则返回对应的`result`，如果所有条件都不匹配则返回`default`，如果`default`不存在，则返回NULL。

对于`expr=search=NULL`，的情况与Oracle行为一致，会返回第一个`search`为NULL的`result`。

注意：可能值与返回值的评估使用`短路评估`，即：只要存在`expr`=`search`则后续`search`不会被评估。

## 3. 示例
```sql
greatsql> SELECT decode(1, 1, 'one', 2, 'two', 'other');
+----------------------------------------+
| decode(1, 1, 'one', 2, 'two', 'other') |
+----------------------------------------+
| one                                    |
+----------------------------------------+

greatsql> SELECT decode(null, 1, 'one', null, 'null');
+--------------------------------------+
| decode(null, 1, 'one', null, 'null') |
+--------------------------------------+
| null                                 |
+--------------------------------------+
```
