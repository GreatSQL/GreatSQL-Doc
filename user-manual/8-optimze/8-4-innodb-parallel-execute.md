# InnoDB并行查询使用说明
有两种方式来使用并行查询：

## 1. 设置系统参数
通过全局参数 `force_parallel_execute` 来控制是否启用并行查询；使用全局参数 `parallel_default_dop` 来控制使用多少线程去并行查询。上述参数在使用过程中，随时可以修改，无需重启数据库。

例如，想要开启并行执行，并且并发度为4：
```
force_parallel_execute=on;

parallel_default_dop=4;
```
可以根据实际情况调整 `parallel_cost_threshold` 参数的值，如果设置为0，则所有查询都会使用并行；设置为非0，则只有查询语句的代价估值大于该值的查询才会使用并行。

## 2. 使用hint语法
使用hint语法可以控制单个语句是否进行并行执行。在系统默认关闭并行执行的情况下, 可以使用hint对特定的SQL进行加速。相反地，也可以限制某类SQL进入并行执行。

- `SELECT /*+ PQ */ … FROM …` 使用默认的并发度4进行并行查询。

- `SELECT /*+ PQ(8) */ … FROM …` 使用并发度为8进行并行查询。

- `SELECT /*+ NO_PQ */ … FROM …` 这条语句不使用并行查询。

# 并行查询相关参数、状态变量

## 1. 新增参数
在并行框架中，增加6个并行相关的参数：

| System Variable Name	| force_parallel_execute |
| --- | --- | 
| Variable Scope	| global, session |
| Dynamic Variable	| YES |
| Permitted Values |	ON/OFF |
| Default	| OFF |
| Description	| 设置并行查询的开关，bool值，on/off。默认off，关闭并行查询特性。 |

<br/>

| System Variable Name	| parallel_cost_threshold |
| --- | --- | 
| Variable Scope	| global, session |
| Dynamic Variable	| YES |
| Permitted Values |	[0, ULONG_MAX] |
| Default	| 1000 |
| Description	| 设置SQL语句走并行查询的阈值，只有当查询的估计代价高于这个阈值才会执行并行查询，SQL语句的估计代价低于这个阈值，执行原生的查询过程。 |

<br/>

| System Variable Name	| parallel_default_dop |
| --- | --- | 
| Variable Scope	| global, session |
| Dynamic Variable	| YES |
| Permitted Values |	[0, 1024] |
| Default	| 4 |
| Description	| 设置每个SQL语句的并行查询的最大并发度。<br/>SQL语句的查询并发度会根据表的大小来动态调整，如果表的二叉树太小（表的切片划分数小于并行度），则会根据表的切片划分数来设置该查询的并发度。每一个查询的最大并行度都不会超过parallel_default_dop参数设置的值。 |

<br/>

| System Variable Name	| parallel_max_threads |
| --- | --- | 
| Variable Scope	| global, session |
| Dynamic Variable	| YES |
| Permitted Values |	[0, ULONG_MAX] |
| Default	| 64 |
| Description	| 设置系统中总的并行查询线程数。 |

<br/>

| System Variable Name	| parallel_memory_limit |
| --- | --- | 
| Variable Scope	| global, session |
| Dynamic Variable	| YES |
| Permitted Values |	[0, ULONG_MAX] |
| Default	| 1073741824（1GB） |
| Description	| 并行执行时leader线程和worker线程使用的总内存大小上限。<br/>在一个重TP，轻AP的场景里，innodb_buffer_pool_size可以设置为物理内存的50%左右，parallel_memory_limit可以设置为物理内存的20% ~ 30%左右。 |

<br/>

| System Variable Name	| parallel_queue_timeout |
| --- | --- | 
| Variable Scope	| global, session |
| Dynamic Variable	| YES |
| Permitted Values |	[0, ULONG_MAX] |
| Default	| 0 |
| Description	| 设置系统中并行查询的等待的超时时间，如果系统的资源不够，例如运行的并行查询线程已达到parallel_max_threads的值，并行查询语句将会等待，如果超时后还未获取资源，将会执行原生的查询过程。 <br/>单位：毫秒|

## 2. 新增状态变量
在并行框架中，同时增加了4个状态变量：

- **PQ_threads_running**

global级别，当前正在运行的并行执行的总线程数。

- **PQ_memory_used**

global级别，当前并行执行使用的总内存量。

- **PQ_threads_refused**

global级别，由于总线程数限制，导致未能执行并行执行的查询总数。

- **PQ_memory_refused**

global级别，由于总内存限制，导致未能执行并行执行的查询总数。
