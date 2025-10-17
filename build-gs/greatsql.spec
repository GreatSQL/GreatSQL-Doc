# Copyright (c) 2000, 2015, Oracle and/or its affiliates. All rights reserved.
# Copyright (c) 2023, GreatDB Software Co., Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING. If not, write to the
# Free Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston
# MA  02110-1301  USA.

# Rebuild on OL5/RHEL5 needs following rpmbuild options:
#  rpmbuild --define 'dist .el5' --define 'rhel 5' --define 'el5 1' mysql.spec

# Install cmake28 from EPEL when building on OL5/RHEL5 and OL6/RHEL6.

# NOTE: "vendor" is used in upgrade/downgrade check, so you can't
# change these, has to be exactly as is.

%undefine _missing_build_ids_terminate_build
%global mysql_vendor Oracle and/or its affiliates
%global greatsql_vendor GreatDB Software Co., Ltd.
%global mysqldatadir /var/lib/mysql

%global mysql_version 8.4.4
%global greatsql_version 4
%global revision d73de75905d
%global tokudb_backup_version %{mysql_version}-%{greatsql_version}
%global rpm_release 1

%global release %{greatsql_version}.%{rpm_release}%{?dist}

# By default, a build will be done using the system SSL library
%{?with_ssl: %global ssl_option -DWITH_SSL=%{with_ssl}}
%{!?with_ssl: %global ssl_option -DWITH_SSL=system}

# By default a build will be done including the TokuDB
%{!?with_tokudb: %global tokudb 0}

# By default a build will be done including the RocksDB
%{!?with_rocksdb: %global rocksdb 0}

# Pass path to mecab lib
%{?with_mecab: %global mecab_option -DWITH_MECAB=%{with_mecab}}
%{?with_mecab: %global mecab 1}

# Regression tests may take a long time, override the default to skip them
%{!?runselftest:%global runselftest 0}

%{!?with_systemd:                %global systemd 0}
%global systemd 1
%{!?with_debuginfo:              %global nodebuginfo 1}
%{!?product_suffix:              %global product_suffix -80}
%{!?feature_set:                 %global feature_set community}
%{!?compilation_comment_release: %global compilation_comment_release GreatSQL (GPL), Release %{greatsql_version}, Revision %{revision}}
%{!?compilation_comment_debug:   %global compilation_comment_debug GreatSQL - Debug (GPL), Release %{greatsql_version}, Revision %{revision}}
%{!?src_base:                    %global src_base greatsql}
%global add_fido_plugins 1

# Setup cmake flags for TokuDB
%if 0%{?tokudb}
  %global TOKUDB_FLAGS -DWITH_VALGRIND=OFF -DUSE_VALGRIND=OFF -DDEBUG_EXTNAME=OFF -DBUILD_TESTING=OFF -DUSE_GTAGS=OFF -DUSE_CTAGS=OFF -DUSE_ETAGS=OFF -DUSE_CSCOPE=OFF -DTOKUDB_BACKUP_PLUGIN_VERSION=%{tokudb_backup_version}
  %global TOKUDB_DEBUG_ON -DTOKU_DEBUG_PARANOID=ON
  %global TOKUDB_DEBUG_OFF -DTOKU_DEBUG_PARANOID=OFF
%else
  %global TOKUDB_FLAGS -DWITHOUT_TOKUDB=1
  %global TOKUDB_DEBUG_ON %{nil}
  %global TOKUDB_DEBUG_OFF %{nil}
%endif

# Setup cmake flags for RocksDB
%if 0%{?rocksdb}
  %global ROCKSDB_FLAGS -DWITH_ROCKSDB=0
%else
  %global ROCKSDB_FLAGS -DWITH_ROCKSDB=0
%endif

%global shared_lib_pri_name mysqlclient
%global shared_lib_sec_name perconaserverclient

# multiarch
%global multiarchs            ppc %{power64} %{ix86} x86_64 %{sparc} %{arm} aarch64 loongarch64

%global src_dir               %{src_base}-%{mysql_version}-%{greatsql_version}

# We build debuginfo package so this is not used
%if 0%{?nodebuginfo}
%global _enable_debug_package 0
%global debug_package         %{nil}
%global __os_install_post     /usr/lib/rpm/brp-compress %{nil}
%endif

%global license_files_server  %{src_dir}/README.md
%global license_type          GPLv2

Name:           greatsql
Summary:        GreatSQL: a high performance, highly reliable, easy to use, and high security database that can be used to replace MySQL or Percona Server.
Group:          Applications/Databases
Version:        %{mysql_version}
Release:        %{release}
License:        GPL-2.0-or-later AND LGPL-2.1-only AND BSL-1.0 AND GPL-1.0-or-later OR Artistic-1.0-Perl AND BSD-2-Clause
URL:            https://greatsql.cn
SOURCE0:        https://product.greatdb.com/GreatSQL-%{mysql_version}-%{greatsql_version}/%{name}-%{mysql_version}-%{greatsql_version}.tar.xz
SOURCE10:       https://archives.boost.io/release/1.77.0/source/boost_1_77_0.tar.xz
SOURCE11:       mysqld.cnf
SOURCE12:       mysql_config.sh
Patch0:         mysql-5.7-sharedlib-rename.patch
BuildRequires:  cmake >= 2.8.2
BuildRequires:  make
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  perl
BuildRequires:  perl(Carp)
BuildRequires:  perl(Config)
BuildRequires:  perl(Cwd)
BuildRequires:  perl(Data::Dumper)
BuildRequires:  perl(English)
BuildRequires:  perl(Errno)
BuildRequires:  perl(Exporter)
BuildRequires:  perl(Fcntl)
BuildRequires:  perl(File::Basename)
BuildRequires:  perl(File::Copy)
BuildRequires:  perl(File::Find)
BuildRequires:  perl(File::Path)
BuildRequires:  perl(File::Spec)
BuildRequires:  perl(File::Spec::Functions)
BuildRequires:  perl(File::Temp)
BuildRequires:  perl(Getopt::Long)
BuildRequires:  perl(IO::File)
BuildRequires:  perl(IO::Handle)
BuildRequires:  perl(IO::Pipe)
BuildRequires:  perl(IO::Select)
BuildRequires:  perl(IO::Socket)
BuildRequires:  perl(IO::Socket::INET)
BuildRequires:  perl(JSON)
BuildRequires:  perl(Memoize)
BuildRequires:  perl(POSIX)
BuildRequires:  perl(Sys::Hostname)
BuildRequires:  perl(Time::HiRes)
BuildRequires:  perl(Time::localtime)
BuildRequires:  time
BuildRequires:  libaio-devel
BuildRequires:  ncurses-devel
BuildRequires:  pam-devel
BuildRequires:  readline-devel
%ifnarch aarch64
BuildRequires:  numactl-devel
%endif
BuildRequires:  openssl
BuildRequires:  openssl-devel
BuildRequires:  zlib-devel
BuildRequires:  bison
BuildRequires:  openldap-devel
BuildRequires:  libcurl-devel
BuildRequires:  libedit
BuildRequires:  libevent-devel
BuildRequires:  libicu-devel
BuildRequires:  lz4
BuildRequires:  lz4-devel
BuildRequires:  libzstd-devel
%if 0%{?systemd}
BuildRequires:  systemd
BuildRequires:  pkgconfig(systemd)
%endif
BuildRequires:  cyrus-sasl-devel
BuildRequires:  openldap-devel

