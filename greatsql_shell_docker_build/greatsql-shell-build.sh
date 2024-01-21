#!/bin/bash

. ~/.bash_profile
#set -e
#set -u
#set -x

OPT_DIR=/opt
MYSQL_VERSTION=8.0.32
RELEASE=25
GLIBC=`ldd --version | head -n 1 | awk '{print $NF}'`
ARCH=`uname -p`
OS=`grep '^ID=' /etc/os-release | sed 's/.*"\(.*\)".*/\1/ig'`
#OS=Linux
MYSQLSH_PKG_NAME=greatsql-shell-${MYSQL_VERSTION}-${RELEASE}-${OS}-glibc${GLIBC}-${ARCH}
BASE_DIR=${OPT_DIR}/${MYSQLSH_PKG_NAME}
BUILD_PKG="greatsql_shell_docker_build.tar" \
ANTLR_PKG="antlr4-4.10" \
BOOST_PKG="boost_1_77_0" \
MYSQL_PKG="mysql-8.0.32" \
MYSQLSH_PKG="mysql-shell-8.0.32-src" \
PATCHELF_PKG="patchelf-0.14.5" \
PROTOBUF_PKG="protobuf*-3.19.4" \
RPCSVC_PKG="rpcsvc-proto-1.4" \
MYSQLSH_PATCH="mysqlsh-for-greatsql-8.0.32.patch" \
MYSQLSH_MAKE="greatsql-shell-automake.sh"
JOBS=`lscpu | grep '^CPU(s)'|awk '{print $NF}'`
if [ ${JOBS} -ge 16 ] ; then
  JOBS=`expr ${JOBS} - 4`
else
  JOBS=`expr ${JOBS} - 1`
fi

#extract
echo "1. extracting tarballs"
cd ${OPT_DIR}
tar xf ${OPT_DIR}/${BUILD_PKG} -C ${OPT_DIR} && \
tar xf ${OPT_DIR}/${ANTLR_PKG}*z -C ${OPT_DIR} ; \
tar xf ${OPT_DIR}/${BOOST_PKG}*z -C ${OPT_DIR} ; \
tar xf ${OPT_DIR}/${MYSQL_PKG}*z -C ${OPT_DIR} ; \
tar xf ${OPT_DIR}/${MYSQLSH_PKG}*z -C ${OPT_DIR} ; \
tar xf ${OPT_DIR}/${PATCHELF_PKG}*z -C ${OPT_DIR} ; \
tar xf ${OPT_DIR}/${PROTOBUF_PKG}*z -C ${OPT_DIR} ; \
tar xf ${OPT_DIR}/${RPCSVC_PKG}*z -C ${OPT_DIR} ; \

#antlr4
echo "2. compiling antlr4"
cd ${OPT_DIR}/${ANTLR_PKG}/runtime/Cpp/bld && \
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local/antlr4 > /dev/null 2>&1 && \
make -j${JOBS} > /dev/null 2>&1 && make -j${JOBS} install > /dev/null 2>&1

#patchelf
echo "3. compiling antlr4"
cd ${OPT_DIR}/${PATCHELF_PKG} && ./bootstrap.sh > /dev/null 2>&1 && ./configure > /dev/null 2>&1 && make -j${JOBS} > /dev/null 2>&1 && make -j${JOBS} install > /dev/null 2>&1

#rpcsvc-proto
echo "4. compiling rpcsvc-proto"
cd ${OPT_DIR}/${RPCSVC_PKG} && ./configure > /dev/null 2>&1 && make -j${JOBS} > /dev/null 2>&1 && make -j${JOBS} install > /dev/null 2>&1 ; \

#protobuf
echo "5. compiling protobuf"
cd ${OPT_DIR}/${PROTOBUF_PKG} && ./configure > /dev/null 2>&1 && make -j${JOBS} > /dev/null 2>&1 && make -j${JOBS} install > /dev/null 2>&1 ; \

echo "6. compiling mysql shell"
cd ${OPT_DIR}/${MYSQL_PKG} && \
rm -fr bld && \
mkdir bld && \
cd bld && \
cmake .. -DBOOST_INCLUDE_DIR=${OPT_DIR}/${BOOST_PKG} \
-DLOCAL_BOOST_DIR=${OPT_DIR}/${BOOST_PKG} \
-DWITH_SSL=system > /dev/null 2>&1 && \
cmake --build . --target mysqlclient -- -j${JOBS} > /dev/null 2>&1 ; \
cmake --build . --target mysqlxclient -- -j${JOBS} > /dev/null 2>&1 && \
cd ${OPT_DIR}/${MYSQLSH_PKG} && \
patch -p1 -f < ${OPT_DIR}/${MYSQLSH_PATCH} > /dev/null 2>&1 && \
rm -fr bld && \
mkdir bld && \
cd bld && \
cmake .. \
-DCMAKE_INSTALL_PREFIX=${BASE_DIR} \
-DMYSQL_SOURCE_DIR=${OPT_DIR}/${MYSQL_PKG} \
-DMYSQL_BUILD_DIR=${OPT_DIR}/${MYSQL_PKG}/bld/ \
-DHAVE_PYTHON=1 \
-DWITH_PROTOBUF=bundled \
-DBUILD_SOURCE_PACKAGE=0 \
-DBUNDLED_ANTLR_DIR=/usr/local/antlr4/ \
-DPYTHON_LIBRARIES=/usr/lib64/python3.8 -DPYTHON_INCLUDE_DIRS=/usr/include/python3.8/ > /dev/null 2>&1 \
&& make -j${JOBS} > /dev/null 2>&1 && make -j${JOBS} install > /dev/null 2>&1 && \
cp /usr/local/lib/libprotobuf.so.30 ${BASE_DIR}/lib/mysqlsh/ && \
pip3.8 install --user certifi > /dev/null 2>&1 ; \
${BASE_DIR}/bin/mysqlsh --version ; \
cd ${OPT_DIR} ; tar cf ${MYSQLSH_PKG_NAME}.tar ${MYSQLSH_PKG_NAME}; xz -9 -f ${MYSQLSH_PKG_NAME}.tar

echo "7. MySQL Shell for GreatSQL 8.0.32-25 build completed! TARBALL is: "
ls -la ${MYSQLSH_PKG_NAME}.tar.xz
cd ${OPT_DIR} && rm -fr ${ANTLR_PKG}* ${BOOST_PKG}* ${MYSQL_PKG}* ${MYSQLSH_PKG}* \
${MYSQLSH_PATCH} ${PATCHELF_PKG}* ${PROTOBUF_PKG}* ${RPCSVC_PKG}* 
/bin/bash
