import toml
from datetime import datetime
import time
import evaldb as db
from qtrvsim import QtRVSim
from preprocessor import preprocess
import os
import re
import sys
import urllib.parse
import traceback
from dotenv import load_dotenv

load_dotenv()

TIMEOUT_TIME = 10 #seconds

# Configurable directory for tasks
TASKS_DIR = os.getenv('TASKS_DIR', '../web/tasks')

def fetch_submissions(count):
	"""Fetch the earliest <count> submissions from the database."""

	submissions = db.get_latest_submissions(count)

	#for each taskid fetch its task filename

	task_ids = [submission[1] for submission in submissions]

	if len(task_ids) == 0:
		print("  No submissions available to evaluate.")
		return None

	task_filenames = db.get_task_files(task_ids)

	#make a dictionary of taskid -> task filename
	task_filenames = {task[0]: task[1] for task in task_filenames}

	#resolve task filenames using TASKS_DIR
	resolved_filenames = {}
	for task_id, task_filename in task_filenames.items():
		# If path is relative, use TASKS_DIR; if absolute, use as-is
		if not os.path.isabs(task_filename):
			resolved_filenames[task_id] = os.path.join(TASKS_DIR, os.path.basename(task_filename))
		else:
			resolved_filenames[task_id] = task_filename
	task_filenames = resolved_filenames

	return (submissions, task_filenames)

