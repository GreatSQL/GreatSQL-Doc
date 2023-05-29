# SQL兼容性 - LENGTH()函数
---
[toc]
## 1. 语法
```
length(data)
```

## 2. 定义和用法
在Oracle中，`LENGTH()` 函数返回字符串的长度，而在MySQL中 `LENGTH()` 函数返回字符串的字节数。当参数data中字符串的长度为0时，MySQL返回值为0，而Oracle返回值为NULL。

针对上述差异，GreatSQL对 `LENGTH()` 函数做了扩展，以支持类似Oracle中的行为模式。

## 3. ORACLE兼容说明

因为MySQL已原生支持 `LENGTH()` 函数，因此想要在GreatSQL中使用扩展后的 `LENGTH()` 函数时，需要先执行 `set sql_mode=oracle;` 激活SQL兼容模式。

对于个别转义字符如 ‘‘\n’’，因为MySQL会将其自动转为特殊字符，因此最后结果是算作1个字符而不是2个字符。

对于表达式比如 `LENGTH(''+1)` ，目前oracle mode下支持数字转字符串，最后结果变成数值字符串的长度，这个动作与Oracle的不一致。

## 4. 示例

```
-- 在MySQL环境中，在utf8mb4字符集模式下，结果返回17
-- 示例中的每个中文字符占位3个字节，每个ASCII字符占位1个字节
greatsql> SELECT LENGTH( _UTF8MB4 'GreatSQL数据库');
+---------------------------------------+
| LENGTH( _UTF8MB4 'GreatSQL数据库')    |
+---------------------------------------+
|                                    17 |
+---------------------------------------+

-- 在GreatSQL中，先激活SQL兼容模式
greatsql> set sql_mode='oracle';

-- 示例中的每个中文字符和ASCII字符都算作一个字符
greatsql> SELECT LENGTH( _UTF8MB4 'GreatSQL数据库');
+---------------------------------------+
| LENGTH( _UTF8MB4 'GreatSQL数据库')    |
+---------------------------------------+
|                                    11 |
+---------------------------------------+
```
