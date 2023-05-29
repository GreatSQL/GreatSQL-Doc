# SQL兼容性 - MONTHS_BETWEEN()函数
---
[toc]

## 1. 语法

```sql
MONTHS_BETWEEN(date1, date2)
```

## 2. 定义和用法
函数 `MONTHS_BETWEEN()` 的作用是计算日期 `date1` 和`date2` 之间相差的月份数，返回值类型要看具体情况，详见下方说明。

**1. 关于返回值是正数还是负数**
- 若 `date1` 晚于 `date2`，则返回正数；
- 若`date1`早于`date2`，则返回负数；
- 若 `date1` 与 `date2` 相同，则返回0。

**2. 关于返回值是正数还是小数**
- 若 `date1` 和 `date2` 中的日期数值相同（如：`'2021-04-13'`和`'2021-03-13'`）或均为各自月份的最后一天（如：`'2021-02-28'`和`'2021-03-31'`），则返回结果为整数；
- 其余情况数据库会以31天为分母，并根据`date1`和`date2`里的天数差(小于31天)计算结果中的小数部分。

## 3. SQL兼容说明

- 函数 `MONTHS_BETWEEN()` 的输入参数支持字符串格式，GreatSQL会将其自动转换为 `DATE`/`DATETIME` 类型后再进行日期计算，但需保证输入的字串能被转成正确的日期类型，否则会因日期转换错误返回NULL，并提示warning，因输入不合法信息导致与Oracle结果显示不一致的问题时，目前暂不做处理。

**注**：合法的日期字串应至少包含完整的日期部分（年、月、日），时间部分（时、分、秒）为可选项；当指定的时间部分时，也应包含完整的时分秒的值。合法的格式如下面几种：
- `YYMMDD`，'230518'
- `YYYYMMDD`，'20230518'
- `YYMMDDHHmmss`，'230518095050'
- `YYYYMMDDHHmmss`，'20230518095050'
- `YY-MM-DD`，'23-05-18'
- `YYYY-MM-DD`，'2023-05-18'
- `YYYY-MM-DD HH`，'2023-05-18 09'
- `YYYY-MM-DD HH:mm`，'2023-05-18 09:50'
- `YY-MM-DD HH:mm:ss`，'23-05-18 09:50:50'

而类似下面这几种则是非法格式，无法被解析：
- `YYYYMMDDHH`，'2022020203'
- `YYYYMM`，'202102'

```sql
-- 参数日期格式不合法，不能解析，返回NULL
greatsql> SELECT MONTHS_BETWEEN('2022022823', '20220224') FROM dual;
+-----------------------------------------+
| MONTHS_BETWEEN('2022022823','20220224') |
+-----------------------------------------+
|                                    NULL |
+-----------------------------------------+
1 row in set, 1 warning (0.00 sec)

greatsql> show warnings;
+---------+------+----------------------------------------+
| Level   | Code | Message                                |
+---------+------+----------------------------------------+
| Warning | 1292 | Incorrect datetime value: '2022022823' |
+---------+------+----------------------------------------+
```

## 4. 示例

```sql
greatsql> select months_between(to_date('2021-3-21', 'yyyy-mm-dd'), to_date('2021-1-10', 'yyyy-mm-dd')) as MT1 from dual
 union all
 select months_between('2021-3-21', '2021-1-10') from dual;
+--------------------+
| MT1                |
+--------------------+
| 2.3548387096774195 |
| 2.3548387096774195 |
+--------------------+

greatsql> select months_between(to_date('2021-1-10', 'yyyy-mm-dd'), to_date('2021-3-21', 'yyyy-mm-dd')) as MT2 from dual 
 union all
 select months_between( '2021-1-10', '2021-3-21' );
+---------------------+
| MT2                 |
+---------------------+
| -2.3548387096774195 |
| -2.3548387096774195 |
+---------------------+
```

**注意**：函数 `MONTHS_BETWEEN()` 使用相关注意事项可参考[函数 `TO_DATE()` 中的规则](https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/relnotes/greatsql-803224/sql-compat-func-todate.md)。
