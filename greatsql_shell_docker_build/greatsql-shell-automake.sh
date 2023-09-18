#!/bin/bash
MAJOR_VERSION=8
MINOR_VERSION=0
PATCH_VERSION=32
GLIBC=`ldd --version | head -n 1 | awk '{print $NF}'`
ARCH=`uname -p`
OS=`grep '^ID=' /etc/os-release | sed 's/.*"\(.*\)".*/\1/ig'`
#OS=Linux
PKG_NAME=greatsql-mysql-shell-${MAJOR_VERSION}.${MINOR_VERSION}.${PATCH_VERSION}-${OS}-glibc${GLIBC}-${ARCH}
BASE_DIR=/usr/local/${PKG_NAME}
BOOST_VERSION=1_77_0
MYSQL_SOURCE_DIR=mysql-${MAJOR_VERSION}.${MINOR_VERSION}.${PATCH_VERSION}
SHELL_SOURCE_DIR=mysql-shell-8.0.32-src
CMAKE_EXE_LINKER_FLAGS=""
JOBS=`lscpu | grep '^CPU(s)'|awk '{print $NF}'`
if [ ${JOBS} -ge 16 ] ; then
  JOBS=`expr ${JOBS} - 4`
else
  JOBS=`expr ${JOBS} - 1`
fi

cd /opt/${MYSQL_SOURCE_DIR} && \
rm -fr bld && \
mkdir bld && \
cd bld && \
cmake .. -DBOOST_INCLUDE_DIR=/opt/boost_${BOOST_VERSION} \
-DLOCAL_BOOST_DIR=/opt/boost_${BOOST_VERSION} \
-DWITH_SSL=system && \
cmake --build . --target mysqlclient -- -j${JOBS}; \
cmake --build . --target mysqlxclient -- -j${JOBS}

cd /opt/${SHELL_SOURCE_DIR} && \
rm -fr bld && \
mkdir bld && \
cd bld && \
cmake .. \
-DCMAKE_INSTALL_PREFIX=${BASE_DIR} \
-DMYSQL_SOURCE_DIR=/opt/${MYSQL_SOURCE_DIR} \
-DMYSQL_BUILD_DIR=/opt/${MYSQL_SOURCE_DIR}/bld/ \
-DHAVE_PYTHON=1 \
-DWITH_PROTOBUF=bundled \
-DBUILD_SOURCE_PACKAGE=0 \
-DBUNDLED_ANTLR_DIR=/usr/local/antlr4/ \
&& make -j${JOBS} && make -j${JOBS} install

cp /usr/local/lib/libprotobuf.so.30 ${BASE_DIR}/lib/mysqlsh/
