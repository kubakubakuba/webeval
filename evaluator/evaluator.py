import toml
from datetime import datetime
import time
import evaldb as db
from qtrvsim import QtRVSim
import os

TIMEOUT_TIME = 10 #seconds

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

	#for each task_filename add ../web/ to the beginning
	task_filenames = {task_id: "../web/" + task_filename for task_id, task_filename in task_filenames.items()}

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

		#get PID of the running evaluator
		pid = os.getpid()
		#save file into /tmp/qtrvsim_web_eval/_job_PID/submission.S
		filepath = f"/tmp/qtrvsim_web_eval/_job_{pid}/submission.S"
		#make the directory if it does not exist
		os.makedirs(os.path.dirname(filepath), exist_ok=True)
		#save the file from s[2] to filepath
		with open(filepath, 'w') as f:
			f.write(s[2])

		print(task_filenames)

		with open(task_filenames[task_id]) as f:
			task_data = toml.load(f)
			arguments = task_data['arguments']['run']

			num_testcases = len(task_data['testcases'])
			sim = QtRVSim(args=task_data["arguments"]["run"], submission_file=filepath, working_dir=os.path.dirname(filepath))
			#sim.set_verbose(True)

			score = 0
			tests_passed = 0
			timed_out = False

			for i in range(num_testcases):
				#if flag is set or reference_regs are not empty, compare registers
				if task_data["testcases"][i].get("do_compare_registers", False) or task_data["testcases"][i].get("reference_regs", None) != None:
					sim.set_do_compare_registers(True)
					sim.set_reference_ending_regs(task_data["testcases"][i]["reference_regs"][0])

				if task_data["testcases"][i].get("do_compare_memory", False) or task_data["testcases"][i].get("reference_mem", None) != None:
					sim.set_do_compare_memory(True)

					mem = task_data["testcases"][i]["reference_mem"][0]
					mem = {int(k, 16) : v for k, v in mem.items()} #rewrite the memory dict from 'address' : value to adress : value

					sim.set_reference_ending_memory(mem)

				if task_data["testcases"][i].get("do_set_starting_memory", False) or task_data["testcases"][i].get("starting_mem", None) != None:
					mem = task_data["testcases"][i]["starting_mem"][0]
					mem = {int(k, 16) : v for k, v in mem.items()}#rewrite the memory dict from 'address' : value to adress : value

					sim.set_starting_memory(mem)

				#run the evaluation
				sim.run(task_data["testcases"][i]["name"])
				sim.log_test_name(task_data["testcases"][i]["name"])
				
				if sim.get_result() == 0:
					tests_passed += 1

				if sim.get_result() == 2: #do not evaluate further testcases if one timed out
					timed_out = True
					break

				sim.reset()
			
			if tests_passed == num_testcases:
				was_accepted = 0 #mark as accepted

				scoring_testcase = sim.results[task_data["score"]["testcase"]]
				score = scoring_testcase[1] #TODO: can be changed to cache, now is set to cycles

			if timed_out:
				score = -1
				was_accepted = 2

			sim.end_eval(task_data["score"]["testcase"])

		print(f"  submission {s[0]} evaluated, accepted: {was_accepted}, cycles: {score}")
		db.update_submission(s[0])
		db.update_result(s[4], s[1], score, was_accepted, sim.get_log())
		
		#TODO: remove the directory after evaluation
		#remove submission.S and __ending_mem__ and __starting_mem__ files
		os.remove(filepath)
		os.remove(sim.mem_output_file)
		os.remove(sim.starting_memory_file)

		os.rmdir(os.path.dirname(filepath)) #if is notempty will not be deleted

		#wait for a second
		time.sleep(1)

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