BuildRequires:  cmake >= 3.6.1
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  libtirpc-devel
BuildRequires:  rpcgen
BuildRequires:  m4
BuildRequires:  krb5-devel
BuildRequires:  libudev-devel

#some more requires, 2025.3.24
BuildRequires:  mecab-devel
BuildRequires:  gzip
BuildRequires:  perl(base)
BuildRequires:  perl(Digest::file)
BuildRequires:  perl(Digest::MD5)
BuildRequires:  perl(Env)
BuildRequires:  perl(FindBin)
BuildRequires:  perl(if)
BuildRequires:  perl-interpreter
BuildRequires:  perl-generators
BuildRequires:  perl(IPC::Open3)
BuildRequires:  perl(lib)
#BuildRequires:  perl(LWP::Simple)
BuildRequires:  perl(Net::Ping)
BuildRequires:  perl(Socket)
BuildRequires:  perl(strict)
BuildRequires:  perl(Test::More)
BuildRequires:  perl(warnings)
BuildRequires:  procps
BuildRequires:  protobuf-lite
BuildRequires:  zlib
#end for some more requires

BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

Conflicts:      community-mysql mysql-community
Conflicts:      mariadb
Conflicts:      Percona-Server

# For rpm => 4.9 only: https://fedoraproject.org/wiki/Packaging:AutoProvidesAndRequiresFiltering
%global __requires_exclude ^perl\\(GD|hostnames|lib::mtr|lib::v1|mtr_|My::|Lmo|Lmo::Meta|Lmo::Object|Lmo::Types|Lmo::Utils|Percona::Toolkit|Quoter|Transformers)
%global __provides_exclude_from ^(%{_datadir}/(mysql|mysql-test)/.*|%{_libdir}/mysql/plugin/.*\\.so|%{_bindir}/mysql.*|%{_sbindir}/mysqld.*)$

%global _privatelibs lib(protobuf|mysqlclient|mysqlharness|mysqlrouter|mysqlclient|daemon|fnv|memcached|murmur|test)*\\.so*
%global __provides_exclude %{?__provides_exclude:%__provides_exclude|}%{_privatelibs}
%global __requires_exclude %{?__requires_exclude:%__requires_exclude|}%{_privatelibs}

%description
GreatSQL: a high performance, highly reliable, easy to use, and high security database that can be used to replace MySQL or Percona Server.

For a description of GreatSQL see https://greatsql.cn

%package -n greatsql-server
Summary:        GreatSQL: a high performance, highly reliable, easy to use, and high security database that can be used to replace MySQL or Percona Server.
Group:          Applications/Databases
Requires:       coreutils
Requires:       bash /bin/sh
Requires:       grep
Requires:       procps
Requires:       shadow-utils
Requires:       net-tools
Requires(pre):  greatsql-shared
Requires:       greatsql-client
Requires:       greatsql-icu-data-files
Requires:       openssl
Conflicts:      greatsql-mysql-config < %{version}-%{release}
Obsoletes:      greatsql-mysql-config < %{version}-%{release}
Conflicts:      mysql-server mysql-community-server mysql-config
Conflicts:      mariadb-server mariadb-galera-server mariadb-connector-c-config mariadb-config
Conflicts:      Percona-SQL-server-50 Percona-Server-server-51 Percona-Server-server-55 Percona-Server-server-56 Percona-Server-server-57 Percona-Server-server
%if 0%{?systemd}
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
%else
Requires(post):   /sbin/chkconfig
Requires(preun):  /sbin/chkconfig
Requires(preun):  /sbin/service
%endif

%description -n greatsql-server
GreatSQL database server binaries and system database setup.

For a description of GreatSQL see https://greatsql.cn

%package -n greatsql-client
Summary:        GreatSQL - Client
Group:          Applications/Databases
Requires:       greatsql-shared
Conflicts:      mysql mysql-client mysql-community-client
Conflicts:      mariadb mariadb-client
Conflicts:      Percona-SQL-client-50 Percona-Server-client-51 Percona-Server-client-55 Percona-Server-client-56 Percona-Server-client-57 Percona-Server-client

%description -n greatsql-client
This package contains the standard GreatSQL client and administration tools.

For a description of GreatSQL see https://greatsql.cn

%package -n greatsql-test
Summary:        Test suite for the GreatSQL
Group:          Applications/Databases
Requires:       perl(Carp)
Requires:       perl(Config)
Requires:       perl(Cwd)
Requires:       perl(Data::Dumper)
Requires:       perl(English)
Requires:       perl(Errno)
Requires:       perl(Exporter)
Requires:       perl(Fcntl)
Requires:       perl(File::Basename)
Requires:       perl(File::Copy)
Requires:       perl(File::Find)
Requires:       perl(File::Path)
Requires:       perl(File::Spec)
Requires:       perl(File::Spec::Functions)
Requires:       perl(File::Temp)
Requires:       perl(Getopt::Long)
Requires:       perl(IO::File)
Requires:       perl(IO::Handle)
Requires:       perl(IO::Pipe)
Requires:       perl(IO::Select)
Requires:       perl(IO::Socket)
Requires:       perl(IO::Socket::INET)
Requires:       perl(JSON)
Requires:       perl(Memoize)
Requires:       perl(POSIX)
Requires:       perl(Sys::Hostname)
Requires:       perl(Time::HiRes)
Requires:       perl(Time::localtime)
Requires(pre):  greatsql-shared greatsql-client greatsql-server
Conflicts:      mysql-test mysql-community-test
Conflicts:      mariadb-test
Conflicts:      Percona-SQL-test-50 Percona-Server-test-51 Percona-Server-test-55 Percona-Server-test-56 Percona-Server-test-57 Percona-Server-test

%description -n greatsql-test
This package contains the GreatSQL regression test suite.

For a description of GreatSQL see https://greatsql.cn

%package -n greatsql-devel
Summary:        GreatSQL - Development header files and libraries
Group:          Applications/Databases
Conflicts:      mysql-devel mysql-community-devel
Conflicts:      mariadb-devel mariadb-connector-c-devel
Conflicts:      Percona-SQL-devel-50 Percona-Server-devel-51 Percona-Server-devel-55 Percona-Server-devel-56 Percona-Server-devel-57 Percona-Server-devel

%description -n greatsql-devel
This package contains the development header files and libraries necessary
to develop GreatSQL client applications.

For a description of GreatSQL see https://greatsql.cn

%package -n greatsql-shared
Summary:        GreatSQL - Shared libraries
Group:          Applications/Databases
Conflicts:      mysql-libs mysql-community-libs mysql-libs < %{version}-%{release}
Conflicts:      mariadb-libs
Conflicts:      Percona-Server-shared-51 Percona-Server-shared-55 Percona-Server-shared-55 Percona-Server-shared-56 Percona-Server-shared-57 Percona-Server-shared

%description -n greatsql-shared
This package contains the shared libraries (*.so*) which certain languages
and applications need to dynamically load and use GreatSQL.

For a description of GreatSQL see https://greatsql.cn

%if 0%{?tokudb}
%package -n greatsql-tokudb
Summary:        GreatSQL - TokuDB package
Group:          Applications/Databases
Requires:       greatsql-server = %{version}-%{release}
Requires:       greatsql-shared = %{version}-%{release}
Requires:       greatsql-client = %{version}-%{release}
Requires:       jemalloc >= 3.3.0
Conflicts:      Percona-server-tokudb

%description -n greatsql-tokudb
This package contains the TokuDB plugin for GreatSQL %{version}-%{release}
%endif

