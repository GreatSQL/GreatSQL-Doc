# CLONE备份加密

[toc]

GreatSQL 8.0.32-24支持在执行CLONE备份时加密备份文件，以及对加密后的备份文件解密。

## 1. CLONE备份加密
在执行clone前，先设置选项 `clone_encrypt_key_path` 开启加密功能。

```sql
greatsql> set global clone_encrypt_key_path= 'PATH/mysql_encrypt_key'
```
其中，`mysql_encrypt_key` 密钥文件的内容类似下面这样：
```
$ cat mysql_encrypt_key
aes-128-cbc
Jmfyvubtms66kIcHwHco8XeOYPA6GiQb86U
1234567890123456
```

该文件共有三行，分别为：
- 第一行，加密模式：`aes-128-cbc`，表示使用128位密钥长度和cbc模式进行加密。
- 第二行，密钥：`Jmfyvubtms66kIcHwHco8XeOYPA6GiQb86U`，允许的密钥长度为128、192和256，允许的模式值为ECB、CBC、CFB1、CFB8、CFB128和OFB。
- 第三行，加密向量：`1234567890123456`，要求长度为16位。

接下来就可以进行CLONE加密备份了。CLONE支持几种不同的备份模式：备份（远程实例 or 本地实例）数据到本地存储中，将远程实例数据备份并覆盖本地实例。

想要执行CLONE备份，需要先给运行的用户至少授予 `BACKUP_ADMIN` 权限，例如：
```sql
greatsql> CREATE USER bkuser IDENTIFIED BY 'bkuser';
greatsql> GRANT SELECT, BACKUP_ADMIN ON *.* TO bkuser;
```

如果要备份远程实例，还需要先设置好选项 `clone_valid_donor_list`（如果是将本地实例CLONE备份到本地存储中则不需要设置），例如：
```sql
greatsql> SET GLOBAL clone_valid_donor_list = '172.17.140.10:3306';
```

再设置密钥文件路径（要确保GreatSQL数据库进程有权限访问这个密钥文件）：
```sql
greatsql> SET GLOBAL clone_encrypt_key_path = '/data/backup/mysql_encrypt_key';
```

接下来就可以额执行CLONE备份了，例如：
```sql
-- 将本地实例备份到本地存储中
greatsql> CLONE LOCAL DATA DIRECTORY = '/data/backup/20230515';

-- 或者将远程实例备份到本地存储中
greatsql> CLONE INSTANCE FROM bkuser@172.17.140.10:3306 IDENTIFIED BY 'bkuser' DATA DIRECTORY = '/data/backup/20230515';
```

**特别提醒**：执行CLONE加密备份时，如果是将远程实例数据备份并覆盖本地实例的模式，那么接收实例中 `innodb_flush_method` 选项不要设置为 `O_DIRECT` 模式。因为在执行CLONE加密备份时，采用512字节加密（这样可以同时处理redo和ibd文件）一次并落盘，这时如果 `innodb_flush_method = O_DIRECT` 会极大增加刷盘的次数，导致备份耗时特别久。这时可以采用默认值即可。

查看加密备份文件：
```shell
# 进入数据备份目录
$ cd /data/backup/20230515

# 查看备份文件
$ ls -a
 .   '#clone'    ib_buffer_pool.xbcrypt  '#innodb_redo'   mysql.ibd.xbcrypt   sys_audit.ibd.xbcrypt   test               undo_002.xbcrypt
 ..   greatsql   ibdata1.xbcrypt          mysql           sys                 sys_mac.ibd.xbcrypt     undo_001.xbcrypt
```
可以看到，无论是用户表空间文件，还是MySQL系统表空间、redo log、undo log等文件，全部数据文件都加上了 ".xbcrypt" 后缀，都是加密后的文件。

## 2. 解密clone加密备份文件

执行CLONE加密备份存储到本地文件时，备份文件名都会带有 ".xbcrypt" 后缀，在将加密数据备份文件导入前，还需要先解密才行。

在GreatSQL中，新增一个文件名为 `mysqldecrypt` 的解密工具，可以用它来解密数据文件。

下面演示如何进行解密操作。

### 2.1 解密整个数据备份目录

把解密工作封装在小脚本中：
```shell
$ cat /data/backup/clone_decrypt_files.sh
# 调用 mysqldecrypt 工具解密整个目录
#!/bin/sh
export PATH=$PATH:/usr/local/GreatSQL-8.0.32-24-Linux-glibc2.28-x86_64/bin
cd /data/backup

# 先做一次全量备份
cp -rfp /data/backup/20230515 /data/backup/20230515-orig

cd /data/backup/20230515
mysqldecrypt --clone-decrypt \
 --clone-decrypt-key=/data/backup/mysql_encrypt_key \
 --clone-decrypt-dir=./ --remove-original=true
```
参数 `--remove-original=true` 的作用是在解密完成后，是否删除原有的加密文件，`true`表示删除，`false`表示保留。因为已经做了一次全量备份，所以可以放心删除。另外，该参数只针对解密整个数据目录时才生效，当解密单个文件时是不生效的。

### 2.2 解密单个加密表空间文件

有时候，只需要恢复单个表，而不需要恢复整个数据库，`mysqldecrypt` 支持只解密指定文件，可以满足这种需求。

同样地，把解密工作封装在小脚本中：
```shell
$ cat /data/backup/clone_decrypt_dir.sh
# 调用 mysqldecrypt 工具对加密文件逐个解密
#!/bin/sh
export PATH=$PATH:/usr/local/GreatSQL-8.0.32-24-Linux-glibc2.28-x86_64/bin
cd /data/backup

# 先做一次全量备份
cp -rfp /data/backup/20230515 /data/backup/20230515-orig

cd /data/backup/20230515
for f in `find . -iname "*\.xbcrypt"`
do
 mysqldecrypt --clone-decrypt \
 --clone-decrypt-key=/data/backup/mysql_encrypt_key \
 --clone-decrypt-file=$f > $(dirname $f)/$(basename $f .xbcrypt) && rm -f $f;
done
```

**注意**：在解密单个表空间文件时，指定参数 `--remove-original=true` 不生效，所以才在解密后，同时执行删除加密文件操作。在此之前，请务必确认是否需要先行做一次全量备份。

完成解密后，就可以继续进行数据恢复工作，可以对整个实例全量恢复，也可以只恢复某个数据表。

## 3. 使用帮助
更多 `mysqldecrypt` 参数可以加上 `--help` 查看，有以下几个：
- `--help`，查看帮助。
- `--clone-decrypt`，声明是否进行解密，可选项 FALSE|TRUE，默认值 FALSE。
- `--clone-decrypt-key`，设置密钥文件路径。
- `--clone-decrypt-file`，设置要解密的单个文件路径。
- `--clone-decrypt-dir`，设置要解密的备份文件目录。
- `--remove-original`，设置是否在完成解密后删除原文件，可选项 FALSE|TRUE，默认值 FALSE。
