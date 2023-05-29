# mysqldump备份加密

[toc]

GreatSQL 8.0.32-24支持在mysqldump进行逻辑备份时产生加密备份文件，并且也支持对加密后的备份文件解密导入。

下面是具体使用方法。

首先，用openssl生成密钥文件：
```
# 利用随机函数生成明文密码串
$ echo $RANDOM | sha256sum | awk '{print $1}' > /data/backup/dumpkey.txt

# 利用openssl加密，生成密钥文件
$ openssl enc -aes-256-cbc -K 215869594 -iv 1814916769 -in /data/backup/dumpkey.txt -out /data/backup/dumpkey.enc
```
**注意**：个别时候生成的密钥文件在后面备份加密指定时可能无法使用，会报错：`Invalid encrypt key file.`，这时只要换个明文密码，重新生成一次即可（重新执行上述两个步骤的工作即可）。

加密导出
```
# 执行逻辑备份，并设置加密
$ mysqldump --encrypt=aes-256-cbc --encrypt-key-file=/data/backup/dumpkey.enc --encrypt-iv=2132180222132180 -B test > /data/backup/test-enc.sql
```
这就完成逻辑备份并将其加密。

**备注**：
- `--encrypt` 为加解密算法。
- `--encrypt-key-file` 为秘钥文件。
- `--encrypt-iv` 为初始化向量，部分加密算法不需要会忽略该选项，该参数必须是16位长度。

如果有需要，可以将导出文件进行解密以查看备份文件内容：
```
# 解密导出文件
$ mysqldump --decrypt=aes-256-cbc --decrypt-key-file=/data/backup/dumpkey.enc --decrypt-iv=2132180222132180 --decrypt-file=/data/backup/test-enc.sql > /data/backup/test.sql
```

也可以在mysql客户端中，直接将加密文件导入（导入的过程中同时解密）：
```
$ mysql -e "source_decrypt decrypt-mode aes-256-cbc decrypt-key-file /data/backup/dumpkey.enc decrypt-iv 2132180222132180 decrypt-file /data/backup/test-enc.sql"
```

**备注**：
其中 `--decrypt` 为加解密算法，`--decrypt-key-file` 为秘钥文件，`--decrypt-iv` 为初始化向量，部分加密算法不需要会忽略该选项。

**使用帮助**
更多 `mysqldump` 加解密相关参数可以加上 `--help` 查看，有以下几个：
```
$ ./bin/mysqldump --help | grep -i cryp
  --encrypt=name      Encrypt mysqldump mode .
  --encrypt-key=name  Encrypt mysqldump key.
  --encrypt-iv=name   Encrypt mysqldump iv.
  --encrypt-key-file=name
                      Encrypt mysqldump key file.
  --decrypt=name      Decrypt mysqldump mode.
  --decrypt-key=name  Decrypt mysqldump key.
  --decrypt-iv=name   Decrypt mysqldump iv.
  --decrypt-key-file=name
                      Decrypt mysqldump key file.
  --decrypt-file=name Decrypt mysqldump file.
```
参数名及作用都比较好理解。
