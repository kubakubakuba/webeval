from eval import Evaluator

code = "test.S" 					#your code file
task_file = "test.toml" 			#the task.toml file with the necessary testcases
folder = "/tmp/qtrvsim_web_eval" 	#folder where the evaluation is performed in, usually /tmp/qtrvsim_web_eval

verbose = False						#set this to true if you need more info to debug
log_file = code.replace(".S", ".log") if code.endswith(".S") else code.replace(".c", ".log")

#we create an evaluator object, which uses the QtRVSim class
QEval = Evaluator(folder, verbose)

#we start the evaluation on the task file and the file with the code that is to be evaluated
QEval.evaluate(task_file, code)

#we save the evaluation log to a file
QEval.save_log(log_file)