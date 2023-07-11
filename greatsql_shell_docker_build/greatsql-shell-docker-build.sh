#!/bin/bash
##
## 自动构建GreatSQL Docker编译环境
##
## 文档：https://gitee.com/GreatSQL/GreatSQL-Doc/blob/master/user-manual/4-install-guide/4-6-install-with-source-code.md
##

docker build -t greatsql_shell_build_env .

mysql_src_dir=$1
shell_src_dir=$2
boost_src_dir=$3

mysql_basename=$(basename $mysql_src_dir)
shell_basename=$(basename $shell_src_dir)
boost_basename=$(basename $boost_src_dir)

if [ $? -ne 0 ];then
  echo "Docker build error!"
else 
  echo "Docker build success!you can run it:

docker run -d \\
-v $mysql_src_dir:/opt/${mysql_basename} \\
-v $shell_src_dir:/opt/${shell_basename} \\
-v $boost_src_dir:/opt/${boost_basename} \\
--name greatsql_shell_build_env greatsql_shell_build_env"
fi
