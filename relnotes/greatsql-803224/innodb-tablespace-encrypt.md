# 表空间国密加密

[toc]

## 1. 编译安装BabaSSL

编译安装BabaSSL以支持国密算法。

**提示：** BabaSSL现已改名为铜锁（Tongsuo），项目仓库地址： https://github.com/Tongsuo-Project/Tongsuo 。

铜锁/Tongsuo是一个提供现代密码学算法和安全通信协议的开源基础密码库，为存储、网络、密钥管理、隐私计算等诸多业务场景提供底层的密码学基础能力，实现数据在传输、使用、存储等过程中的私密性、完整性和可认证性，为数据生命周期中的隐私和安全提供保护能力。

```
# 下载源码，编译安装
$ wget https://github.com/Tongsuo-Project/Tongsuo/releases/download/8.3.2/BabaSSL-8.3.2.tar.gz
$ tar zxf BabaSSL-8.3.2.tar.gz
$ cd Tongsuo-8.3.2
$ mkdir bld; cd bld; ../config; make; make install

# 修改 /etc/profile
$ vim /etc/profile
export LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH

# 退出当前session，重新ssh登入，确认BabaSSL已被启用
$ openssl version
BabaSSL 8.3.2
OpenSSL 1.1.1h  22 Sep 2020

# 确认支持国密算法
# 注意到有SM3、SM4字样即可
$ openssl ciphers|grep SM
TLS_AES_256_GCM_SHA384:TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256:TLS_SM4_GCM_SM3:TLS_SM4_CCM_SM3... 
```

## 2. 修改GreatSQL相关设置，启用国密支持
修改 my.cnf 配置文件，增加以下国密支持选项：
```
#enable openssl & SM
require_secure_transport = ON
tls_ciphersuites = "TLS_SM4_GCM_SM3:TLS_SM4_CCM_SM3"
tls_version = 'TLSv1.3'
```

如果是采用 systemd 启动GreatSQL，则修改服务文件：
```
$ vim /lib/systemd/system/greatsql.service
...
Environment=LD_LIBRARY_PATH=/usr/local/lib64
```

如果是直接在命令行下手动方式启动GreatSQL，则确保BabaSSL已经启用的情况下，再次重启GreatSQL服务。

## 3. 登入测试
再次登入GreatSQL，确认国密支持已生效：
```
# 用tcp协议登入，确认国密算法生效
$ mysql -hxx -uxx -pxx --protocol=tcp -P3306
greatsql> \s
...
SSL:                    Cipher in use is TLS_SM4_GCM_SM3

# 确认相关配置选项正确性
greatsql> select * from performance_schema.global_variables where variable_name in ('require_secure_transport', 'tls_ciphersuites', 'tls_version');
+--------------------------+---------------------------------+
| VARIABLE_NAME            | VARIABLE_VALUE                  |
+--------------------------+---------------------------------+
| require_secure_transport | ON                              |
| tls_ciphersuites         | TLS_SM4_GCM_SM3:TLS_SM4_CCM_SM3 |
| tls_version              | TLSv1.3                         |
+--------------------------+---------------------------------+
```

## 4. 采用国密算法加密表空间
在开始对数据库对象设置加密之前，要先生成一份master keyring file。

新建一个专用于存储GreatSQL master keyring file 的目录（注意：不能放在 datadir 目录下），并修改相应的属主及权限模式：
```
# datadir是 /data/GreatSQL，要区分开
$ mkdir /opt/GreatSQL/keyring
$ chown -R mysql:mysql /opt/GreatSQL/keyring
$ chmod -R 750 /opt/GreatSQL/keyring
```

修改 my.cnf，配置相关选项：
```
loose-plugin-load=keyring_file.so
keyring_file_data=/opt/GreatSQL/keyring/master_keyring
```