%if 0%{?rocksdb}
%package -n greatsql-rocksdb
Summary:        GreatSQL - RocksDB package
Group:          Applications/Databases
Requires:       greatsql-server = %{version}-%{release}
Requires:       greatsql-shared = %{version}-%{release}
Requires:       greatsql-client = %{version}-%{release}
Conflicts:      Percona-server-rocksdb

%description -n greatsql-rocksdb
This package contains the RocksDB plugin for GreatSQL %{version}-%{release}

For a description of GreatSQL see https://greatsql.cn
%endif

%package  -n   greatsql-mysql-router
Summary:       GreatSQL MySQL Router
Group:         Applications/Databases
Provides:      greatsql-mysql-router = %{version}-%{release}
Obsoletes:     greatsql-mysql-router < %{version}-%{release}
Conflicts:     mysql-router mysql-router-community
Conflicts:     percona-mysql-router

%description -n greatsql-mysql-router
The GreatSQL MySQL Router software delivers a fast, multi-threaded way of
routing connections from GreatSQL Clients to GreatSQL Servers.

For a description of GreatSQL see https://greatsql.cn

%package   -n   greatsql-mysql-router-devel
Summary:        Development header files and libraries for GreatSQL MySQL Router
Group:          Applications/Databases
Provides:       greatsql-mysql-router-devel = %{version}-%{release}
Conflicts:      mysql-router-devel
Conflicts:      percona-mysql-router-devel

%description -n greatsql-mysql-router-devel
This package contains the development header files and libraries
necessary to develop GreatSQL MySQL Router applications.

For a description of GreatSQL see https://greatsql.cn

%package   -n   greatsql-icu-data-files
Summary:        GreatSQL packaging of ICU data files

%description -n greatsql-icu-data-files
This package contains ICU data files needer by GreatSQL regular expressions.

For a description of GreatSQL see https://greatsql.cn

%prep
#%setup -q -T -a 0 -a 10 -c -n %{src_dir}
%setup -q -T -a 0 -c -n %{src_dir}
pushd %{src_dir}
%patch -P0 -p1

cp %{SOURCE11} scripts

%build
# Fail quickly and obviously if user tries to build as root
%if 0%{?runselftest}
if [ "x$(id -u)" = "x0" ] ; then
   echo "The MySQL regression tests may fail if run as root."
   echo "If you really need to build the RPM as root, use"
   echo "--define='runselftest 0' to skip the regression tests."
   exit 1
fi
%endif

# Build full release
mkdir release
(
  cd release
  cmake ../%{src_dir} \
           -DBUILD_CONFIG=mysql_release \
           -DINSTALL_LAYOUT=RPM \
           -DCMAKE_BUILD_TYPE=RelWithDebInfo \
           -DWITH_BOOST=.. \
	   -DCMAKE_SKIP_INSTALL_RPATH=YES \
%if 0%{?systemd}
           -DWITH_SYSTEMD=1 \
%endif
           -DINSTALL_LIBDIR="%{_lib}/mysql" \
           -DINSTALL_PLUGINDIR="%{_lib}/mysql/plugin" \
           -DMYSQL_UNIX_ADDR="%{mysqldatadir}/mysql.sock" \
           -DINSTALL_MYSQLSHAREDIR=share/greatsql \
           -DINSTALL_SUPPORTFILESDIR=share/greatsql \
           -DFEATURE_SET="%{feature_set}" \
           -DWITH_AUTHENTICATION_LDAP=OFF \
           -DWITH_PAM=1 \
           -DWITH_TOKUDB=OFF \
	   -DWITH_NDB=OFF \
	   -DWITH_NDBCLUSTER=OFF \
	   -DWITH_NDBCLUSTER_STORAGE_ENGINE=OFF \
           -DWITH_UNIT_TESTS=OFF \
           -DWITH_ROCKSDB=OFF \
           -DROCKSDB_DISABLE_AVX2=1 \
           -DROCKSDB_DISABLE_MARCH_NATIVE=1 \
           -DGROUP_REPLICATION_WITH_ROCKSDB=OFF \
           -DALLOW_NO_SSE42=ON \
           -DMYSQL_MAINTAINER_MODE=OFF \
           -DFORCE_INSOURCE_BUILD=1 \
%ifnarch aarch64
           -DWITH_NUMA=ON \
%endif
           -DWITH_LDAP=system \
           -DWITH_SYSTEM_LIBS=ON \
           -DWITH_LZ4=bundled \
           -DWITH_ZLIB=bundled \
           -DWITH_PROTOBUF=bundled \
           -DWITH_RAPIDJSON=bundled \
           -DWITH_ICU=bundled \
           -DWITH_READLINE=system \
           -DWITH_LIBEVENT=bundled \
           -DWITH_ZSTD=bundled \
           -DWITH_KEYRING_VAULT=ON \
%if 0%{?add_fido_plugins}
           -DWITH_FIDO=bundled \
%else
           -DWITH_FIDO=none \
%endif
           -DWITH_SSL=system \
	   -DWITH_ROUTER=ON \
	   -DENABLED_LOCAL_INFILE=ON \
           -DCOMPILATION_COMMENT="%{compilation_comment_release}" %{TOKUDB_FLAGS} %{TOKUDB_DEBUG_OFF} %{ROCKSDB_FLAGS}
  echo BEGIN_NORMAL_CONFIG ; echo END_NORMAL_CONFIG
  make %{?_smp_mflags}
)

%install
%define _unpackaged_files_terminate_build 0
MBD=$RPM_BUILD_DIR/%{src_dir}

# Ensure that needed directories exists
install -d -m 0751 %{buildroot}/var/lib/mysql
install -d -m 0755 %{buildroot}/var/run/mysqld
install -d -m 0750 %{buildroot}/var/lib/mysql-files
install -d -m 0750 %{buildroot}/var/lib/mysql-keyring

# Router directories
install -d -m 0755 %{buildroot}/var/log/mysqlrouter
install -d -m 0755 %{buildroot}/var/run/mysqlrouter

# Install all binaries
cd $MBD/release
make DESTDIR=%{buildroot} install

# Install logrotate and autostart
#install -D -m 0644 packaging/rpm-common/mysql.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/mysql
#investigate this logrotate
install -D -m 0644 $MBD/release/support-files/mysql-log-rotate %{buildroot}%{_sysconfdir}/logrotate.d/mysql
install -D -m 0644 $MBD/%{src_dir}/build-gs/rpm/mysqld.cnf %{buildroot}%{_sysconfdir}/my.cnf
install -D -p -m 0644 %{_builddir}/greatsql-%{version}-%{greatsql_version}/greatsql-%{version}-%{greatsql_version}/scripts/mysqld.cnf %{buildroot}%{_sysconfdir}/my.cnf
install -d %{buildroot}%{_sysconfdir}/my.cnf.d

#%if 0%{?systemd}
#%else
#%if 0%{?rhel} < 7
#  install -D -m 0755 $MBD/%{src_dir}/build-gs/rpm/mysql.init %{buildroot}%{_sysconfdir}/init.d/mysql
#%endif


# Add libdir to linker
install -d -m 0755 %{buildroot}%{_sysconfdir}/ld.so.conf.d
echo "%{_libdir}/mysql" >> %{buildroot}%{_sysconfdir}/ld.so.conf.d/mysql-%{_arch}.conf
echo "%{_libdir}/mysql/private" >> %{buildroot}%{_sysconfdir}/ld.so.conf.d/mysql-%{_arch}.conf
echo "%{_libdir}/mysqlrouter" >> %{buildroot}%{_sysconfdir}/ld.so.conf.d/mysql-%{_arch}.conf
echo "%{_libdir}/mysqlrouter/private" >> %{buildroot}%{_sysconfdir}/ld.so.conf.d/mysql-%{_arch}.conf

