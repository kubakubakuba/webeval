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
		with open(task_filenames[task_id]) as f:
			task_data = toml.load(f)
			arguments = task_data['arguments']['run']

		#run the task in qtrvsim_cli with the given arguments, dump the output into a file results/userid_taskid.log
		arguments = arguments.split()
		command = ["qtrvsim_cli"] + arguments + ["--asm", s[1]]
		print(f"  evaluating submission {s[0]}, with arguments: {arguments}, filename: {s[1]}")
		command.extend(arguments)

		killed = False

		try:
			process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			stdout, stderr = process.communicate(timeout=TIMEOUT_TIME)
		except TimeoutExpired:
			process.kill()
			stdout, stderr = None, None
			killed = True
			print(f"\033[91m  submission {s[0]} for {task_filenames[task_id].split('/')[1]} timed out\033[0m")

		time_evaluated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		result_filename = f"results/{s[2]}_{task_id}.log"

		stdout_text =  "" if killed else stdout.decode('utf-8')
		stderr_text = f'Killed after {TIMEOUT_TIME} seconds.' if killed else stderr.decode('utf-8')

		#write stdout and stderr to a file
		with open(result_filename, 'w') as f:
			f.write(f"evaluation started on: {time_evaluated}\n")
			f.write("stdout:\n")
			f.write(stdout_text)
			f.write("\nstderr:\n")
			f.write(stderr_text)

		was_accepted = 0 #TODO: check if the output is correct

		match = re.search(r"^cycles: (\d+)$", stdout_text, re.MULTILINE)

		if (match is not None) and not killed:
			cycles = int(match.group(1))
		else:
			cycles = -1

		#TODO: sample evaluation, if cycles if less than zero
		if cycles < 0:
			was_accepted = 1

		if killed:
			was_accepted = 2

		print(f"  submission {s[0]} evaluated, accepted: {was_accepted}, cycles: {cycles}, result file: {result_filename}")
		update_submission(s[3], 1, was_accepted, cycles, result_filename)
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