也可以在线执行下面的命令启用keyring_file plugin：
```
greatsql> INSTALL PLUGIN keyring_file soname 'keyring_file.so';
```
重启GreatSQL，确认这个plugin已启用，并且相关选项也是生效的：
```
greatsql> select * from information_schema.PLUGINS where plugin_name = 'keyring_file'\G
*************************** 1. row ***************************
           PLUGIN_NAME: keyring_file
        PLUGIN_VERSION: 1.0
         PLUGIN_STATUS: ACTIVE
           PLUGIN_TYPE: KEYRING
   PLUGIN_TYPE_VERSION: 1.1
        PLUGIN_LIBRARY: keyring_file.so
PLUGIN_LIBRARY_VERSION: 1.10
         PLUGIN_AUTHOR: Oracle Corporation
    PLUGIN_DESCRIPTION: store/fetch authentication data to/from a flat file
        PLUGIN_LICENSE: GPL
           LOAD_OPTION: ON
           
greatsql> select * from performance_schema.global_variables where variable_name in ('keyring_file_data');
+-------------------+--------------------------------------+
| VARIABLE_NAME     | VARIABLE_VALUE                       |
+-------------------+--------------------------------------+
| keyring_file_data | /opt/GreatSQL/keyring/master_keyring |
+-------------------+--------------------------------------+
```
刚初始化时的master key还是个空文件，需要重新生成一份：
```
greatsql> system ls -la /opt/GreatSQL/keyring/master_keyring
-rw-r----- 1 mysql mysql 0 Apr 21 16:35 /opt/GreatSQL/keyring/master_keyring

# 更新master key
greatsql> ALTER INSTANCE ROTATE INNODB MASTER KEY;

greatsql> system ls -la /opt/GreatSQL/keyring/master_keyring
-rw-r----- 1 mysql mysql 187 Apr 21 16:36 /opt/GreatSQL/keyring/master_keyring
```

接下来就可以对多种数据库对象（库、表、表空间）设置是否加密。
```
-- 设置该库下新建的表默认加密
greatsql> alter database test encryption = 'Y';

greatsql> show create database test\G
*************************** 1. row ***************************
       Database: test
Create Database: CREATE DATABASE `test` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='Y' */

greatsql> create table t1(id int primary key) ENCRYPTION=‘Y';

greatsql> show create table t1\G
*************************** 1. row ***************************
       Table: t2
Create Table: CREATE TABLE `t2` (
  `id` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ENCRYPTION=‘Y’

greatsql> alter table t1 ENCRYPTION=’N’;  -- 取消加密
```
**注意：** keyring文件需要做好备份，万一不慎被删除、修改或移走，都会导致被加密的数据库对象无法被正确读取，这时就可以将备份文件恢复回去。

## 5. 查看元数据
可以在 `performance_schema` 和 `information_schema` 中查看加密相关元数据信息：

```
-- 查看当前的master key
greatsql> SELECT * FROM performance_schema.keyring_keys;
+--------------------------------------------------+-----------+----------------+
| KEY_ID                                           | KEY_OWNER | BACKEND_KEY_ID |
+--------------------------------------------------+-----------+----------------+
| INNODBKey-c72ac980-7612-11ed-bd22-00155d064000-3 |           |                |
+--------------------------------------------------+-----------+----------------+

-- 查看都有哪些表空间文件被加密
greatsql> SELECT SPACE, NAME, SPACE_TYPE, ENCRYPTION FROM INFORMATION_SCHEMA.INNODB_TABLESPACES WHERE ENCRYPTION=‘Y';
+-------+---------+------------+------------+
| SPACE | NAME    | SPACE_TYPE | ENCRYPTION |
+-------+---------+------------+------------+
|     6 | test/t1 | Single     | Y          |
+-------+---------+------------+------------+

-- 查看有哪些表被加密
greatsql> SELECT TABLE_SCHEMA, TABLE_NAME, CREATE_OPTIONS FROM INFORMATION_SCHEMA.TABLES  WHERE CREATE_OPTIONS LIKE '%ENCRYPTION%'; -- table
+--------------+------------+----------------+
| TABLE_SCHEMA | TABLE_NAME | CREATE_OPTIONS |
+--------------+------------+----------------+
| test         | t1         | ENCRYPTION='Y' |
+--------------+------------+----------------+

-- 查看哪些库被加密
SELECT SCHEMA_NAME, DEFAULT_ENCRYPTION FROM INFORMATION_SCHEMA.SCHEMATA   WHERE DEFAULT_ENCRYPTION='YES';
+-------------+--------------------+
| SCHEMA_NAME | DEFAULT_ENCRYPTION |
+-------------+--------------------+
| test        | YES                |
+-------------+--------------------+
```

更多详情请见MySQL文档：
- https://dev.mysql.com/doc/refman/8.0/en/keyring.html
- https://dev.mysql.com/doc/refman/8.0/en/innodb-data-encryption.html