# multiarch support
%ifarch %{multiarchs}
  mv %{buildroot}/%{_bindir}/mysql_config %{buildroot}/%{_bindir}/mysql_config-%{__isa_bits}
  install -p -m 0755 %{SOURCE12} %{buildroot}/%{_bindir}/mysql_config
%endif

%if 0%{?systemd}
install -D -p -m 0644 scripts/mysqlrouter.service %{buildroot}%{_unitdir}/mysqlrouter.service
#install -D -p -m 0644 packaging/rpm-common/mysqlrouter.conf %{buildroot}%{_tmpfilesdir}/mysqlrouter.conf
#install -D -p -m 0644 packaging/rpm-common/mysqlrouter.tmpfiles.d %{buildroot}%{_tmpfilesdir}/mysqlrouter.conf
%else
install -D -p -m 0755 packaging/rpm-common/mysqlrouter.init %{buildroot}%{_sysconfdir}/init.d/mysqlrouter
%endif
install -D -p -m 0644 packaging/rpm-common/mysqlrouter.conf %{buildroot}%{_sysconfdir}/mysqlrouter/mysqlrouter.conf

# Remove files pages we explicitly do not want to package
rm -rf %{buildroot}%{_infodir}/mysql.info*
rm -rf %{buildroot}%{_datadir}/greatsql/mysql.server
rm -rf %{buildroot}%{_datadir}/greatsql/mysqld_multi.server
rm -f %{buildroot}%{_datadir}/greatsql/win_install_firewall.sql
rm -f %{buildroot}%{_datadir}/greatsql/audit_log_filter_win_install.sql
rm -rf %{buildroot}%{_bindir}/mysql_embedded
rm -rf %{buildroot}/usr/cmake/coredumper-relwithdebinfo.cmake
rm -rf %{buildroot}/usr/cmake/coredumper.cmake
rm -rf %{buildroot}/usr/include/kmip.h
rm -rf %{buildroot}/usr/include/kmippp.h
rm -rf %{buildroot}/usr/lib/libkmip.a
rm -rf %{buildroot}/usr/lib/libkmippp.a

%check
%if 0%{?runselftest}
  pushd release
    make test VERBOSE=1
    export MTR_BUILD_THREAD=auto
  pushd mysql-test
  ./mtr \
    --mem --parallel=auto --force --retry=0 \
    --mysqld=--binlog-format=mixed \
    --suite-timeout=720 --testcase-timeout=30 \
    --clean-vardir
  rm -r $(readlink var) var
%endif

%pretrans -n greatsql-server
if [ -d %{_datadir}/mysql ] && [ ! -L %{_datadir}/mysql ]; then
  MYCNF_PACKAGE=$(rpm -qf /usr/share/mysql --queryformat "%{NAME}")
fi

if [ "$MYCNF_PACKAGE" == "mariadb-libs" -o "$MYCNF_PACKAGE" == "mysql-libs" ]; then
  MODIFIED=$(rpm -Va "$MYCNF_PACKAGE" | grep '/usr/share/mysql' | awk '{print $1}' | grep -c 5)
  if [ "$MODIFIED" == 1 ]; then
    cp -r %{_datadir}/mysql %{_datadir}/mysql.old
  fi
fi

%pre -n greatsql-server
/usr/sbin/groupadd -g 27 -o -r mysql >/dev/null 2>&1 || :
/usr/sbin/useradd -M %{!?el5:-N} -g mysql -o -r -d /var/lib/mysql -s /bin/false \
    -c "GreatSQL" -u 27 mysql >/dev/null 2>&1 || :
if [ "$1" = 1 ]; then
  if [ -f %{_sysconfdir}/my.cnf ]; then
    timestamp=$(date '+%Y%m%d-%H%M')
    cp %{_sysconfdir}/my.cnf \
    %{_sysconfdir}/my.cnf.rpmsave-${timestamp}
  fi
fi

%post -n greatsql-server
datadir=$(/usr/bin/my_print_defaults server mysqld | grep '^--datadir=' | sed -n 's/--datadir=//p' | tail -n 1)
/bin/chmod 0751 "$datadir" >/dev/null 2>&1 || :
if [ ! -e /var/log/mysqld.log ]; then
    /usr/bin/install -m0640 -omysql -gmysql /dev/null /var/log/mysqld.log
fi

%if 0%{?systemd}
  %systemd_post mysqld.service
  if [ $1 == 1 ]; then
      /usr/bin/systemctl enable mysqld >/dev/null 2>&1 || :
  fi
%else
  if [ $1 == 1 ]; then
      /sbin/chkconfig --add mysql
  fi
%endif

if [ -d /etc/greatsql.conf.d ]; then
    CONF_EXISTS=$(grep "greatsql.conf.d" /etc/my.cnf | wc -l)
    if [ ${CONF_EXISTS} = 0 ]; then
        echo "!includedir /etc/greatsql.conf.d/" >> /etc/my.cnf
    fi
fi
echo "user = mysql" >> /etc/my.cnf
echo "datadir = /var/lib/mysql" >> /etc/my.cnf
echo "socket = /var/lib/mysql/mysql.sock" >> /etc/my.cnf
echo "log-error = /var/log/mysqld.log" >> /etc/my.cnf
echo "pid-file = /var/run/mysqld/mysqld.pid" >> /etc/my.cnf
echo "slow_query_log = ON" >> /etc/my.cnf
echo "long_query_time = 0.01" >> /etc/my.cnf
echo "log_slow_verbosity = FULL" >> /etc/my.cnf
echo "log_error_verbosity = 3" >> /etc/my.cnf
echo "innodb_buffer_pool_size = 1G" >> /etc/my.cnf
echo "innodb_redo_log_capacity = 256M" >> /etc/my.cnf
echo "innodb_io_capacity = 10000" >> /etc/my.cnf
echo "innodb_io_capacity_max = 20000" >> /etc/my.cnf
echo "innodb_flush_sync = OFF" >> /etc/my.cnf

%preun -n greatsql-server
%if 0%{?systemd}
  %systemd_preun mysqld.service
%else
  if [ "$1" = 0 ]; then
    /sbin/service mysql stop >/dev/null 2>&1 || :
    /sbin/chkconfig --del mysql
  fi
%endif
if [ "$1" = 0 ]; then
  if [ -L %{_datadir}/mysql ]; then
      rm %{_datadir}/mysql
  fi
  if [ -f %{_sysconfdir}/my.cnf ]; then
    cp %{_sysconfdir}/my.cnf \
    %{_sysconfdir}/my.cnf.rpmsave
  fi
fi

%postun -n greatsql-server
%if 0%{?systemd}
  %systemd_postun_with_restart mysqld.service
%else
  if [ $1 -ge 1 ]; then
    /sbin/service mysql condrestart >/dev/null 2>&1 || :
  fi
%endif

%posttrans -n greatsql-server
if [ -d %{_datadir}/mysql ] && [ ! -L %{_datadir}/mysql ]; then
  MYCNF_PACKAGE=$(rpm -qf /usr/share/mysql --queryformat "%{NAME}")
  if [ "$MYCNF_PACKAGE" == "file %{_datadir}/mysql is not owned by any package" ]; then
    mv %{_datadir}/mysql %{_datadir}/mysql.old
  fi
fi

if [ ! -d %{_datadir}/mysql ] && [ ! -L %{_datadir}/mysql ]; then
    ln -s %{_datadir}/greatsql %{_datadir}/mysql
