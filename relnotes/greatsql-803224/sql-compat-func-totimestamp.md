# SQL兼容性 - TO_TIMESTAMP()函数
---
[toc]
## 1. 语法

```
TO_TIMESTAMP(string , fmt)
```

## 2. 定义和用法

函数 `TO_TIMESTAMP()` 的作用是将字符串类型数据 `string` 转换为日期(时间)格式类型，`fmt`用于指定`string`的日期模型。

参数 `fmt` 支持的日期模型如下表所示：

| 格式     | 描述 | 示例或说明 |
| -------- | ---------------------------------------------------------- | ---------------------------------------------------------- |
| YYYY/RRRR               | 4-digit year                                                                                       | 2021                                                                                                                                                                                                                                                                                                                                                                               |
| YYY                     | 3-digit year                                                                                       | 021                                                                                                                                                                                                                                                                                                                                                                                |
| YY                      | 2-digit year                                                                                       | 21                                                                                                                                                                                                                                                                                                                                                                                 |
| RR                      | 2-digit year                                                                                       | 与YY类似，但会因指定的年号与当前年份的后两位数字返回不同的值：<br/>- 当前年份后两位为[00,49]:<br/>  'RR'对应年号在[00,49], 返回年号前两位数值与当前年份相同<br/>  'RR'对应年号在[50,99], 返回年号前两位数值比当前年份小1<br/>- 当前年份后两位为[50,99]:<br/>  'RR'对应年号在[00,49], 返回年号前两位数值比当前年份大1<br/>  'RR'对应年号在[50,99], 返回年号前两位数值与当前年份相同 |
| Y| 1-digit year| 1|
| DD| Day of month (1-31)||
| HH, HH12| Hour of day (1-12).||
| HH24| Hour of day (0-23).||
| MI| Minute that ranges from 0 to 59||
| MM| Month that ranges from 01 through 12, where January is 01.||
| MON| Abbreviated name of the month.| JAN,FEB|
| MONTH| Name of the month.| JANUARY|
| SS| Second (0-59).||
| AM| Meridian indicator with or without periods.| 格式与PM等价，最后的date值取决于第一个参数字串中对应位置值|
| PM| Meridian indicator with or without periods.| 格式与AM等价，最后的date值取决于第一个参数字串中对应位置值|
| FF[1-6]| Fractional seconds||
| D| Day of week (1-7). This element depends on the NLS territory of the session.||
| DDD| Day of year (1-366).||
| `-` `/` `,` `.` `;` `:` | Punctuation is reproduced in the result.                                                           | Any non-alphanumeric character is allowed to match the punctuation characters in the format model.|
| SSSSS| Seconds past midnight (0-86399).||
| J| Julian day; the number of days since January 1, 4712 BC. Number specified with J must be integers. | GreatSQL 只支持 0001-01-01 ~ 9999-12-31 之间的 Julian day，即范围为：[1721424, 5373484]|
| X| Local radix character.| 'HH:MI:SSXFF'|
| Y,YYY| Year with comma in this position.| 2,023|
| RM| Roman numeral month (I-XII; January = I).||
| TH| Ordinal Number| DDTH|
| FM| Fill mode.||
| FX| Format exact.||


函数返回结果说明：

- 参数 `fmt` 中指定日期格式，`string` 被成功解析后，将返回一个带日期的timestamp值(日期+时间，如：`2023-01-01 00:00:00.00000`)
- 当无法根据 `fmt` 从 `string` 中获取合法日期时间值时，将返回NULL。
- 返回的 `timestamp` 值，微秒部分长度为6位，微秒部分的值根据FF指示器来确定，具体示例如下：

