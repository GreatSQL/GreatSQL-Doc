# SQL兼容性 - INSTR()函数
---
[toc]
## 1. 语法
```
INSTR( string1, string2 [, start_position [, nth_appearance ] ] )
```

## 2. 定义和用法
`INSTR()` 函数的作用是返回要截取的字符串在源字符串中的位置。即在 `string1` 中查找 `string2`，是从 `start_position` 给出的偏移量开始在 `string1` 里查找，查找出第 `nth_appearance` 次出现 `string2` 的位置。

## 3. SQL兼容说明

在GreatSQL中 `INSTR()` 函数的使用方法和Oracle相同。

在MySQL中已有 `INSTR()` 函数，其原生用法为：
```sql
INSTR(str,substr)
```

在GreatSQL中，扩展为下面的用法：
```sql
INSTR( string1, string2 [, start_position [, nth_appearance ] ] )
```
即：`INSTR(源字符串, 目标字符串, 起始位置, 匹配序号)`。

**注意**：由于在MySQL中已有原生 `INSTR()` 函数，如果想使用GreatSQL扩展后的 `INSTR()` 函数，需要先执行 `set sql_mode = oracle` 激活SQL兼容模式。

GreatSQL中 `INSTR()` 函数与Oracle不同之处有：当参数 `nth_appearance` 值为小数时，结果与Oacle不一致（Oacle会做特殊转换处理），详见下方示例。

## 4. 示例

下面几个案例展示在GreatSQL和Oracle中可能存在不同的处理行为和返回结果：
```
-- 在GreatSQL和Oracle中均返回1
> select INSTR('0.3333', '0.3') from dual;

-- 在GreatSQL和Oracle中均返回1
> select INSTR(0.3333, 0.3) from dual;

-- 在GreatSQL返回1
-- 在Oracle中返回2
> select INSTR('0.3333', 0.3) from dual;
```

下面是在GreatSQL中的测试案例：
```
-- 先激活SQL兼容模式
greatsql> set sql_mode = oracle;

-- 返回：3，第一次出现“l”的位置
greatsql> select INSTR('helloworld','l') from dual;
+-------------------------+
| INSTR('helloworld','l') |
+-------------------------+
|                       3 |
+-------------------------+

-- 返回：4，即“lo”同时出现，第一个字母“l”出现的位置
greatsql> select INSTR('helloworld','lo') from dual;
+--------------------------+
| INSTR('helloworld','lo') |
+--------------------------+
|                        4 |
+--------------------------+

-- 返回：4，在"helloworld"的第2个字符(字符"e")偏移位置开始，查找第二次出现的“l”的位置
greatsql> select INSTR('helloworld','l',2,2) from dual;
+-----------------------------+
| INSTR('helloworld','l',2,2) |
+-----------------------------+
|                           4 |
+-----------------------------+

-- 返回：9，在"helloworld"的偏移位置倒数第1(字符"d")开始，往回查找第一次出现的“l”的位置
greatsql> select INSTR('helloworld','l',-1,1) from dual;
+------------------------------+
| INSTR('helloworld','l',-1,1) |
+------------------------------+
|                            9 |
+------------------------------+

-- 返回：22，即最后IP第四段数据
greatsql> select SUBSTR('192.168.0.22', INSTR('192.168.0.22', '.', 1, 3) +1) from dual;
+-------------------------------------------------------------+
| SUBSTR('192.168.0.22', INSTR('192.168.0.22', '.', 1, 3) +1) |
+-------------------------------------------------------------+
| 22                                                          |
+-------------------------------------------------------------+
```

下面这些案例可以自行测试，想想结果是否符合预期：
```
set sql_mode = oracle;
select instr('a','A') from dual;
select instr('thisisatestsentence','t',1,'')  from dual;
select instr('thisisatestsentence','t','',1)  from dual;
select instr('thisisatestsentence','t',1,2.1)  from dual;
select instr('thisisatestsentence','t',1,2.5)  from dual;
select instr('thisisatestsentence','t',0.1,1)  from dual;
select instr('thisisatestsentence','t',0.5,1)  from dual;
```

