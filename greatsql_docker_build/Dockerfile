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
RUN dnf install -y gcc-toolset-10 && source /opt/rh/gcc-toolset-10/enable
RUN echo 'source /opt/rh/gcc-toolset-10/enable' >> /root/.bash_profile

# update patchelf 0.12
COPY patchelf-0.12.tar.gz /tmp/
RUN cd /tmp && tar -xzvf patchelf-0.12.tar.gz && cd patchelf-0.12 && ./bootstrap.sh && ./configure && make && make install

COPY rpcsvc-proto-1.4.tar.gz /tmp/rpcsvc-proto-1.4.tar.gz
RUN tar zxvf /tmp/rpcsvc-proto-1.4.tar.gz -C /tmp && cd /tmp/rpcsvc-proto-1.4/ && ./configure && make && make install

RUN rm -fr /tmp/*

COPY boost_1_73_0.tar.gz /opt/

CMD ["/usr/sbin/init"]