fi

%post -n greatsql-shared

%postun -n greatsql-shared

%ifarch x86_64
%if 0%{?compatlib}
%post -n greatsql-shared-compat
for lib in libmysqlclient{.so.18.0.0,.so.18,_r.so.18.0.0,_r.so.18}; do
  if [ ! -f %{_libdir}/mysql/${lib} ]; then
    ln -s libmysqlclient.so.18.1.0 %{_libdir}/mysql/${lib};
  fi
done
/sbin/ldconfig

%postun -n greatsql-shared-compat
for lib in libmysqlclient{.so.18.0.0,.so.18,_r.so.18.0.0,_r.so.18}; do
  if [ -h %{_libdir}/mysql/${lib} ]; then
    rm -f %{_libdir}/mysql/${lib};
  fi
done
/sbin/ldconfig
%endif
%endif

%if 0%{?rocksdb}
%post -n greatsql-rocksdb
if [ $1 -eq 1 ] ; then
  echo -e "\n\n * This release of GreatSQL is distributed with RocksDB storage engine."
  echo -e " * Run the following script to enable the RocksDB storage engine in GreatSQL:\n"
  echo -e "\tps-admin --enable-rocksdb -u <mysql_admin_user> -p[mysql_admin_pass] [-S <socket>] [-h <host> -P <port>]\n"
fi
%endif

%pre -n greatsql-mysql-router
/usr/sbin/groupadd -r mysqlrouter >/dev/null 2>&1 || :
/usr/sbin/useradd -M -N -g mysqlrouter -r -d /var/lib/mysqlrouter -s /bin/false \
    -c "GreatSQL MySQL Router" mysqlrouter >/dev/null 2>&1 || :

%post -n greatsql-mysql-router
/sbin/ldconfig
%if 0%{?systemd}
%systemd_post mysqlrouter.service
%else
/sbin/chkconfig --add mysqlrouter
%endif

%preun -n greatsql-mysql-router
%if 0%{?systemd}
%systemd_preun mysqlrouter.service
%else
if [ "$1" = 0 ]; then
    /sbin/service mysqlrouter stop >/dev/null 2>&1 || :
    /sbin/chkconfig --del mysqlrouter
fi
%endif

%postun -n greatsql-mysql-router
/sbin/ldconfig
%if 0%{?systemd}
%systemd_postun_with_restart mysqlrouter.service
%else
if [ $1 -ge 1 ]; then
    /sbin/service mysqlrouter condrestart >/dev/null 2>&1 || :
fi
%endif


%files -n greatsql-server
%defattr(-, root, root, -)
%doc %{?license_files_server}
%doc %{src_dir}/Docs/INFO_SRC*
%doc release/Docs/INFO_BIN*
%attr(644, root, root) %{_mandir}/man1/innochecksum.1*
%attr(644, root, root) %{_mandir}/man1/ibd2sdi.1*
%attr(644, root, root) %{_mandir}/man1/my_print_defaults.1*
%attr(644, root, root) %{_mandir}/man1/myisam_ftdump.1*
%attr(644, root, root) %{_mandir}/man1/myisamchk.1*
%attr(644, root, root) %{_mandir}/man1/myisamlog.1*
%attr(644, root, root) %{_mandir}/man1/myisampack.1*
%attr(644, root, root) %{_mandir}/man8/mysqld.8*
%attr(644, root, root) %{_mandir}/man1/mysqldumpslow.1*
%attr(644, root, root) %{_mandir}/man1/mysql_secure_installation.1*
%attr(644, root, root) %{_mandir}/man1/mysqlman.1*
%attr(644, root, root) %{_mandir}/man1/mysql_tzinfo_to_sql.1*
%attr(644, root, root) %{_mandir}/man1/perror.1*
%attr(644, root, root) %{_mandir}/man1/lz4_decompress.1*

%config(noreplace) %{_sysconfdir}/my.cnf
%dir %{_sysconfdir}/my.cnf.d

%attr(755, root, root) %{_bindir}/comp_err
%attr(755, root, root) %{_bindir}/innochecksum
%attr(755, root, root) %{_bindir}/ibd2sdi
%attr(755, root, root) %{_bindir}/my_print_defaults
%attr(755, root, root) %{_bindir}/myisam_ftdump
%attr(755, root, root) %{_bindir}/myisamchk
%attr(755, root, root) %{_bindir}/myisamlog
%attr(755, root, root) %{_bindir}/myisampack
%attr(755, root, root) %{_bindir}/mysql_secure_installation
%attr(755, root, root) %{_bindir}/mysql_tzinfo_to_sql
%attr(755, root, root) %{_bindir}/mysqldumpslow
%attr(755, root, root) %{_bindir}/ps_mysqld_helper
%attr(755, root, root) %{_bindir}/perror
%attr(755, root, root) %{_bindir}/lz4_decompress
%attr(755, root, root) %{_bindir}/ps-admin
%attr(755, root, root) %{_bindir}/zstd_decompress
%attr(755, root, root) %{_bindir}/mysqldecompress
%if 0%{?systemd}
%attr(755, root, root) %{_bindir}/mysqld_pre_systemd
%attr(755, root, root) %{_bindir}/mysqld_safe
%else
%attr(755, root, root) %{_bindir}/mysqld_multi
%attr(755, root, root) %{_bindir}/mysqld_safe
%endif
%attr(755, root, root) %{_sbindir}/mysqld
%dir %{_libdir}/mysql/private
%attr(755, root, root) %{_libdir}/mysql/private/libprotobuf-lite.so.*
%attr(755, root, root) %{_libdir}/mysql/private/libprotobuf.so.*
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_bad_any_cast_impl.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_bad_optional_access.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_bad_variant_access.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_base.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_city.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_civil_time.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_cord_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_cord.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_cordz_functions.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_cordz_handle.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_cordz_info.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_cordz_sample_token.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_crc32c.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_crc_cord_state.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_crc_cpu_detect.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_crc_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_debugging_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_demangle_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_die_if_null.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_examine_stack.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_exponential_biased.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_failure_signal_handler.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags_commandlineflag_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags_commandlineflag.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags_config.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags_marshalling.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags_parse.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags_private_handle_accessor.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags_program_name.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags_reflection.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags_usage_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_flags_usage.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_graphcycles_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_hash.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_hashtablez_sampler.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_int128.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_kernel_timeout_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_leak_check.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_entry.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_flags.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_globals.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_initialize.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_internal_check_op.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_internal_conditions.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_internal_format.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_internal_globals.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_internal_log_sink_set.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_internal_message.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_internal_nullguard.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_internal_proto.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_severity.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_log_sink.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_low_level_hash.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_malloc_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_periodic_sampler.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_random_distributions.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_random_internal_distribution_test_util.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_random_internal_platform.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_random_internal_pool_urbg.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_random_internal_randen_hwaes_impl.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_random_internal_randen_hwaes.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_random_internal_randen_slow.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_random_internal_randen.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_random_internal_seed_material.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_random_seed_gen_exception.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_random_seed_sequences.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_raw_hash_set.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_raw_logging_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_scoped_set_env.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_spinlock_wait.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_stacktrace.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_statusor.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_status.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_strerror.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_str_format_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_strings_internal.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_strings.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_string_view.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_symbolize.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_synchronization.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_throw_delegate.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_time.so
%attr(755, root, root) %{_libdir}/mysql/private/libabsl_time_zone.so
%if 0%{?add_ssl_lib}
%attr(755, root, root) %{_libdir}/mysql/private/libcrypto.so
%attr(755, root, root) %{_libdir}/mysql/private/libcrypto.so.1.1
%attr(755, root, root) %{_libdir}/mysql/private/libssl.so
%attr(755, root, root) %{_libdir}/mysql/private/libssl.so.1.1
%endif
%if 0%{?add_fido_plugins}
%attr(755, root, root) %{_libdir}/mysql/private/libfido2.so.*
%attr(755, root, root) %{_libdir}/mysql/plugin/authentication_webauthn_client.so
%endif

