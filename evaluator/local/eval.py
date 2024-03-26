from qtrvsim import QtRVSim
import os, re, urllib.parse, traceback, toml

TIMEOUT_TIME = 10 #seconds

class Evaluator():
	def __init__(self, folder="/tmp/qtrvsim_web_eval", verbose=False):
		self.log = ""
		self.folder = folder
		self.result = -1
		self.score = -1
		self.verbose = verbose
		self.sim = None

	def evaluate(self, task_file, submission_file):
		#get arguments from task toml file
		was_accepted = 1 #was not accepted
		cache_exit = False
		make_exit = False
		filepath = ""

		try:
			with open(task_file) as f:
				task_data = toml.load(f)

				cache_max_size = task_data["task"].get("cache_max_size", -1)
				is_c_solution = task_data["task"].get("c_solution", False)

				#get PID of the running evaluator
				pid = os.getpid()

				filepath = self.folder + f"/_job_{pid}/submission.S"
				#make the directory if it does not exist
				if is_c_solution:
					filepath = self.folder + f"/_job_{pid}/submission.c"

				#make the directory if it does not exist
				os.makedirs(os.path.dirname(filepath), exist_ok=True)
				#save the file from s[2] to filepath

				file_content = ""
				with open(submission_file, 'r') as f:
					file_content = f.read()

				with open(filepath, 'w') as f:
					f.write(file_content)

				error_log = ""
				if cache_max_size > 0:
					#read first line of the submission file
					with open(filepath, 'r') as f:
						lines = f.readlines()
					
					#cache settings should be in format 
					#policy,sets,words_in_block,ways,write_method, where policy is either random, lru, lfu
					#for example:
					#lru,1,1,1,wb
					#the line should be in exact format #pragma cache:lru,1,1,1,wb
					
					d_cache_par = None

					for line in lines:
						if line.startswith('#pragma cache:'):
							d_cache_par = line.replace('#pragma cache:', '').strip()
							break

					# Check if the cache parameters line was found
					if d_cache_par == None:
						error_log += "Error: cache parameters line not found\nUse:\n\n#pragma cache:policy,sets,words_in_block,ways,write_method\n\nsomewhere in your file to set these parameters.\n"
						error_log += "policy is either random, lru, lfu\n"
						error_log += f"maximum cache size for this task is {cache_max_size} bytes\n"
						cache_exit = True

					# Check if the parameters can be parsed
					if not cache_exit:
						match = re.match(r'^(lru|lfu|random),\d+,\d+,\d+,(wb|wt)$', d_cache_par)
						if not match:
							error_log += f"Error: cache parameters line not in the correct format {d_cache_par}\n"
							error_log += "Use:\n\n#pragma cache:policy,sets,words_in_block,ways,write_method\n\n"
							error_log += "policy is either random, lru, lfu\n"
							error_log += f"maximum cache size for this task is {cache_max_size} bytes\n"
							cache_exit = True

					d_cache_size_ok = False

					if not cache_exit:
						# Extract the numbers from the parameters and perform the calculation
						numbers = [int(num) for num in re.findall(r'\d+', d_cache_par)]
						if len(numbers) >= 3:
							d_cache_size_ok = numbers[0] * numbers[1] * numbers[2] <= cache_max_size
							
					# Check if the calculation result is 1
					if not d_cache_size_ok and not cache_exit:
						error_log += f"Error: cache size is too big {d_cache_par}\n"
						error_log += f"maximum cache size for this task is {cache_max_size} bytes\n"
						cache_exit = True

					if not cache_exit:
						# Set the cache parameters
						task_data["arguments"]["run"] += f' --d-cache {d_cache_par}'
					

				num_testcases = len(task_data['testcases'])
				self.sim = QtRVSim(args=task_data["arguments"]["run"], submission_file=filepath, working_dir=os.path.dirname(filepath))
				
				if self.verbose:
					self.sim.set_verbose(True)

				score = 0
				tests_passed = 0
				timed_out = False
				assembly_error = False
				makefile_present = False

				if task_data.get("files", None) != None:
					
					for file in task_data["files"]:
						self.sim.create_file(file["name"], file["code"])

				if task_data.get("make", None) != None:
					makefile_present = True
					Makefile = task_data["make"].get("Makefile", None)
						
					self.sim.create_makefile(Makefile)
					self.sim.run_make()

					if not self.sim.makefile_successfull:
						make_exit = True
						error_log += "Error: makefile failed\n"
						error_log += self.sim.makefile_log

				for i in range(num_testcases):
					if cache_exit or make_exit:
						break
					#if flag is set or reference_regs are not empty, compare registers
					if task_data["testcases"][i].get("do_compare_registers", False) or task_data["testcases"][i].get("reference_regs", None) != None:
						#sim.set_do_compare_registers(True)
						self.sim.set_reference_ending_regs(task_data["testcases"][i]["reference_regs"][0])

					if task_data["testcases"][i].get("do_compare_memory", False) or task_data["testcases"][i].get("reference_mem", None) != None:
						#sim.set_do_compare_memory(True)

						mem = task_data["testcases"][i]["reference_mem"][0]
						self.sim.set_reference_ending_memory(mem)

					if task_data["testcases"][i].get("do_set_starting_memory", False) or task_data["testcases"][i].get("starting_mem", None) != None:
						mem = task_data["testcases"][i]["starting_mem"][0]

						self.sim.set_starting_memory(mem)

					if task_data["testcases"][i].get("do_compare_uart", False) or task_data["testcases"][i].get("reference_uart", None) != None:
						#sim.set_do_compare_uart(True)
						uart = task_data["testcases"][i]["reference_uart"][0]
						uart_string = uart.get("uart", None)
						self.sim.set_reference_ending_uart(uart_string, "__uart.out")

					if task_data["testcases"][i].get("do_set_input_uart", False) or task_data["testcases"][i].get("input_uart", None) != None:
						uart = task_data["testcases"][i]["input_uart"][0]
						uart_string = uart.get("uart", None)
						self.sim.set_input_uart(uart_string, "__uart.in")

					if task_data["testcases"][i].get("private", False):
						self.sim.set_private()

					#run the evaluation
					self.sim.log_test_name(task_data["testcases"][i]["name"])
					self.sim.run(task_data["testcases"][i]["name"])
					self.sim.log_test_result(task_data["testcases"][i]["name"])


					if self.sim.get_result() == 0:
						tests_passed += 1

					if self.sim.get_result() == 2: #do not evaluate further testcases if one timed out
						timed_out = True
						break

					if self.sim.get_result() == 5: #qtrvsim.py error code for integrated assembly error
						assembly_error = True
						break

					self.sim.reset()
				
				if tests_passed == num_testcases and not cache_exit and not make_exit:
					was_accepted = 0 #mark as accepted

					scoring_testcase = self.sim.results[task_data["score"]["testcase"]]
					score = scoring_testcase[1] #TODO: can be changed to cache, now is set to cycles

				if timed_out:
					score = -1
					was_accepted = 2

				if assembly_error:
					raise Exception("Error in integrated assembly")

				if not cache_exit and not make_exit:
					self.sim.end_eval(task_data["score"]["testcase"])


			if cache_exit:
				score = -1
				was_accepted = 3
				self.sim.log = error_log

			if make_exit:
				score = -1
				was_accepted = 4
				self.sim.log = error_log

			if makefile_present:
				self.sim.run_make_clean()
				os.remove(os.path.join(os.path.dirname(filepath), "Makefile"))

			self.log = self.sim.get_log()
			self.score = score
			self.result = was_accepted
			
			try:
				os.remove(filepath)
			except OSError as e:
				print(f"Error: {e.filename} - {e.strerror}.")

			try:
				os.rmdir(os.path.dirname(filepath))  # if not empty will not be deleted
			except OSError as e:
				print(f"Error: {e.filename} - {e.strerror}.")

		except Exception as e:
			if self.sim.get_result() == 5: #qtrvsim.py error code for integrated assembly error
				error_log = f"An error occurred during evaluation:\n"
				error_log += f"Error in integrated assembly.\n"

				error_line_nums = re.findall(r'.*:(\d+):error:.*', self.sim.error_log)
				error_line_nums = [int(num) for num in error_line_nums]

				error_types = re.findall(r'.*:\d+:error:(.*)$', self.sim.error_log)

				error_lines = []
				if os.path.exists(filepath):
					with open(filepath, 'r') as f:
						lines = f.readlines()
						for num in error_line_nums:
							error_lines.append(lines[num-1].strip())

				for i, err in enumerate(error_lines):
					error_log += f"On line {error_line_nums[i]} in your code:\n"
					error_log += f"{error_types[0]}\nhere -->" + err + "\n"

				error_log += f"\nPlease check your code and try again.\n"
				error_log += f"\nPlease note, that %lo and %hi are not yet supported in the integrated assembly, and will thus throw an assembly error when no Makefile for compilation is present at the task.\n"

				self.log = error_log
				self.result = 5
				self.score = -1


			else:
				print(f"Error: {e}")
				error_log = f"An error occurred during evaluation:\n"
				error_log += f"{type(e).__name__}\n"
				error_log += f"Message: {e}\n"
				error_log += f"Traceback: {traceback.format_exc()}\n"
				error_log += f"Please create an issue with this error on GitLab: https://gitlab.fel.cvut.cz/b35apo/qtrvsim-eval-web/-/issues/new?issue[title]=Error%20in%20evaluator%20uid%20{s[4]}%20tid{s[1]}&issue[description]={type(e).__name__}%0A{urllib.parse.quote(str(traceback.format_exc()), safe='')}%0A{urllib.parse.quote(str(e), safe='')}"

				self.log = error_log
				self.result = 6
				self.score = -1

	def save_log(self, log_file):
		result_states = {
			0: "Accepted",
			1: "Rejected",
			2: "Timeout",
			3: "Cache error",
			4: "Make error",
			5: "Assembly error",
			99: "Internal evaluator error"
		}

		result = result_states.get(self.result, "Unknown")
		
		with open(log_file, 'w') as f:
			f.write(f"Result: {result}\n")
			f.write(f"Score: {self.score}\n")
			f.write(f"\n---------\nLog:\n")
			f.write(self.log)