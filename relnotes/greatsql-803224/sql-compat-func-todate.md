# SQL兼容性 - TO_DATE()函数
---
[toc]
## 1. 语法

```
TO_DATE(string , fmt)
```

## 2. 定义和用法

`TO_DATE()`函数用于将字符串类型数据 `string`, 转换为日期(时间)格式类型，`fmt` 用于指定 `string` 的日期模型。

当前 `fmt` 日期模型支持说明：

| 格式     | 描述                                                       | 示例或说明                                                 |
| -------- | ---------------------------------------------------------- | ---------------------------------------------------------- |
| YYYY/RRRR | 4-digit year | 2023 |
| YYY | 3-digit year | 023 |
| YY | 2-digit year | 23 |
| RR | 2-digit year | 与YY类似，但会因指定的年号与当前年份的后两位数字返回不同的值：<br/>- 当前年份后两位为[00,49]:<br/>  'RR'对应年号在[00,49], 返回年号前两位数值与当前年份相同<br/>  'RR'对应年号在[50,99], 返回年号前两位数值比当前年份小1<br/>- 当前年份后两位为[50,99]:<br/>  'RR'对应年号在[00,49], 返回年号前两位数值比当前年份大1<br/>  'RR'对应年号在[50,99], 返回年号前两位数值与当前年份相同 |
| Y | 1-digit year | 1 |
| DD | Day of month (1-31) | |
| HH, HH12 | Hour of day (1-12). | |
| HH24 | Hour of day (0-23). | |
| MI | Minute that ranges from 0 to 59 | |
| MM | Month that ranges from 01 through 12, where January is 01. | |
| MON | Abbreviated name of the month. | JAN,FEB |
| MONTH | Name of the month. | JANUARY |
| SS | Second (0-59). | |
| AM/A.M. | Meridian indicator with or without periods. | 格式与PM等价，最后的date值取决于第一个参数字串中对应位置值 |
| PM/P.M. | Meridian indicator with or without periods. | 格式与AM等价，最后的date值取决于第一个参数字串中对应位置值 |
| D | Day of week (1-7). This element depends on the NLS territory of the session. | |
| DDD | Day of year (1-366). | |
| `-` `/` `,` `.` `;` `:` | Punctuation is reproduced in the result.                                                           | Any non-alphanumeric character is allowed to match the punctuation characters in the format model. |
| SSSSS | Seconds past midnight (0-86399). | |
| J | Julian day; the number of days since January 1, 4712 BC. Number specified with J must be integers. | GreatSQL 只支持 0001-01-01 ~ 9999-12-31 之间的 Julian day，即范围为：[1721424, 5373484] |
| X | Local radix character. | 'HH:MI:SSXFF' |
| Y,YYY | Year with comma in this position. | 2,023 |
| RM | Roman numeral month (I-XII; January = I). | |
| TH | Ordinal Number | DDTH |
| FM | Fill mode. | |
| FX | Format exact. | |

**输出说明：**

- 当`fmt` 同时指定日期或时间格式，`string` 被成功解析后，将返回一个 `DATETIME`值(日期+时间，如: `2023-01-01 00:00:00`)

- 未被指定的日期或时间部分，`TO_DATE()` 会为返回的`DATETIME`值对应部分赋予默认值。

|  日期或时间部分  | 默认值                                                 |
| ----------------------- | ------------------------------------------------------------ |
| year   | 本年(即'select now()' 所在年份) |
| month  | 本月(即'select now()' 所在月份) |
| day    | 每月1日 |
| hour   | 0 |
| minute | 0 |
| second | 0 |

**示例：**
| TO_DATE()输入 | 返回值                                                 |
| ----------------------- | ------------------------------------------------------------ |
| TO_DATE('2023', 'YYYY') | 2023-05-01 00:00:00 |
| TO_DATE('202310', 'YYYYMM') | 2023-10-01 00:00:00 |
| TO_DATE('11', 'HH')     | 2023-05-01 11:00:00 |

## 3. SQL兼容说明

- 对指定格式包含HH或HH12时，GreatSQL与Oracle在显示12点时，返回值不同。例如：

| TO_DATE()输入   | Oracle返回          | GreatSQL返回 |
| ------------- | ------------------- | ----------- |
| TO_DATE('12','HH12') | 2023-05-01 12:00:00 | 2023-05-01 00:00:00    |
| TO_DATE('12','HH')   | 2023-05-01 12:00:00 | 2023-05-01 00:00:00    |

- 在Oracle中，`YY/RR` 格式可以读取 2位/3位/4位 年份数字，而GreatSQL只能读取2位年份数字。

| TO_DATE()输入   | Oracle返回          | GreatSQL返回 |
| ------------------------- | ---------- | ----------- |
| TO_DATE('20121018', 'YYMMDD')    | 2012-10-18 | NULL        |
| TO_DATE('2012-10-18','YY-MM-DD') | 2012-10-18 | NULL        |
| TO_DATE('20121018', 'RRMMDD')    | 2012-10-18 | NULL        |
| TO_DATE('012-10-18','RR-MM-DD')  | 2012-10-18 | NULL        |
| TO_DATE('12-10-18','YY-MM-DD')   | 2012-10-18 | 2012-10-18 00:00:00  |


## 4. 示例

```sql
greatsql> select to_date('2003-01-02 10:11:12 PM', 'YYYY-MM-DD HH12:MI:SS PM') from dual;
+---------------------------------------------------------------+
| to_date('2003-01-02 10:11:12 PM', 'YYYY-MM-DD HH12:MI:SS PM') |
+---------------------------------------------------------------+
| 2003-01-02 22:11:12                                           |
+---------------------------------------------------------------+

greatsql> select to_date('03-01-02 8:11:2.123456', 'YY-MM-DD HH24:MI:SS') from dual;
+----------------------------------------------------------+
| to_date('03-01-02 8:11:2.123456', 'YY-MM-DD HH24:MI:SS') |
+----------------------------------------------------------+
| 2003-01-02 08:11:02                                      |
+----------------------------------------------------------+
1 row in set, 1 warning (0.00 sec)

greatsql> show warnings;
+---------+------+--------------------------------------------------------------+
| Level   | Code | Message                                                      |
+---------+------+--------------------------------------------------------------+
| Warning | 1292 | Truncated incorrect datetime value: '03-01-02 8:11:2.123456' |
+---------+------+--------------------------------------------------------------+

greatsql> SELECT TO_DATE('23:45:33','hh24:mi:ss');
+----------------------------------+
| TO_DATE('23:45:33','hh24:mi:ss') |
+----------------------------------+
| 2023-05-01 23:45:33              |
+----------------------------------+
```
