# QtRVSim online evaluation

The app will be written in Flask and will be using a MySQL database.

## Roadmap:
- [x] Users are able to register
- [x] Users are able to login
- [x] List of tasks is displayed on the homepage
- [x] Tasks are displayed on their separate pages which the homepage links to
- [x] Logged in users are able to submit solutions on the submit page (with the task number)
- [x] The submission form has a textarea for the task solution (library CodeMirror for assembly highlighting)
- [x] After submitting, the file will be saved in a folder, and a new record will be created in the submission table
- [x] A file will be evaluated and the submission closed, results will be saved in results file
- [x] The results will be displayed on the submission page
- [x] Automatic evaluator, which periodically checks for new submissions and evaluates them
- [x] Find a way to compare the output to the expected output
- [x] Evaluator compares the task output to the reference
- [x] Comparison of reference registers and submission registers
- [x] Comparison of reference memory and submission memory
- [x] On each task page, a leaderboard will be shown with the users best submissions (in cycles), made by a request (to the submissions table) for that task
- [x] Each user will only have the latest submission listed
- [x] Basic app functionality Done?
- [ ] Improve styling if need be
- [ ] Implement admin panel
- [ ] Users can view their last submissions (before it gets overwritten by new one of the same task)

## Database structure (subject to change):

### Users table
| Field              | Type    | Length | Default        |
|--------------------|---------|--------|----------------|
| id                 | int     | 32     | AUTO_INCREMENT |
| username           | varchar | 128    | None           |
| password           | varchar | 128    | None           |
| salt               | varchar | 128    | None           |

### Submissions table

| Field        | Type       | Length | Default             |
|--------------|------------|--------|---------------------|
| id           | int        | 64     | AUTO_INCREMENT      |
| userid       | int        | 64     | None                |
| taskid       | int        | 64     | None                |
| filepath     | varchar    | 64     | None                |
| evaluated    | tinyint    | 1      | 0                   |
| result       | smallint   | 2      | -1                  |
| result_file  | varchar    | 64     | NULL                |
| score        | int        | 32     | -1                  |
| time         | datetime   | None   | current_timestamp() |

User submits a task -> a submission is created. An evaluator evaluates the tasks in the order they came in the database.
After a task is evaluated, it is marked as evaluated, so it is not evaluated more than one time. An evaluation log is created.

### Tasks table

| Field     | Type    | Length | Default        |
|-----------|---------|--------|----------------|
| id        | int     | 64     | AUTO_INCREMENT |
| name      | varchar | 64     | None           |
| path      | varchar | 256    | None           |
| available | tinyint | 1      | 1              |

Database is running on a remote VPS (omega.swpelc.eu, 158.101.208.70:3306)
Testing app is running on the same server on port 5000 [here](http://omega.swpelc.eu:5000). 

## Task creation
Tasks will be stored in toml format, with structure similar to this one (rewritten it to make it more readable, user friendly).

```toml
[task]
name = "Read an save to memory"

description = '''
# Read and save to memory

Write a program that loads 2 values from memory starting at the adress 0x400 into two registers (a0 and a1).
Then add the values in a0 and a1, and store the result in a2.
Save the result in memory after the two values that were loaded.
'''

[arguments]
run = "--d-regs --dump-cycles"

[[inputs]]
data_in = "Two values in memory starting at address 0x400."
data_out = "The values in registers, the sum in register a2, and the sum in memory after the two values."
description = "Loading of values from memory."

[[testcases]]
name = "test01"
do_compare_registers = true
do_compare_memory = true
do_set_starting_memory = true

[[testcases.reference_regs]]
a0 = 5
a1 = 10
a2 = 15

[[testcases.starting_mem]]
0x400 = 5
0x404 = 10

[[testcases.reference_mem]]
0x408 = 15

[[testcases]]
name = "test02"
do_compare_memory = true
do_set_starting_memory = true

[[testcases.starting_mem]]
0x400 = 150
0x404 = 200

[[testcases.reference_mem]]
0x408 = 350

[score]
description = "Runtime of the program in cycles."
metric = "cycles"
```
Arguments are passed to the `QtRVSim` object, which is used to run the simulator.

Inputs is an array, that will be printed to users. Here, you can specify sample data, which the user can test their program on.

Testcases is main part of the evaluator.

In each of the testcases a flag can be set, whether to compare registers (or memory adresses), as well as a dictionary of which of them to compare. We do not need to set the flags at each test (setting them back to `False`) is done automatically at the end of each test.

These are the flags and values that can be set:
```toml
do_compare_registers = true
do_compare_memory = true
do_set_starting_memory = true

[[testcases.reference_regs]]
a0 = 5
a1 = 10
a2 = 15

[[testcases.starting_mem]]
0x400 = 5
0x404 = 10

[[testcases.reference_mem]]
0x408 = 350
```
You can use hex and/or decimal values for the the values set to the registers and memory adresses.

After all necessary tests a score test will be run. This is a "test", which measures the final result based on a metric we provide. Metrics that can be provided as of now are:
```toml
metric = "cycles"
metric = "cache"
```
Note that, in order to use the cache metric, the simulator needs to be run with the `--dump-cache-stats` argument. To use the cycles metric, the simulator needs to be run with the `--dump-cycles` argument.

The scoring metrics are handled at the end of `qtrvsim.py` file.

If you need to run a manual evaluation, you can do so by using the `QtRVSim` class from the `qtrvsim.py` file in a following way:
```python
from qtrvsim import QtRVSim

sim = QtRVSim(args="--d-regs --dump-cycles --dump-cache-stats", submission_file="submissions/test/test.S")
#sim.set_verbose(True)
staring_memory = {
	0x400 : 1,
	0x404 : 2,
}

sim.set_starting_memory(staring_memory)

sim.set_do_compare_registers(True)
reference_regs = {
	'a0' : 0x00000001,
	'a1' : 0x00000002,
	'a2' : 0x00000003,
}
sim.set_reference_ending_regs(reference_regs)

sim.set_do_compare_memory(True)

memory = {
	0x408 : 3,
}

sim.set_reference_ending_memory(memory)

sim.run()

print(sim.get_log())
#print(sim.get_result())
#print(sim.get_score())
```

## Task evaluation log

The log is saved as a plaintext .log file, and is shown to the user. Each log file name is of this format: `username_taskid.log`. (this means that new submission's log overwrites the old one). This file is displayed to the user in this way:

<img src="rsrc/eval.png" width="750">

A custom styling for CodeMirror has been written, to make the log more readable.

## Database config
Database configuration is made in a file `db_connect.py`
```python
db_config = {
	'user': 'username',
	'password': 'password',
	'host': 'ip',
	'database': 'db_name',
	'port': 3306
}
```

## Acknowledgements
- [Flask](https://flask.palletsprojects.com/en/3.0.x/)
- [CodeMirror](https://codemirror.net/)
- [Bootstrap](https://getbootstrap.com/)
- [QtRVSim](https://github.com/cvut/qtrvsim)
