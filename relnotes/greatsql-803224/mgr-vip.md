# MGR内置动态VIP

[toc]

## 启用内置vip插件
- 开启新插件
```
plugin_load_add=greatsql_ha.so
```

或者在启动数据库实例后， 执行
```
install plugin greatsql_ha soname 'greatsql_ha.so';
```

## 新增配置参数
- 配置开启内置vip功能
```
loose-greatsql_ha_enable_mgr_vip = 1
```
- 配置vip
```
loose-greatsql_ha_mgr_vip_ip = 172.17.140.1
```
- 配置要绑定的网卡名，插件会将vip绑定到MGR主所在机器的指定网卡上，比如配置为eth0，为了防止网卡原有的ip被覆盖，实际绑定后，会绑定在名为eth0:0的网卡上
```
loose-greatsql_ha_mgr_vip_nic = 'eth0'
```
- 配置掩码
```
loose-greatsql_ha_mgr_vip_mask = '255.255.255.0'
```
- 目前只支持在单主模式下才能启用内置vip特性，所以还需要设置下面参数：
```
loose-group_replication_single_primary_mode= TRUE
loose-group_replication_enforce_update_everywhere_checks= FALSE
```
- 上述参数如果没有配置，或者配置格式不对时，内置vip功能会失效（目前没有格式检查报错的功能）。
- 除了上述新增参数，其他MGR相关参数按照常规单主MGR配置要求即可。
- 上述参数支持在线动态修改。

上述配置说明的完整示例如下（MGR组内每个实例都需要配置）：
```
[mysqld]
#GreatSQL MGR vip
plugin-load-add=greatsql_ha.so
loose-greatsql_ha_enable_mgr_vip=1
loose-greatsql_ha_mgr_vip_ip =172.17.140.1
loose-greatsql_ha_mgr_vip_mask=255.255.240.0
loose-greatsql_ha_mgr_vip_nic=eth0

#single-primary mode
loose-group_replication_single_primary_mode=1
loose-group_replication_enforce_update_everywhere_checks=0
```

当MGR Primary节点上绑定的vip被手动删除或者出现异常配置导致vip绑定行为不对时，可以通过在MGR Primary节点上执行 `set global greatsql_ha_force_change_mgr_vip = on` 命令去重新获取MGR拓扑结构，从而重新绑定vip，该命令执行之后，参数  `greatsql_ha_force_change_mgr_vip` 值仍然为off，这个是符合预期的行为。

## 启动说明
配置VIP需要相关内核权限，获取相关权限有两种方式，以下二选一即可（推荐采用方法二）：

1. 给mysqld进程的启动用户，例如是mysql用户，设置root权限。
2. 【推荐方法】通过setcap命令为mysqld二进制文件添加 `CAP_NET_ADMIN` 和 `CAP_NET_RAW` 的capability。具体命令如下：
```shell
#执行该命令需要sudo权限或root
$ setcap CAP_NET_ADMIN,CAP_NET_RAW+ep path_to_greatsql/bin/mysqld
```
**注意**
- 建议采用 `systemd` 方式管理GreatSQL服务，或者对启动用户用户（如 mysql）开启sudo权限，利用sudo调用 `systemd` 再启动GreatSQL服务，这样能确保mysqld进程可获得内核权限，成功绑定VIP。
- 当 `setcap` 命令为mysqld二进制文件添加capability以后，需要保证登录系统的用户和启动mysqld的用户保持一致，才能确保mysqld进程可获得内核权限。例如：用root用户登录系统，然后再以普通用户（mysql）启动mysqld进程，setcap无法生效，绑定vip时会失败报错。