%dir %{_libdir}/mysql/plugin
%attr(755, root, root) %{_libdir}/mysql/plugin/procfs.so
%attr(755, root, root) %{_libdir}/mysql/plugin/adt_null.so
%attr(755, root, root) %{_libdir}/mysql/plugin/auth_socket.so
%attr(755, root, root) %{_libdir}/mysql/plugin/authentication_kerberos_client.so
%attr(755, root, root) %{_libdir}/mysql/plugin/authentication_ldap_sasl.so
%attr(755, root, root) %{_libdir}/mysql/plugin/authentication_ldap_sasl_client.so
%attr(755, root, root) %{_libdir}/mysql/plugin/authentication_ldap_simple.so
%attr(755, root, root) %{_libdir}/mysql/plugin/authentication_oci_client.so
%attr(755, root, root) %{_libdir}/mysql/plugin/greatdb_ha.so
%attr(755, root, root) %{_libdir}/mysql/plugin/group_replication.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_audit_api_message_emit.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_encryption_udf.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_keyring_file.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_keyring_kmip.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_keyring_kms.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_log_filter_dragnet.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_log_sink_json.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_log_sink_rotate.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_log_sink_syseventlog.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_mysqlbackup.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_query_attributes.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_reference_cache.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_audit_api_message.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_component_deinit.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_host_application_signal.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_mysql_command_services.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_mysql_system_variable_set.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_sensitive_system_variables.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_status_var_reader.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_table_access.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_udf_services.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_validate_password.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_audit_log_filter.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_binlog_utils_udf.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_keyring_vault.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_masking_functions.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_percona_udf.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_event_tracking_consumer.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_event_tracking_consumer_a.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_event_tracking_consumer_b.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_event_tracking_consumer_c.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_event_tracking_producer_a.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_event_tracking_producer_b.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_execute_prepared_statement.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_execute_regular_statement.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_mysql_signal_handler.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_mysql_thd_store_service.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_server_telemetry_metrics.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_server_telemetry_traces.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_uuid_vx_udf.so
%attr(755, root, root) %{_libdir}/mysql/plugin/conflicting_variables.so
%attr(755, root, root) %{_libdir}/mysql/plugin/connection_control.so
%attr(755, root, root) %{_libdir}/mysql/plugin/ddl_rewriter.so
%attr(755, root, root) %{_libdir}/mysql/plugin/ha_example.so
%attr(755, root, root) %{_libdir}/mysql/plugin/ha_mock.so
%attr(755, root, root) %{_libdir}/mysql/plugin/keyring_udf.so
%attr(755, root, root) %{_libdir}/mysql/plugin/locking_service.so
%attr(755, root, root) %{_libdir}/mysql/plugin/mypluglib.so
%attr(755, root, root) %{_libdir}/mysql/plugin/mysql_clone.so
%attr(755, root, root) %{_libdir}/mysql/plugin/mysql_no_login.so
%attr(755, root, root) %{_libdir}/mysql/plugin/rewrite_example.so
%attr(755, root, root) %{_libdir}/mysql/plugin/rewriter.so
%attr(755, root, root) %{_libdir}/mysql/plugin/semisync_master.so
%attr(755, root, root) %{_libdir}/mysql/plugin/semisync_slave.so
%attr(755, root, root) %{_libdir}/mysql/plugin/semisync_replica.so
%attr(755, root, root) %{_libdir}/mysql/plugin/semisync_source.so
%attr(755, root, root) %{_libdir}/mysql/plugin/validate_password.so
%attr(755, root, root) %{_libdir}/mysql/plugin/version_token.so
%attr(755, root, root) %{_libdir}/mysql/plugin/test_services_command_services.so
%attr(755, root, root) %{_libdir}/mysql/plugin/test_services_host_application_signal.so
%attr(755, root, root) %{_libdir}/mysql/plugin/test_udf_wrappers.so
%if 0%{?mecab}
%{_libdir}/mysql/mecab
%attr(755, root, root) %{_libdir}/mysql/plugin/libpluginmecab.so
%endif
#coredumper
%attr(755, root, root) %{_includedir}/coredumper/coredumper.h
%attr(755, root, root) /usr/lib/libcoredumper.a
# Percona plugins
%attr(755, root, root) %{_libdir}/mysql/plugin/auth_pam.so
%attr(755, root, root) %{_libdir}/mysql/plugin/auth_pam_compat.so
%attr(755, root, root) %{_libdir}/mysql/plugin/dialog.so
%attr(644, root, root) %{_datadir}/greatsql/mysql-log-rotate
%attr(644, root, root) %{_datadir}/greatsql/dictionary.txt
%attr(644, root, root) %{_datadir}/greatsql/install_rewriter.sql
%attr(644, root, root) %{_datadir}/greatsql/uninstall_rewriter.sql
%attr(644, root, root) %{_datadir}/greatsql/audit_log_filter_linux_install.sql
%attr(644, root, root) %{_datadir}/greatsql/sys_masking.sql
%if 0%{?systemd}
%attr(644, root, root) %{_unitdir}/mysqld.service
%attr(644, root, root) %{_unitdir}/mysqld@.service
%attr(644, root, root) %{_prefix}/lib/tmpfiles.d/mysql.conf
%else
%attr(755, root, root) %{_sysconfdir}/init.d/mysql
%endif
%attr(644, root, root) %config(noreplace,missingok) %{_sysconfdir}/logrotate.d/mysql
%dir %attr(751, mysql, mysql) /var/lib/mysql
%dir %attr(755, mysql, mysql) /var/run/mysqld
%dir %attr(750, mysql, mysql) /var/lib/mysql-files
%dir %attr(750, mysql, mysql) /var/lib/mysql-keyring

%attr(755, root, root) %{_datadir}/greatsql/messages_to_clients.txt
%attr(755, root, root) %{_datadir}/greatsql/messages_to_error_log.txt
%attr(755, root, root) %{_datadir}/greatsql/charsets/
%attr(755, root, root) %{_datadir}/greatsql/bulgarian/
%attr(755, root, root) %{_datadir}/greatsql/chinese/
%attr(755, root, root) %{_datadir}/greatsql/czech/
%attr(755, root, root) %{_datadir}/greatsql/danish/
%attr(755, root, root) %{_datadir}/greatsql/dutch/
%attr(755, root, root) %{_datadir}/greatsql/english/
%attr(755, root, root) %{_datadir}/greatsql/estonian/
%attr(755, root, root) %{_datadir}/greatsql/french/
%attr(755, root, root) %{_datadir}/greatsql/german/
%attr(755, root, root) %{_datadir}/greatsql/greek/
%attr(755, root, root) %{_datadir}/greatsql/hungarian/
%attr(755, root, root) %{_datadir}/greatsql/italian/
%attr(755, root, root) %{_datadir}/greatsql/japanese/
%attr(755, root, root) %{_datadir}/greatsql/korean/
%attr(755, root, root) %{_datadir}/greatsql/norwegian-ny/
%attr(755, root, root) %{_datadir}/greatsql/norwegian/
%attr(755, root, root) %{_datadir}/greatsql/polish/
%attr(755, root, root) %{_datadir}/greatsql/portuguese/
%attr(755, root, root) %{_datadir}/greatsql/romanian/
%attr(755, root, root) %{_datadir}/greatsql/russian/
%attr(755, root, root) %{_datadir}/greatsql/serbian/
%attr(755, root, root) %{_datadir}/greatsql/slovak/
%attr(755, root, root) %{_datadir}/greatsql/spanish/
%attr(755, root, root) %{_datadir}/greatsql/swedish/
%attr(755, root, root) %{_datadir}/greatsql/ukrainian/

