# SQL兼容性 - TO_NUMBER()函数
---
[toc]
## 1. 语法

```sql
TO_NUMBER(expr [ , fmt [ , 'nlsparam'] ] )
```

## 2. 定义和用法

`TO_NUMBER` 将 `expr` 转换成一个由 `fmt` 指定格式的 `number` 类型的值。

当前支持用法：
```
-- 最简语法
TO_NUMBER(expr)

-- 自动去除左右空格
TO_NUMBER(' xxxxx ')

-- 目前fmt参数仅支持常用如"9990.9909"或'9990.9909'格式，整数位以及小数位支持9或0表示格式，不进行四舍五入操作
TO_NUMBER(expr [ , fmt [ , 'nlsparam'] ] )

-- 以下两个SQL都返回NULL
TO_NUMBER('')
TO_NUMBER(null)

-- 完整语法
TO_NUMBER(expr [ , fmt [ , 'nlsparam'] ] )
```

参数 `fmt` 可选值如下表所示：

| fmt序号 | 格式符 | 含义                                                         | 举例                                                         |
| ------- | ------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 1       | 9      | 返回具有指定位数的值，如果是正数则带有前导空格，如果是负数则带有前导减号。前导零是空白，除了零值，它为定点数的整数部分返回零 | `TO_NUMBER('1234','9999')`  返回 **1234**|
| 2       | 0      | 前导零， 尾随0                                               | `TO_NUMBER('0234','0999')` 返回 **234**；参数整数部分必须4位，待转换字符串高位以0补充 |
| 3       | 逗号,  | 字符串中含逗号的转换，格式模型中可指定多个逗号，格式限制为：逗号不能在开端；逗号不能出现在小数点右边 | `TO_NUMBER('1,234.567','9,999.999')`  返回 **1234.567** |
| 4       | 小数.  | 小数格式转换, 它是指定小数点的位置                           | `TO_NUMBER('0.12','0.99')`  返回 **0.12** |
| 5       | EEEE   | 返回科学计数算法的值(当为‘+’，指数<15,结果显示数字，>=15以后结果显示科学计算数据)；当为‘-’，指数<16,结果显示数字，>=16以后结果显示科学计算数据) | `TO_NUMBER('1.6E+02','9.9EEEE')` 返回 **160**；`TO_NUMBER('1.6e+16','9.9EEEE')` 返回 **1.6e16** |
| 6       | X      | 十六进制转换为10进制的数                                     | `TO_NUMBER('4D2','XXX')`  返回 **1234** |

## 3. SQL兼容说明

1. 目前支持的 `fmt` 格式列在上方表格中，其它暂时未支持的格式会触发报错提示。

2. 科学计数法(EEEE, fmt = 5)格式输出结果与Oracle有差异，执行SQL语句 `select TO_NUMBER('1.666e+30','9.999EEEE') FROM dual;` 在Oracle 得到的结果为 **1.666e+30**，GreatSQL得到的结果为：**1.666e30**。

3. 当设定为 X 格式（fmt = 6），且输入参数值包含特殊字符如 **‘.’** 时，`TO_NUMBER(',0.','xxx')` 结果与Oracle有差异，Oracle返回一个很大的数值，而GreatSQL判定为fmt格式输入不匹配发出报错。

4. 执行例如 `TO_NUMBER(',123,','99,999,')` 时，结果与Oracle有差异，Oracle中会报错，GreatSQL不会报错。目前与已知兼容场景冲突，如：`TO_NUMBER(',123','9,9,9,999')` 及 `TO_NUMBER('123,','9,9,9,999,')`，在GreatSQL中都不会报错，这几个例子在GreatSQL中都是返回 **123**。

