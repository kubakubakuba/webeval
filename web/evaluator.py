import mysql.connector
from db import db_config
import toml
import subprocess
from datetime import datetime
import re
import threading
import time
from subprocess import TimeoutExpired
import db
from qtrvsim import QtRVSim
import os

TIMEOUT_TIME = 10 #seconds

def fetch_submissions(count):
	"""Fetch the earliest <count> submissions from the database."""

	submissions = db.get_latest_submissions(count)

	#for each taskid fetch its task filename

	task_ids = [submission[0] for submission in submissions]

	if len(task_ids) == 0:
		print("  No submissions available to evaluate.")
		return None

	task_filenames = db.get_task_files(task_ids)

	#make a dictionary of taskid -> task filename
	task_filenames = {task[0]: task[1] for task in task_filenames}

	return (submissions, task_filenames)

def update_submission(submission_id, evaluated, result, score, result_file):
	"""Update a submission in the database."""
	#update the submission with the given id
	db.update_submission(evaluated, result, score, result_file, submission_id)

def evaluate_submissions(num_submissions = 10):
	fetch = fetch_submissions(num_submissions)
	if fetch is None:
		return None
	
	submissions, task_filenames = fetch

	for s in submissions:
		#get arguments from task toml file
		task_id = s[0]
		arguments = []
		was_accepted = 1 #was not accepted
		with open(task_filenames[task_id]) as f:
			task_data = toml.load(f)
			arguments = task_data['arguments']['run']

			num_testcases = len(task_data['testcases'])
			sim = QtRVSim(args=task_data["arguments"]["run"], submission_file=s[1])
			#sim.set_verbose(True)

			score = 0
			tests_passed = 0
			timed_out = False

			for i in range(num_testcases):
				if task_data["testcases"][i].get("do_compare_registers", False): #compare registers
					sim.set_do_compare_registers(True)
					sim.set_reference_ending_regs(task_data["testcases"][i]["reference_regs"][0])

				if task_data["testcases"][i].get("do_compare_memory", False): #compare memory
					sim.set_do_compare_memory(True)

					mem = task_data["testcases"][i]["reference_mem"][0]
					mem = {int(k, 16) : v for k, v in mem.items()} #rewrite the memory dict from 'address' : value to adress : value

					sim.set_reference_ending_memory(mem)

				if task_data["testcases"][i].get("do_set_starting_memory", False): #set starting memory
					mem = task_data["testcases"][i]["starting_mem"][0]
					mem = {int(k, 16) : v for k, v in mem.items()}#rewrite the memory dict from 'address' : value to adress : value

					sim.set_starting_memory(mem)

				#run the evaluation
				sim.run()
				sim.log_test_name(task_data["testcases"][i]["name"])
				
				if sim.get_result() == 0:
					tests_passed += 1

				if sim.get_result() == 2: #do not evaluate further testcases if one timed out
					timed_out = True
					break

				sim.reset()
			
			if tests_passed == num_testcases:
				was_accepted = 0
				sim.set_do_compare_registers(False)
				sim.set_do_compare_memory(False)
				sim.run()

				score_metric = task_data["score"]["metric"]
				score = sim.get_scores()[score_metric]

			if timed_out:
				score = -1
				was_accepted = 2

			sim.end_eval(task_data["score"]["metric"])

		result_filename = f"results/{s[2]}_{task_id}.log"

		#write stdout and stderr to a file
		with open(result_filename, 'w') as f:
			f.write(sim.get_log())

		print(f"  submission {s[0]} evaluated, accepted: {was_accepted}, cycles: {score}, result file: {result_filename}")
		update_submission(s[3], 1, was_accepted, score, result_filename)
		#remove the submission file
		#os.remove(s[1])

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