%files -n greatsql-client
%defattr(-, root, root, -)
%doc %{?license_files_server}
%attr(755, root, root) %{_bindir}/mysql
%attr(755, root, root) %{_bindir}/mysqladmin
%attr(755, root, root) %{_bindir}/mysqlbinlog
%attr(755, root, root) %{_bindir}/mysqlcheck
%attr(755, root, root) %{_bindir}/mysqldecrypt
%attr(755, root, root) %{_bindir}/mysqldump
%attr(755, root, root) %{_bindir}/mysqlimport
%attr(755, root, root) %{_bindir}/mysqlshow
%attr(755, root, root) %{_bindir}/mysqlslap
%attr(755, root, root) %{_bindir}/mysql_config_editor
%attr(755, root, root) %{_bindir}/mysql_migrate_keyring
%attr(755, root, root) %{_bindir}/mysql_keyring_encryption_test
%attr(755, root, root) %{_bindir}/mysql_client_load_balance_test
%attr(755, root, root) %{_bindir}/mysql_test_event_tracking
%if 0%{?add_ssl_lib}
%attr(755, root, root) %{_bindir}/my_openssl
%endif

%attr(644, root, root) %{_mandir}/man1/mysql.1*
%attr(644, root, root) %{_mandir}/man1/mysqladmin.1*
%attr(644, root, root) %{_mandir}/man1/mysqlbinlog.1*
%attr(644, root, root) %{_mandir}/man1/mysqlcheck.1*
%attr(644, root, root) %{_mandir}/man1/mysqldump.1*
%attr(644, root, root) %{_mandir}/man1/mysqlimport.1*
%attr(644, root, root) %{_mandir}/man1/mysqlshow.1*
%attr(644, root, root) %{_mandir}/man1/mysqlslap.1*
%attr(644, root, root) %{_mandir}/man1/mysql_config_editor.1*

%files -n greatsql-devel
%defattr(-, root, root, -)
%doc %{?license_files_server}
%attr(644, root, root) %{_mandir}/man1/comp_err.1*
%attr(644, root, root) %{_mandir}/man1/mysql_config.1*
%attr(755, root, root) %{_bindir}/mysql_config
%ifarch %{multiarchs}
%attr(755, root, root) %{_bindir}/mysql_config-%{__isa_bits}
%endif
%{_includedir}/mysql
%{_datadir}/aclocal/mysql.m4
%{_libdir}/mysql/lib%{shared_lib_pri_name}.a
%{_libdir}/mysql/libmysqlservices.a
%{_libdir}/mysql/lib%{shared_lib_pri_name}.so
%{_libdir}/pkgconfig/%{shared_lib_pri_name}.pc

%files -n greatsql-shared
%defattr(-, root, root, -)
%doc %{?license_files_server}
%dir %attr(755, root, root) %{_libdir}/mysql
%attr(644, root, root) %{_sysconfdir}/ld.so.conf.d/mysql-%{_arch}.conf
%{_libdir}/mysql/lib%{shared_lib_pri_name}.so.24*
#coredumper
%attr(755, root, root) %{_includedir}/coredumper/coredumper.h
%attr(755, root, root) /usr/lib/libcoredumper.a

%ifarch x86_64
%if 0%{?compatlib}
%files -n greatsql-shared-compat
%defattr(-, root, root, -)
%doc %{?license_files_server}
%dir %attr(755, root, root) %{_libdir}/mysql
%attr(644, root, root) %{_sysconfdir}/ld.so.conf.d/mysql-%{_arch}.conf
%{_libdir}/mysql/libmysqlclient.so.%{compatlib}.*
%{_libdir}/mysql/libmysqlclient_r.so.%{compatlib}.*
%endif
%endif

%files -n greatsql-test
%defattr(-, root, root, -)
%doc %{?license_files_server}
%attr(-, root, root) %{_datadir}/mysql-test
%attr(755, root, root) %{_bindir}/mysql_client_test
%attr(755, root, root) %{_bindir}/mysqltest
%attr(755, root, root) %{_bindir}/mysqltest_safe_process
%attr(755, root, root) %{_bindir}/mysqlxtest

%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_sleep_is_connected.so
%attr(755, root, root) %{_libdir}/mysql/plugin/auth.so
%attr(755, root, root) %{_libdir}/mysql/plugin/auth_test_plugin.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_example_component1.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_example_component2.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_example_component3.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_log_sink_test.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_backup_lock_service.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_string_service_charset.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_string_service_long.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_string_service.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_pfs_example.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_pfs_example_component_population.so
%attr(755, root, root) %{_libdir}/mysql/plugin/pfs_example_plugin_employee.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_pfs_notification.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_pfs_resource_group.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_udf_registration.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_mysql_current_thread_reader.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_udf_reg_3_func.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_udf_reg_avg_func.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_udf_reg_int_func.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_udf_reg_int_same_func.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_udf_reg_only_3_func.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_udf_reg_real_func.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_udf_unreg_3_func.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_udf_unreg_int_func.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_udf_unreg_real_func.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_sys_var_service_int.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_sys_var_service.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_sys_var_service_same.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_sys_var_service_str.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_status_var_service.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_status_var_service_int.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_status_var_service_reg_only.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_status_var_service_str.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_status_var_service_unreg_only.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_system_variable_source.so
%attr(644, root, root) %{_libdir}/mysql/plugin/daemon_example.ini
%attr(755, root, root) %{_libdir}/mysql/plugin/libdaemon_example.so
%attr(755, root, root) %{_libdir}/mysql/plugin/replication_observers_example_plugin.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_framework.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_services.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_services_threaded.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_session_detach.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_session_attach.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_session_in_thd.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_session_info.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_2_sessions.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_all_col_types.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_cmds_1.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_commit.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_complex.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_errors.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_lock.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_processlist.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_replication.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_shutdown.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_stmt.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_sqlmode.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_stored_procedures_functions.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_views_triggers.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_x_sessions_deinit.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_x_sessions_init.so
%attr(755, root, root) %{_libdir}/mysql/plugin/qa_auth_client.so
%attr(755, root, root) %{_libdir}/mysql/plugin/qa_auth_interface.so
%attr(755, root, root) %{_libdir}/mysql/plugin/qa_auth_server.so
%attr(755, root, root) %{_libdir}/mysql/plugin/test_security_context.so
%attr(755, root, root) %{_libdir}/mysql/plugin/test_services_plugin_registry.so
%attr(755, root, root) %{_libdir}/mysql/plugin/test_udf_services.so
%attr(755, root, root) %{_libdir}/mysql/plugin/udf_example.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_mysqlx_global_reset.so
%attr(755, root, root) %{_libdir}/mysql/plugin/component_test_mysql_runtime_error.so
%attr(755, root, root) %{_libdir}/mysql/plugin/libtest_sql_reset_connection.so

