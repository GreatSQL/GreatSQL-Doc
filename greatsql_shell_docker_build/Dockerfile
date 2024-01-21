#for x86_64
FROM centos:8

#for aarch64
#FROM docker.io/arm64v8/centos

LABEL maintainer="greatsql.cn" \
email="greatsql@greatdb.com" \
forum="https://greatsql.cn/forum.php" \
gitee="https://gitee.com/GreatSQL/GreatSQL-Docker"

ENV LANG en_US.utf8
ARG OPT_DIR=/opt \
INSTALL_PKG="automake bison boost-devel bzip2 bzip2-devel clang cmake cmake3 \
cyrus-sasl-devel cyrus-sasl-scram diffutils expat-devel file flex gcc gcc-c++ \
gcc-toolset-11 gcc-toolset-11-annobin-plugin-gcc git libaio-devel libarchive \
libcurl-devel libevent-devel libffi-devel libicu-devel libssh libssh libssh-config libssh-devel \
libtirpc libtirpc-devel libtool libuuid libuuid-devel libxml2-devel libzstd libzstd-devel \
lz4-devel make ncurses-devel ncurses-libs net-tools numactl numactl-devel numactl-libs \
openldap-clients openldap-devel openssl openssl-devel pam pam-devel \
perl perl-Env perl-JSON perl-Memoize perl-Time-HiRes pkg-config psmisc \
python38 python38-devel python38-libs python38-pyyaml \
readline-devel redhat-lsb-core redhat-lsb-core rpm* scl-utils-build \
tar time unzip uuid valgrind vim wget wget yum-utils zlib-devel" \
BUILD_PKG="greatsql_shell_docker_build.tar" \
MYSQLSH_MAKE="greatsql-shell-build.sh"

CMD /bin/bash

RUN unlink /etc/localtime; ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime ; \
rm -f /etc/yum.repos.d/CentOS-Linux-* ; \
curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-vault-8.5.2111.repo && \
sed -i -e '/mirrors.cloud.aliyuncs.com/d' -e '/mirrors.aliyuncs.com/d' /etc/yum.repos.d/CentOS-Base.repo && \
yum clean all > /dev/null 2>&1 && \
yum -y update > /dev/null 2>&1 ; \
rm -f /etc/yum.repos.d/CentOS-Linux-* ; \
yum clean all > /dev/null 2>&1 && \
rm -f /etc/yum.repos.d/CentOS-Linux-* ; \
yum install -y ${INSTALL_PKG} > /dev/null 2>&1 ; \
echo 'source /opt/rh/gcc-toolset-11/enable' >> /root/.bash_profile

COPY ${BUILD_PKG} ${OPT_DIR}
COPY ${MYSQLSH_MAKE} /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["bash"]
