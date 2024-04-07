# QtRVSim Python Local Evaluator

This is a implementation of the QtRVSim evaluation script to be used for local evaluation of your code.

## Requirements

Python packages:
  - `toml`

`QtRVSim binary`

You need to have QtRVSim installed (or have a `qtrvsim_cli` binary, you can change the executable location in `qtrvsim.py`). Please follow the instructions at the [QtRVSim repository](https://github.com/cvut/qtrvsim)

`riscv64-unknown-elf-gcc`

A compiler that is needed, when the integrated assembly is not used. Only used in tasks that have a `Makefile` in them.


## Usage

Have your code, that you want to evaluate, in a `.S` or `.c` file. Download a task template file from [GitLab](https://gitlab.fel.cvut.cz/b35apo/qtrvsim-eval-web/-/tree/main/web/tasks?ref_type=heads), or write your own in the same format.

Import the evaluation class and create an instance of it. Pass needed arguments to it, then run the `evaluate` method and save the log with `save_log` method.

```python
from eval import QtRVSimEvaluator

code = "test.S" 					#your code file
task_file = "test.toml" 			#the task.toml file with the necessary testcases
folder = "/tmp/qtrvsim_web_eval" 	#folder where the evaluation is performed in, usually /tmp/qtrvsim_web_eval

verbose = False						#set this to true if you need more info to debug
log_file = code.replace(".S", ".log") if code.endswith(".S") else code.replace(".c", ".log")

#we create an evaluator object, which uses the QtRVSim class
QEval = QtRVSimEvaluator(folder, verbose)

#we start the evaluation on the task file and the file with the code that is to be evaluated
QEval.evaluate(task_file, code)

#we save the evaluation log to a file
QEval.save_log(log_file)
```