| TO_TIMESTAMP() 输入 | 说明 | 输出结果 |
| ------------------------------------------------------------ | -------------------------------------------- | ------------------------------------------------------------ |
| TO_TIMESTAMP('11:00:00.123456', 'HH:Mi:SS') | 未指定FF格式，微秒部分全部置零 | NULL |
| TO_TIMESTAMP('11:00:00.123456', 'HH:Mi:SS.ff') | 指定FF但未指定位数，默认保留全部6位微秒 | 2023-05-01 11:00:00.123456 |
| TO_TIMESTAMP('11:00:00.123456', 'HH:Mi:SS.ff6') | 指定FF并指定位数为6，正确解析 | 2023-05-01 11:00:00.123456 |
| TO_TIMESTAMP('11:00:00.123456', 'HH:Mi:SS.ff2') | 指定FF并指定位数为2，但微秒部分有6位，解析失败 | NULL |
| TO_TIMESTAMP('11:00:00.123456', 'HH:Mi:SS.ff0')<br/><br/>TO_TIMESTAMP('11:00:00.123456', 'HH:Mi:SS.ff7') | 指定FF但位数指示器超出合法范围(1~6),提示错误 | ERROR 1525 (HY000): Incorrect string value: 'please check the format string' |

## 3. SQL兼容说明

- 对指定格式包含HH或HH12时，GreatSQL与Oracle在显示12点时，返回值不同。如下例所示：

| TO_TIMESTAMP()输入| Oracle返回| GreatSQL返回|
| ------------- | ----------------------- | ------------ |
| TO_TIMESTAMP('12','HH12') | 2023-09-01 12:00:00.000000000 | 2023-05-01 00:00:00.000000 |
| TO_TIMESTAMP('12','HH')   | 2023-09-01 12:00:00.000000000 | 2023-05-01 00:00:00.000000 |

- 微秒部分不同：Oracle返回值微秒部分为9位，GreatSQL为6位。

| TO_TIMESTAMP()输入| Oracle返回| GreatSQL返回 |
| -------------------------------------- | ------------------ | ---------------------------------------------------------------------------- |
| TO_TIMESTAMP('11:00:00.123456', 'HH:Mi:SS.ff')     | 11.00.00.123456000 | 2023-05-01 11:00:00.123456 |
| TO_TIMESTAMP('11:00:00.123456', 'HH:Mi:SS.ff6')    | 11.00.00.123456    | 2023-05-01 11:00:00.123456 |
| TO_TIMESTAMP('11:00:00.123456789', 'HH:Mi:SS.ff9') | 11.00.00.123456789 | ERROR 1525 (HY000): Incorrect string value: 'please check the format string' |

- 格式支持不同：Oracle的YY格式可以读取2位/3位/4位年份数字，GreatSQL只能读取2位年份数字。二者差异示例如下：

| TO_TIMESTAMP()输入| Oracle返回| GreatSQL返回 |
| --------------------- | ----------------------------------------- | ----------- |
| TO_TIMESTAMP('20121018', 'YYMMDD')    | 2012-10-18 | NULL        |
| TO_TIMESTAMP('2012-10-18','YY-MM-DD') | 2012-10-18 | NULL        |
| TO_TIMESTAMP('20121018', 'RRMMDD')    | 2012-10-18 | NULL        |
| TO_TIMESTAMP('012-10-18','RR-MM-DD')  | 2012-10-18 | NULL        |
| TO_TIMESTAMP('12-10-18','YY-MM-DD')   | 2012-10-18 | 2012-10-18 00:00:00.000000  |

## 4. 示例

```sql
greatsql> select to_timestamp('2003-01-02 10:11:12 PM', 'YYYY-MM-DD HH12:MI:SS PM') from dual;
+--------------------------------------------------------------------+
| to_timestamp('2003-01-02 10:11:12 PM', 'YYYY-MM-DD HH12:MI:SS PM') |
+--------------------------------------------------------------------+
| 2003-01-02 22:11:12.000000                                         |
+--------------------------------------------------------------------+

greatsql> select to_timestamp('03-01-02 8:11:2.123456', 'YY-MM-DD HH24:MI:SS.FF') from dual;
+-------------------------------------------------------------------+
| to_timestamp('03-01-02 8:11:2.123456', 'YY-MM-DD HH24:MI:SS.FF3') |
+-------------------------------------------------------------------+
| 2003-01-02 08:11:02.123000                                        |
+-------------------------------------------------------------------+
```
