import mysql.connector
from db import db_config
import toml
import subprocess
from datetime import datetime
import re

def fetch_submissions(count = 10):
	"""Fetch the earliest <count> submissions from the database."""
	conn = mysql.connector.connect(**db_config)

	if not conn.is_connected():
		print("Could not connect to database, no submissions fetched.")
		return None

	cursor = conn.cursor()
	#select the earliest <count> submissions that have not been evaluated yet
	cursor.execute("SELECT taskid, filepath, userid, id FROM submissions WHERE evaluated = 0 ORDER BY id ASC LIMIT %s", (count,))
	submissions = cursor.fetchall()

	#for each taskid fetch its task filename

	task_ids = [submission[0] for submission in submissions]

	if len(task_ids) == 0:
		print("No submissions available to evaluate.")
		return None

	cursor.execute("SELECT id, path FROM tasks WHERE id IN (%s)" % (','.join(['%s'] * len(task_ids))), task_ids)
	task_filenames = cursor.fetchall()

	#make a dictionary of taskid -> task filename
	task_filenames = {task[0]: task[1] for task in task_filenames}

	cursor.close()

	return (submissions, task_filenames)

def update_submission(submission_id, evaluated, result, score, result_file):
	"""Update a submission in the database."""
	conn = mysql.connector.connect(**db_config)

	if not conn.is_connected():
		print("Could not connect to database, no submission updated.")
		return None

	cursor = conn.cursor()
	#update the submission with the given id
	cursor.execute("UPDATE submissions SET evaluated = %s, result = %s, score = %s, result_file = %s WHERE id = %s", (evaluated, result, score, result_file, submission_id))
	conn.commit()

	cursor.close()

if __name__ == "__main__":
	fetch = fetch_submissions()
	if fetch is None:
		print("No submissions fetched.")
		exit()
	
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
		print(f"evaluating submission {s[0]}, with arguments: {arguments}, filename: {s[1]}")
		command.extend(arguments)

		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = process.communicate()

		time_evaluated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		result_filename = f"results/{s[2]}_{task_id}.log"

		stdout_text = stdout.decode('utf-8')
		stderr_text = stderr.decode('utf-8')

		#write stdout and stderr to a file
		with open(result_filename, 'w') as f:
			f.write(f"evaluation started on: {time_evaluated}\n")
			f.write("stdout:\n")
			f.write(stdout_text)
			f.write("\nstderr:\n")
			f.write(stderr_text)

		was_accepted = 0 #TODO: check if the output is correct

		match = re.search(r"^cycles: (\d+)$", stdout_text, re.MULTILINE)

		if match:
			cycles = int(match.group(1))
		else:
			cycles = None

		print(f"submission {s[0]} evaluated, accepted: {was_accepted}, cycles: {cycles}, result file: {result_filename}")
		#update the submission in the database

		update_submission(s[3], 1, was_accepted, cycles, result_filename)