-- DROP DATABASE IF EXISTS tpch;
-- CREATE DATABASE IF NOT EXISTS tpch DEFAULT CHARACTER SET latin1;
-- USE tpch;

drop table if exists nation;
create table nation  ( n_nationkey  bigint not null,
				n_name       char(25) not null,
				n_regionkey  bigint not null,
				n_comment    varchar(152),
				primary key(n_nationkey),
				key nation_fk1 (n_regionkey) ) secondary_engine = rapid;

drop table if exists region;
create table region  ( r_regionkey  bigint not null,
				r_name       char(25) not null,
				r_comment    varchar(152),
				primary key(r_regionkey) ) secondary_engine = rapid;

drop table if exists part;
create table part  ( p_partkey     bigint not null,
				p_name        varchar(55) not null,
				p_mfgr        char(25) not null,
				p_brand       char(10) not null,
				p_type        varchar(25) not null,
				p_size        integer not null,
				p_container   char(10) not null,
				p_retailprice decimal(15,2) not null,
				p_comment     varchar(23) not null,
				primary key(p_partkey) ) secondary_engine = rapid;

drop table if exists supplier;
create table supplier ( s_suppkey     bigint not null,
				s_name        char(25) not null,
				s_address     varchar(40) not null,
				s_nationkey   bigint not null,
				s_phone       char(15) not null,
				s_acctbal     decimal(15,2) not null,
				s_comment     varchar(101) not null,
				primary key(s_suppkey),
				key supplier_fk1 (s_nationkey) ) secondary_engine = rapid;

drop table if exists partsupp;
create table partsupp ( ps_partkey     bigint not null,
				ps_suppkey     bigint not null,
				ps_availqty    integer not null,
				ps_supplycost  decimal(15,2)  not null,
				ps_comment     varchar(199) not null,
				primary key(ps_partkey,ps_suppkey),
				key partsupp_fk1 (ps_suppkey),
				key partsupp_fk2 (ps_partkey) ) secondary_engine = rapid;


drop table if exists customer;
create table customer ( c_custkey     bigint not null,
				c_name        varchar(25) not null,
				c_address     varchar(40) not null,
				c_nationkey   bigint not null,
				c_phone       char(15) not null,
				c_acctbal     decimal(15,2)   not null,
				c_mktsegment  char(10) not null,
				c_comment     varchar(117) not null,
				primary key(c_custkey),
				key customer_fk1 (c_nationkey) ) secondary_engine = rapid;

drop table if exists orders;
create table orders  ( o_orderkey       bigint not null,
				o_custkey        bigint not null,
				o_orderstatus    char(1) not null,
				o_totalprice     decimal(15,2) not null,
				o_orderdate      date not null,
				o_orderpriority  char(15) not null,  
				o_clerk          char(15) not null, 
				o_shippriority   integer not null,
				o_comment        varchar(79) not null,
				primary key(o_orderkey),
				key orders_fk1 (o_custkey) ) secondary_engine = rapid;

drop table if exists lineitem;
create table lineitem ( l_orderkey    bigint not null,
				l_partkey     bigint not null,
				l_suppkey     bigint not null,
				l_linenumber  bigint not null,
				l_quantity    decimal(15,2) not null,
				l_extendedprice  decimal(15,2) not null,
				l_discount    decimal(15,2) not null,
				l_tax         decimal(15,2) not null,
				l_returnflag  char(1) not null,
				l_linestatus  char(1) not null,
				l_shipdate    date not null,
				l_commitdate  date not null,
				l_receiptdate date not null,
				l_shipinstruct char(25) not null,
				l_shipmode     char(10) not null,
				l_comment      varchar(44) not null,
				primary key(l_orderkey,l_linenumber),
				key lineitem_fk1 (l_orderkey) ,
				key lineitem_fk2 (l_partkey,l_suppkey) ) secondary_engine = rapid;
