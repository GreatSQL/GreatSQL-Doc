# InnoDB parallel query

There are two ways to use innodb parallel query.

## 1. Set system options
The global option `force_parallel_execute` control whether to enable innodb parallel query; the global option `parallel_default_dop` set how many threads are used for parallel query. The above options can be modified at run time without restarting the database.

For example, if you want to turn on parallel execution, and the concurrency is 4:
```
force_parallel_execute=on;

parallel_default_dop=4;
```

The value of the `parallel_cost_threshold` can be adjusted according to the real situation.

If it is set to 0, all queries will use parallel; if it is set to non-zero, only queries whose cost estimate of the query statement is greater than this value will use parallel.

## 2. Use hint syntax
Use hint syntax to control whether a single statement is executed in parallel.

In the case that the system disables parallel query by default, hints can be used to accelerate specific SQL. Conversely, you can also restrict certain types of SQL from entering parallel execution.

- `SELECT /*+ PQ */… FROM …` Use the default concurrency of 4 for parallel query.
- 
- `SELECT /*+ PQ(8) */… FROM …` Use a concurrency of 8 for parallel query.
- 
- `SELECT /*+ NO_PQ */… FROM …` This statement does not use parallel query.

# Parallel query related system variables, status variables

## 1. New parameters
In the parallel framework, add 6 new parallel-related system variables:

| System Variable Name | force_parallel_execute |
| --- | --- |
| Variable Scope | global, session |
| Dynamic Variable | YES |
| Permitted Values ​​| ON/OFF |
| Default | OFF |
| Description | Set the switch for parallel query, bool value, on/off. The default is off, and the parallel query feature is disabled. |

<br/>

| System Variable Name | parallel_cost_threshold |
| --- | --- |
| Variable Scope | global, session |
| Dynamic Variable | YES |
| Permitted Values ​​| [0, ULONG_MAX] |
| Default | 1000 |
| Description | Set the threshold for parallel query of SQL statements. Only when the estimated cost of the query is greater than this threshold will the parallel query be executed. The estimated cost of the SQL statement is lower than this threshold, and the native query process will be executed. |

<br/>

| System Variable Name | parallel_default_dop |
| --- | --- |
| Variable Scope | global, session |
| Dynamic Variable | YES |
| Permitted Values ​​| [0, 1024] |
| Default | 4 |
| Description | Set the maximum concurrency of parallel queries for each SQL statement. <br/>The query concurrency of SQL statements will be dynamically adjusted according to the size of the index. If the binary tree of the index is too small (the number of slices of the index is less than the degree of parallelism), the concurrency of the query will be set according to the number of slices of the index. The maximum degree of parallelism of each query will not exceed the value set by the parallel_default_dop parameter. |

<br/>

| System Variable Name | parallel_max_threads |
| --- | --- |
| Variable Scope | global, session |
| Dynamic Variable | YES |
| Permitted Values ​​| [0, ULONG_MAX] |
| Default | 64 |
| Description | Set the total number of parallel query threads. |

<br/>

| System Variable Name | parallel_memory_limit |
| --- | --- |
| Variable Scope | global, session |
| Dynamic Variable | YES |
| Permitted Values ​​| [0, ULONG_MAX] |
| Default | 1073741824 (1GB) |
| Description | The upper limit of the total memory size used by the leader thread and the worker thread during parallel execution. |

<br/>

| System Variable Name | parallel_queue_timeout |
| --- | --- |
| Variable Scope | global, session |
| Dynamic Variable | YES |
| Permitted Values ​​| [0, ULONG_MAX] |
| Default | 0 |
| Description | Set the waiting timeout time for parallel query. If the system resources are not enough, for example, the running parallel query thread has reached the value of parallel_max_threads, the parallel query statement will wait. If the resource is not obtained after the timeout, it will be executed Native query process. <br/>Unit: milliseconds|

## 2. New status variables
In the parallel framework, 4 new status variables are added:

-**PQ_threads_running**

Global status, the total number of threads currently running in parallel.

-**PQ_memory_used**

Global status, the total amount of memory currently used by parallel execution.

-**PQ_threads_refused**

Global status, the total number of queries that cannot be executed in parallel due to the limitation of the total number of threads.

-**PQ_memory_refused**

Global status, the total number of queries that could not be executed in parallel due to the total memory limit.

## 3. About InnoDB parallel query optimization
According to the characteristics of the B+ tree, the B+ tree can be divided into several subtrees. At this time, multiple threads can scan different parts of the same InnoDB table in parallel. Multi-threaded transformation of the execution plan. The execution plan of each sub-thread is consistent with the original execution plan of MySQL, but each sub-thread only needs to scan part of the data in the table, and the results are summarized after the sub-thread scan is completed. Through multi-threaded transformation, multi-core resources can be fully utilized and query performance can be improved.

After optimization, it performs well in the TPC-H test, with a maximum increase of 30 times and an average increase of 15 times. This feature is suitable for SAP, financial statistics and other businesses such as periodic data summary reports.

Use restrictions:
- Subqueries are not supported temporarily, and need to be transformed into JOIN first.
- At present, only ARM is supported, and X86 optimization will be completed as soon as possible.
![Enter picture description](https://images.gitee.com/uploads/images/2021/0819/094317_1c0fb43a_8779455.jpeg "16292668686865.jpg")
