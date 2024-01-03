# greatsql_shell_docker_build

如何利用Docker环境快速编译MySQL Shell for GreatSQL二进制包，详情参考：[MySQL Shell 8.0.32 for GreatSQL编译安装](https://mp.weixin.qq.com/s/bB6ZvV6-yB83otLnv_oqrA)

相关文件介绍：
- Dockerfile，用于构建docker编译环境
- greatsql-shell-automake.sh，用于实现自动化编译的脚本
- greatsql-shell-docker-build.sh，用于自动构建Docker编译环境的脚本
- mysqlsh-for-greatsql-8.0.32.patch，需要对MySQL Shell打补丁，才能支持GreatSQL中特有的仲裁节点特性
