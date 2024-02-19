# greatsql_docker_build

2024.2.19更新：

本项目将不再维护，请移步[https://gitee.com/GreatSQL/GreatSQL-Docker/tree/master/GreatSQL-Build](https://gitee.com/GreatSQL/GreatSQL-Docker/tree/master/GreatSQL-Build)，建议改用该项目，谢谢。

如何利用Docker环境快速编译GreatSQL二进制包，详情参考：[编译源码安装](https://greatsql.cn/docs/8032-25/user-manual/4-install-guide/6-install-with-source-code.html)。

相关文件介绍：
- Dockerfile，用于构建docker编译环境
- Dockerfiles，目录下包含了CentOS 7 & CentOS8以及x86_64 & aarch64不同平台下的Dockerfile参考文件
- greatsql-automake.sh，用于实现自动化编译的脚本
- greatsql-docker-build.sh，用于自动构建GreatSQL Docker编译环境的脚本
