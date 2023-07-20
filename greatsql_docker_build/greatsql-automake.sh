#!/bin/bash
MAJOR_VERSION=8
MINOR_VERSION=0
PATCH_VERSION=32
RELEASE=24
REVISION=3714067bc8c
GLIBC=`ldd --version | head -n 1 | awk '{print $NF}'`
ARCH=`uname -p`
OS=`grep '^ID=' /etc/os-release | sed 's/.*"\(.*\)".*/\1/ig'`
#OS=Linux
PKG_NAME=GreatSQL-${MAJOR_VERSION}.${MINOR_VERSION}.${PATCH_VERSION}-${RELEASE}-${OS}-glibc${GLIBC}-${ARCH}
BASE_DIR=/usr/local/${PKG_NAME}
BOOST_VERSION=1_77_0
SOURCE_DIR=greatsql-${MAJOR_VERSION}.${MINOR_VERSION}.${PATCH_VERSION}-${RELEASE}
CMAKE_EXE_LINKER_FLAGS=""
JOBS=`lscpu | grep '^CPU(s)'|awk '{print $NF}'`

if [ ${ARCH} = "x86_64" ] ; then
  CMAKE_EXE_LINKER_FLAGS=" -ljemalloc "
fi

if [ ${ARCH} = "loongarch64" ] ; then
  cd /opt/${SOURCE_DIR}
  sed -i 's/\(.*defined.*mips.*\) \\/\1 defined(__loongarch__) || \\/ig' extra/icu/source/i18n/double-conversion-utils.h
fi

cd /opt/${SOURCE_DIR} && \
rm -fr bld && \
mkdir bld && \
cd bld && \
cmake .. -DBOOST_INCLUDE_DIR=/opt/boost_${BOOST_VERSION} \
-DLOCAL_BOOST_DIR=/opt/boost_${BOOST_VERSION} \
-DCMAKE_INSTALL_PREFIX=${BASE_DIR} -DWITH_ZLIB=bundled \
-DWITH_NUMA=ON -DCMAKE_EXE_LINKER_FLAGS="${CMAKE_EXE_LINKER_FLAGS}" \
-DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_CONFIG=mysql_release \
-DWITH_TOKUDB=OFF -DWITH_ROCKSDB=OFF \
-DCOMPILATION_COMMENT="${MYSQL} GreatSQL, Release ${RELEASE}, Revision ${REVISION}" \
-DMAJOR_VERSION=${MAJOR_VERSION} -DMINOR_VERSION=${MINOR_VERSION} -DPATCH_VERSION=${PATCH_VERSION} \
-DWITH_NDB=OFF -DWITH_NDBCLUSTER_STORAGE_ENGINE=OFF -DWITH_NDBCLUSTER=OFF \
-DWITH_UNIT_TESTS=OFF -DWITH_SSL=system -DWITH_SYSTEMD=ON \
-DWITH_AUTHENTICATION_LDAP=OFF \
&& make -j${JOBS} VERBOSE=1 && make -j${JOBS} install
