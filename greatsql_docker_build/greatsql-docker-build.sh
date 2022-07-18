#!/bin/bash
##
## 自动构建GreatSQL Docker编译环境
##
## 文档：https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/user-manual/4-install-guide/4-6-install-with-source-code.md
##

docker build -t greatsql_build_env .

src_dir=$1

if [ $? -ne 0 ];then
  echo "Docker build error!"
else 
  echo "Docker build success!you can run it:

docker run -d -v $src_dir:/opt/greatsql-8.0.25-16 greatsql_build_env"
fi