5. 转义符号 **`\`** 在GreatSQL中会被统一过滤处理，与Oracle有差异。只有当设置 `sql_mode = NO_BACKSLASH_ESCAPES` 时，GreatSQL不会过滤转义字符，这时就与Oracle行为一致了。例如：`set sql_mode = NO_BACKSLASH_ESCAPES; select TO_NUMBER('-\,0.0','9,9.9') FROM dual;`，会提示错误，与Oracle行为一致。

## 4. 示例
```
greatsql> select to_number('1234.56');
+----------------------+
| to_number('1234.56') |
+----------------------+
|              1234.56 |
+----------------------+

greatsql> show create table t1\G
*************************** 1. row ***************************
       Table: t1
Create Table: CREATE TABLE `t1` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `c1` int unsigned DEFAULT NULL,
  `c2` varchar(10) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

greatsql> select * from t1;
+----+------+----------+
| id | c1   | c2       |
+----+------+----------+
|  1 |  211 | 1234abca |
|  2 | NULL | 1234     |
+----+------+----------+

greatsql> select id, c2, to_number(c2) from t1 where id = 2;
+----+------+---------------+
| id | c2   | to_number(c2) |
+----+------+---------------+
|  2 | 1234 |          1234 |
+----+------+---------------+

greatsql> select id, c2, to_number(c2, "999999.999") from t1 where id = 2;
+----+------+-----------------------------+
| id | c2   | to_number(c2, "999999.999") |
+----+------+-----------------------------+
|  2 | 1234 |                    1234.000 |
+----+------+-----------------------------+

-- 输入值不符合要求，超出转换范围
greatsql>  select id, c2, to_number(c2, "999999") from t1 where id = 1;
ERROR 1690 (22003): NUMBER value is out of range in 'to_number'

-- fmt参数格式错误
greatsql> select to_number(123.456, 'a999.99') ;
ERROR 1525 (HY000): Incorrect format model value: 'a999.99'

-- fmt参数格式正确，但来源数据不符合格式
greatsql> select to_number(123333.456, '999.99') ;
  ERROR 1690 (22003): NUMBER value is out of range in 'to_number'

-- fmt格式参数超出范围
greatsql> select to_number(12333333333333333333333333333333333333333.456,'9999999999999999999999999999999999999999999999999999999999999999999999.99') ;
ERROR 1059 (42000): Identifier name '9999999999999999999999999999999999999999999999999999999999999999999999.99' is too long
  
greatsql> select to_number('12,12,12','99,99,99.99') from dual;
+-------------------------------------+
| to_number('12,12,12','99,99,99.99') |
+-------------------------------------+
|                              121212 |
+-------------------------------------+

greatsql> SELECT to_number('0.12','0.99') FROM dual;
+--------------------------+
| to_number('0.12','0.99') |
+--------------------------+
|                     0.12 |
+--------------------------+

greatsql> SELECT to_number('1.6E+02','9.9EEEE') FROM dual;
+--------------------------------+
| to_number('1.6E+02','9.9EEEE') |
+--------------------------------+
|                            160 |
+--------------------------------+

greatsql> SELECT to_number('1.6e+16','9.9EEEE') FROM dual;
+--------------------------------+
| to_number('1.6e+16','9.9EEEE') |
+--------------------------------+
|                         1.6e16 |
+--------------------------------+

greatsql> SELECT to_number('f12','XXX') FROM dual;
+------------------------+
| to_number('f12','XXX') |
+------------------------+
|                   3858 |
+------------------------+

greatsql> SELECT to_number('4D2','XXX') FROM dual;
+------------------------+
| to_number('4D2','XXX') |
+------------------------+
|                   1234 |
+------------------------+

greatsql> set sql_mode = NO_BACKSLASH_ESCAPES;

greatsql> select to_number('-\,0.0','9,9.9') FROM dual;
ERROR 1690 (22003): NUMBER value is out of range in 'to_number'

greatsql> set sql_mode=DEFAULT;

greatsql> select to_number('-\,0.0','9,9.9') FROM dual;
+-----------------------------+
| to_number('-\,0.0','9,9.9') |
+-----------------------------+
|                           0 |
+-----------------------------+  
```