def evaluate_submissions(num_submissions = 10):
	fetch = fetch_submissions(num_submissions)
	if fetch is None:
		return None
	
	submissions, task_filenames = fetch

	for s in submissions:
		#get arguments from task toml file
		task_id = s[1] #task id
		arguments = []
		was_accepted = 1 #was not accepted
		cache_exit = False
		make_exit = False
		filepath = ""

		try:
			with open(task_filenames[task_id]) as f:
				preprocessed = preprocess(f)
				task_data = toml.loads(preprocessed)
				print(task_data)
				#task_data = toml.load(f)

				cache_max_size = task_data["task"].get("cache_max_size", -1)
				is_c_solution = task_data["task"].get("c_solution", False)

				#get PID of the running evaluator
				pid = os.getpid()
				#save file into /tmp/qtrvsim_web_eval/_job_PID/submission.S
				filepath = f"/tmp/qtrvsim_web_eval/_job_{pid}/submission.S"
				#make the directory if it does not exist
				if is_c_solution:
					filepath = f"/tmp/qtrvsim_web_eval/_job_{pid}/submission.c"

				os.makedirs(os.path.dirname(filepath), exist_ok=True)
				#save the file from s[2] to filepath
				with open(filepath, 'w') as f:
					f.write(s[2])

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
				sim = QtRVSim(submission_file=filepath, working_dir=os.path.dirname(filepath))
				#sim.set_verbose(True)
	
				sim.set_args(args=task_data["arguments"]["run"])

				score = 0
				tests_passed = 0
				timed_out = False
				assembly_error = False
				makefile_present = False

				if task_data.get("files", None) != None:
					
					for file in task_data["files"]:
						sim.create_file(file["name"], file["code"])

				if task_data.get("make", None) != None:
					makefile_present = True
					Makefile = task_data["make"].get("Makefile", None)
						
					sim.create_makefile(Makefile)
					sim.run_make()

					if not sim.makefile_successfull:
						make_exit = True
						error_log += "Error: makefile failed\n"
						error_log += sim.makefile_log

				for i in range(num_testcases):
					if cache_exit or make_exit:
						break
					#if flag is set or reference_regs are not empty, compare registers
					if task_data["testcases"][i].get("do_compare_registers", False) or task_data["testcases"][i].get("reference_regs", None) != None:
						#sim.set_do_compare_registers(True)
						sim.set_reference_ending_regs(task_data["testcases"][i]["reference_regs"][0])

					if task_data["testcases"][i].get("do_compare_memory", False) or task_data["testcases"][i].get("reference_mem", None) != None:
						#sim.set_do_compare_memory(True)

						mem = task_data["testcases"][i]["reference_mem"][0]
						sim.set_reference_ending_memory(mem)

					if task_data["testcases"][i].get("do_set_starting_memory", False) or task_data["testcases"][i].get("starting_mem", None) != None:
						mem = task_data["testcases"][i]["starting_mem"][0]

						sim.set_starting_memory(mem)

					if task_data["testcases"][i].get("do_compare_uart", False) or task_data["testcases"][i].get("reference_uart", None) != None:
						#sim.set_do_compare_uart(True)
						uart = task_data["testcases"][i]["reference_uart"][0]
						uart_string = uart.get("uart", None)
						sim.set_reference_ending_uart(uart_string, "__uart.out")

					if task_data["testcases"][i].get("do_set_input_uart", False) or task_data["testcases"][i].get("input_uart", None) != None:
						uart = task_data["testcases"][i]["input_uart"][0]
						uart_string = uart.get("uart", None)
						sim.set_input_uart(uart_string, "__uart.in")

					if task_data["testcases"][i].get("private", False):
						sim.set_private()

					#run the evaluation
					sim.log_test_name(task_data["testcases"][i]["name"])
					sim.run(task_data["testcases"][i]["name"])
					sim.log_test_result(task_data["testcases"][i]["name"])


					if sim.get_result() == 0:
						tests_passed += 1

					if sim.get_result() == 2: #do not evaluate further testcases if one timed out
						timed_out = True
						break

					if sim.get_result() == 5: #qtrvsim.py error code for integrated assembly error
						assembly_error = True
						break

					sim.reset()
				
				if tests_passed == num_testcases and not cache_exit and not make_exit:
					was_accepted = 0 #mark as accepted

					scoring_testcase = sim.results[task_data["score"]["testcase"]]
					score = scoring_testcase[1] #TODO: can be changed to cache, now is set to cycles

				if timed_out:
					score = -1
					was_accepted = 2

				if assembly_error:
					raise Exception("Error in integrated assembly")

				if not cache_exit and not make_exit:
					sim.end_eval(task_data["score"]["testcase"])


			if cache_exit:
				score = -1
				was_accepted = 3
				sim.log = error_log

			if make_exit:
				score = -1
				was_accepted = 4
				sim.log = error_log

			if makefile_present:
				sim.run_make_clean()
				os.remove(os.path.join(os.path.dirname(filepath), "Makefile"))

			print(f"  submission {s[0]} evaluated, accepted: {was_accepted}, cycles: {score}")
			#print(sim.get_log())

			#TODO: commit changes to database
			db.update_submission(s[0])

			db.update_result(s[4], s[1], score, was_accepted, sim.get_log())
			
			#TODO: remove the directory after evaluation
			
			#remove submission.S and __ending_mem__ and __starting_mem__ files
			
			try:
				os.remove(filepath)
			except OSError as e:
				print(f"Error: {e.filename} - {e.strerror}.")

			try:
				os.rmdir(os.path.dirname(filepath))  # if not empty will not be deleted
			except OSError as e:
				print(f"Error: {e.filename} - {e.strerror}.")

			#wait for a second
			time.sleep(1)

		except Exception as e:
			try:
				if sim.get_result() == 5: #qtrvsim.py error code for integrated assembly error
					error_log = f"An error occurred during evaluation:\n"
					error_log += f"Error in integrated assembly.\n"
					
					#TODO: enable this line to show the stdout to the user
					#error_log += f"{sim.error_log}\n"
					
					#/_job_19596/submission.S:17:error:unknown instruction

					#parsing the error line numbers
					#error_line_num = re.match(r'.*:(\d+):.*', sim.error_log)
					#error_line_num = error_line_num.group(1) if error_line_num else "?"

					error_line_nums = re.findall(r'.*:(\d+):error:.*', sim.error_log, re.MULTILINE)
					error_line_nums = [int(num) for num in error_line_nums]

					error_types = re.findall(r'.*:\d+:error:(.*)$', sim.error_log, re.MULTILINE)

					error_lines = []
					if os.path.exists(filepath):
						with open(filepath, 'r') as f:
							lines = f.readlines()
							for num in error_line_nums:
								error_lines.append(lines[num-1].strip())

					for i, err in enumerate(error_lines):
						if len(error_types) > i and len(error_line_nums) > i:
							error_log += f"On line {error_line_nums[i]} in your code:\n"
							error_log += f"{error_types[i]}\nhere -->" + err + "\n"

					#error_log += f"On line {error_line_num} in your code:\n"
					#error_log += error_lines[0] if len(error_lines) > 0 else "\n"
					#error_log += "here -->" + error_lines[1] if len(error_lines) > 1 else "\n"
					#error_log += error_lines[2] if len(error_lines) > 2 else "\n"

					error_log += f"\nPlease check your code and try again."
					#error_log += f"\nPlease note, that %lo and %hi are not yet supported in the integrated assembly, and will thus throw an assembly error when no Makefile for compilation is present at the task.\n"

					db.update_submission(s[0])
					db.update_result(s[4], s[1], -1, 5, error_log)

				else:
					raise e

			except Exception as e:
				print(f"Error: {e}")
				error_log = f"An error occurred during evaluation:\n"
				error_log += f"{type(e).__name__}\n"
				error_log += f"Message: {e}\n"
				error_log += f"Traceback: {traceback.format_exc()}\n"
				error_log += f"Please create an issue with this error on GitLab: https://gitlab.fel.cvut.cz/b35apo/qtrvsim-eval-web/-/issues/new?issue[title]=Error%20in%20evaluator%20uid%20{s[4]}%20tid{s[1]}&issue[description]={type(e).__name__}%0A{urllib.parse.quote(str(traceback.format_exc()), safe='')}%0A{urllib.parse.quote(str(e), safe='')}"

				db.update_submission(s[0])
				db.update_result(s[4], s[1], -1, 99, error_log)


def evaluator_thread(num_submissions = 10, interval = 60):
	"""Run the evaluator thread."""
	while True:
		print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		evaluate_submissions(num_submissions)
		time.sleep(interval)

if __name__ == "__main__":
	num_submissions = 10	#number of submissions to evaluate at a time
	interval = 10			#seconds between evaluations
	while True:
		#print current time
		print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		evaluate_submissions(num_submissions)
		time.sleep(interval)