%if 0%{?rocksdb}
%files -n greatsql-rocksdb
%attr(-, root, root)
%{_libdir}/mysql/plugin/ha_rocksdb.so
%attr(755, root, root) %{_bindir}/ldb
%attr(755, root, root) %{_bindir}/mysql_ldb
%attr(755, root, root) %{_bindir}/sst_dump
%endif

%files -n greatsql-mysql-router
%defattr(-, root, root, -)
%doc %{src_dir}/router/README.router  %{src_dir}/router/LICENSE.router
%dir %{_sysconfdir}/mysqlrouter
%config(noreplace) %{_sysconfdir}/mysqlrouter/mysqlrouter.conf
%attr(644, root, root) %config(noreplace,missingok) %{_sysconfdir}/logrotate.d/mysqlrouter
%{_bindir}/mysqlrouter
%{_bindir}/mysqlrouter_keyring
%{_bindir}/mysqlrouter_passwd
%{_bindir}/mysqlrouter_plugin_info
%attr(644, root, root) %{_mandir}/man1/mysqlrouter.1*
%attr(644, root, root) %{_mandir}/man1/mysqlrouter_passwd.1*
%attr(644, root, root) %{_mandir}/man1/mysqlrouter_plugin_info.1*
%if 0%{?systemd}
%{_unitdir}/mysqlrouter.service
%{_tmpfilesdir}/mysqlrouter.conf
%else
%{_sysconfdir}/init.d/mysqlrouter
%endif
%{_libdir}/mysqlrouter/private/libmysqlharness.so.*
%{_libdir}/mysqlrouter/private/libmysqlharness_stdx.so.*
%{_libdir}/mysqlrouter/private/libmysqlharness_tls.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_connection_pool.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_http.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_http_auth_backend.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_http_auth_realm.so.*
%{_libdir}/mysqlrouter/private/libprotobuf-lite.so.*
%{_libdir}/mysqlrouter/private/libabsl_*.so
%{_libdir}/mysqlrouter/private/libmysqlrouter_io_component.so.1
%{_libdir}/mysqlrouter/private/libmysqlrouter_metadata_cache.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_mysqlxmessages.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_routing.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_routing_connections.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_destination_status.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_cluster.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_http_server.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_mysql.so.*
%{_libdir}/mysqlrouter/private/libmysqlrouter_utils.so.*
%dir %{_libdir}/mysqlrouter
%dir %{_libdir}/mysqlrouter/private
%{_libdir}/mysqlrouter/*.so
%dir %attr(755, mysqlrouter, mysqlrouter) /var/log/mysqlrouter
%dir %attr(755, mysqlrouter, mysqlrouter) /var/run/mysqlrouter

%files -n greatsql-icu-data-files
%defattr(-, root, root, -)
%doc %{?license_files_server}
%dir %attr(755, root, root) %{_libdir}/mysql/private/icudt73l
%{_libdir}/mysql/private/icudt73l/unames.icu
%{_libdir}/mysql/private/icudt73l/cnvalias.icu
%{_libdir}/mysql/private/icudt73l/uemoji.icu
%{_libdir}/mysql/private/icudt73l/ulayout.icu
%{_libdir}/mysql/private/icudt73l/brkitr

%changelog
* Mon Oct 13 2025 GreatSQL <greatsql@greatdb.com> - 8.4.4-4.1
- Release GreatSQL-8.4.4-4.1

* Thu Apr 24 2025 GreatSQL <greatsql@greatdb.com> - 8.0.32-27.6
- add mysql and mysqlrouter private dir into ldconfig search path
- update descriptions

* Fri Apr 11 2025 Funda Wang <fundawang@yeah.net> - 8.0.32-27.5
- greatsql-mysql-config was removed previously, my.cnf was moved
  into greatsql-server package without conflicts and obsoletes

* Tue Apr 1 2025 GreatSQL <greatsql@greatdb.com> - 8.0.32-27.4
- Remove greatsql-mysql-config, greatsql-shared-compat
- Clearly declare the conflicts list

* Fri Mar 28 2025 Funda Wang <fundawang@yeah.net> - 8.0.32-27.3
- fix requires_exclude

* Mon Mar 24 2025 GreatSQL <greatsql@greatdb.com> - 8.0.32-27.2
- Remove debug build stage
- Add some new cmake options

* Mon Mar 10 2025 GreatSQL <greatsql@greatdb.com> - 8.0.32-27.1
- Release GreatSQL-8.0.32-27.1

* Sun Dec 08 2024 Funda Wang <fundawang@yeah.net> - 8.0.32-26.6
- convert to git lfs

* Wed Dec 04 2024 shenzhongwei <shenzhongwei@kylinos.cn> - 8.0.32-26.5
- fix: %patchN is deprecated (2 usages found), use %patch N (or %patch -P N) 

* Wed Dec 04 2024 Funda Wang <fundawang@yeah.net> - 8.0.32-26.4
- use conflicts rather than obsoletes for mysql and mariadb sub packages

* Tue Nov 26 2024 laokz <zhangkai@iscas.ac.cn> - 8.0.32-26.3
- Add riscv64 patch
- Add missed condition of packaging mysql_config-%{__isa_bits}

* Wed Sep 11 2024 GreatSQL <greatsql@greatdb.com> - 8.0.32-26.2
- Fix the issue of missing audit and datamask plugin files for GreatSQL-8.0.32-26.2

* Thu Aug 8 2024 GreatSQL <greatsql@greatdb.com> - 8.0.32-26.1
- Release GreatSQL-8.0.32-26.1

* Fri Jun 7 2024 GreatSQL <greatsql@greatdb.com> - 8.0.32-25.2
- Change the compilation dependency of compat-openssl to openssl for GreatSQL-8.0.32-25.2

* Mon Apr 22 2024 Wenlong Zhang <zhangwenlong@loongson.cn> - 8.0.32-25.3
- add loongarch64 support

* Thu Dec 28 2023 GreatSQL <greatsql@greatdb.com> - 8.0.32-25.1
- Release GreatSQL-8.0.32-25.1

* Wed Jul 5 2023 GreatSQL <greatsql@greatdb.com> - 8.0.32-24.2
- modify libmysqlrouter.so.* to libmysqlrouter*.so.*

* Wed Jun 7 2023 GreatSQL <greatsql@greatdb.com> - 8.0.32-24.1
- Release GreatSQL-8.0.32-24.1 for openEuler

* Mon Feb 6 2023 GreatSQL <greatsql@greatdb.com> - 8.0.25-16.6
- compat-openssl11-devel

* Tue Sep 13 2022 bzhaoop <bzhaojyathousandy@gmail.com> - 8.0.25-16.5
- refactor the mysqld.cnf into the rpm package
- Add the self-dependency towards greatsql-server and greatsql-mysql-config.

* Tue Aug 16 2022 GreatSQL <greatsql@greatdb.com> - 8.0.25-16.4
- new package greatsql-mysql-config

* Fri Aug 12 2022 bzhaoop <bzhaojyathousandy@gmail.com> - 8.0.25-16.3
- Hide the conflict libs and files from provides and requires.

* Tue Aug 9 2022 bzhaoop <bzhaojyathousandy@gmail.com> - 8.0.25-16.2
- Hide the conflict libs and files.

* Mon Jun 6 2022 GreatSQL <greatsql@greatdb.com> - 8.0.25-16.1
- Release GreatSQL-8.0.25-16.1 for openEuler

* Mon Apr 25 2022 GreatSQL <greatsql@greatdb.com> - 8.0.25-15.1
- Release GreatSQL-8.0.25-15.1 for openEuler
