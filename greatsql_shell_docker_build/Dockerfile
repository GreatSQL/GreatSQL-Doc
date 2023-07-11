FROM centos
ENV container docker
ENV LANG en_US.utf8

#ENV PATH="/usr/local/mysql/bin:${PATH}"
#ENV LD_LIBRARY_PATH="/usr/loca/mysql/lib:${LD_LIBRARY_PATH}"

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f /lib/systemd/system/multi-user.target.wants/*;\
rm -f /etc/systemd/system/*.wants/*;\
rm -f /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*;\
rm -f /lib/systemd/system/anaconda.target.wants/*;

RUN rm -f /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Linux-AppStream.repo /etc/yum.repos.d/CentOS-Linux-BaseOS.repo && \
curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-vault-8.5.2111.repo && \
sed -i -e '/mirrors.cloud.aliyuncs.com/d' -e '/mirrors.aliyuncs.com/d' /etc/yum.repos.d/CentOS-Base.repo && \
yum install -y epel-release && \
yum clean all && \
yum makecache
RUN yum install -y --skip-broken yum-utils wget diffutils net-tools vim git gcc gcc-c++ automake libtool cmake cmake3 \
make psmisc openssl openssl-devel zlib-devel readline-devel bzip2-devel expat-devel  \
bison  flex wget unzip libcurl-devel libevent-devel libffi-devel lz4-devel \
file clang bzip2 libxml2-devel libtirpc libtirpc-devel numactl-devel numactl-libs \
numactl openldap-devel openldap-clients pam-devel valgrind boost-devel \
libzstd libzstd-devel patchelf perl perl-Env perl-JSON perl-Memoize perl-Time-HiRes time libaio-devel libarchive \
ncurses-devel ncurses-libs pam redhat-lsb-core scl-utils-build pkg-config ccache \
jemalloc jemalloc-devel libicu-devel re2-devel redhat-lsb-core rpm* tar libssh \
cyrus-sasl-devel cyrus-sasl-scram

#RUN dnf install -y dnf
RUN dnf install -y gcc-toolset-11 gcc-toolset-11-annobin-plugin-gcc && source /opt/rh/gcc-toolset-11/enable
RUN echo 'source /opt/rh/gcc-toolset-11/enable' >> /root/.bash_profile

#for MySQL Shell
RUN yum install -y libuuid libuuid-devel uuid python38 python38-devel python38-libs python38-pyyaml libssh libssh-config libssh-devel && pip3.8 install --user certifi

#requirement pkg for Shell compiles
COPY greatsql-shell-requirement-pkg.tar.xz /tmp/
RUN tar xf /tmp/greatsql-shell-requirement-pkg.tar.xz -C /tmp/ && cd /tmp/ && tar xf /tmp/antlr4-4.10.0.tar.gz; \
tar xf /tmp/patchelf-0.14.5.tar.gz; tar xf /tmp/protobuf-all-3.19.4.tar.gz; tar xf /tmp/rpcsvc-proto-1.4.tar.gz

RUN cd /tmp/antlr4-4.10/runtime/Cpp/ && mkdir bld && cd bld && cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local/antlr4 && make && make install
RUN cd /tmp/patchelf-0.14.5 && ./bootstrap.sh && ./configure && make && make install
RUN cd /tmp/protobuf-3.19.4 && ./configure && make && make install
RUN cd /tmp/rpcsvc-proto-1.4 && ./configure && make && make install

RUN rm -fr /tmp/*

COPY greatsql-shell-automake.sh /opt/

CMD ["/usr/sbin/init"]
