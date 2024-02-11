import psycopg2
from dotenv import load_dotenv
import os
import argparse

load_dotenv("../.env")

db_config = {
	'user': os.getenv('DB_USER'),
	'password': os.getenv('DB_PASSWORD'),
	'host': os.getenv('DB_HOST'),
	'database': os.getenv('DB_DATABASE'),
	'port': os.getenv('DB_PORT'),
	'sslmode': 'require',
	'connect_timeout': 10
}

def connect():
	"""Connect to the database."""
	db = psycopg2.connect(**db_config)
	cursor = db.cursor()
	return (db, cursor)

def list_tasks():
	"""List all tasks."""
	(db, cursor) = connect()
	cursor.execute('SELECT id, name FROM tasks WHERE available = true')
	tasks = cursor.fetchall()
	cursor.close()
	db.close()
	return tasks

TEMPLATE = """[task]
name = "Sample Task"
template = "S_templates/sample.S"

description = '''
# Your task description goes here (formatted in markdown).
## Use this as a template.
Starting memory is set by setting testcases.starting_mem, ending memory check is done by
setting testcases.reference_mem.
The ending values in registers are checked by setting testcases.reference_regs.
The scoring task is done by referencing the test name in the score.testcase field.
'''

[arguments]
run = "--d-regs --dump-cycles"

[[inputs]]
data_in = "Two values in memory starting at address 0x400."
data_out = "The values in registers, the sum in register a2, and the sum in memory after the two values."
description = "Loading of values from memory."

[[testcases]]
name = "test01"

[[testcases.reference_regs]]
a0 = 5
a1 = 10
a2 = 15

[[testcases.starting_mem]]
0x400 = [5, 10]

[[testcases.reference_mem]]
0x408 = [15]

[[testcases]]
name = "test02"

[[testcases.starting_mem]]
0x400 = [150, 200]

[[testcases.reference_mem]]
0x408 = [350]

[[testcases]]
name = "test03"

[[testcases.starting_mem]]
0x400 = [1523, 1459]

[[testcases.reference_mem]]
0x408 = [2982]

[[testcases]]
name = "scoring testcase"
private = true

[[testcases.starting_mem]]
0x400 = [1711, 1989]

[[testcases.reference_mem]]
0x408 = [3700]

[score]
description = "Runtime of the program in cycles."
testcase = "scoring testcase"
"""

def create_task():
#get the task file name from the user input
	task_real_name = input("Enter the task name (will be shown to user): ")

	task_name = input("Enter the task file name: ")
	if task_name.endswith(".toml"):
		task_name = task_name[:-5]

	#if there are some slashes, raise an error
	if "/" in task_name:
		print("Invalid filename! File is automatically placed in web/tasks/task.toml")
		exit()

	if "." in task_name:
		print("Invalid filename!")
		exit()

	filepath = f"tasks/{task_name}.toml"
	
	if os.path.isfile(f"../web/{filepath}"):
		print("File already exists!")
		exit()

	with open(f"../web/{filepath}", "w") as file:
		file.write(TEMPLATE)

	print("Task file created!")

	#add the task to the database
	(db, cursor) = connect()
	cursor.execute('INSERT INTO tasks (name, path) VALUES (%s, %s)', (task_real_name, filepath))	
	db.commit()
	cursor.close()
	db.close()

	print("Task inserted into database!")

def rename_task(task_id):
	new_name = input("Enter the new task name (will be shown to user): ")
	if new_name.endswith(".toml"):
		new_name = new_name[:-5]
	filename = input("Enter the new task filename: ")
	filepath = f"tasks/{filename}.toml"

	(db, cursor) = connect()
	cursor.execute('UPDATE tasks SET name = %s, path = %s WHERE id = %s', (new_name, filepath, task_id))
	db.commit()
	cursor.close()
	db.close()

	print(f"Task {task_id} renamed!")

def delete_task(task_id):
	(db, cursor) = connect()
	cursor.execute('UPDATE tasks SET available = false WHERE id = %s', (task_id,))
	db.commit()
	cursor.close()
	db.close()

	print("Task deleted!")

def list_tasks():
	(db, cursor) = connect()
	cursor.execute('SELECT id, name, path FROM tasks WHERE available = true')
	tasks = cursor.fetchall()
	cursor.close()
	db.close()
	
	print("{:<10} {:<40} {:<30}".format('ID', 'Name', 'Path'))
	for t in tasks:
		print("{:<10} {:<40} {:<30}".format(t[0], t[1], t[2]))

def list_all_tasks():
	(db, cursor) = connect()
	cursor.execute('SELECT id, name, path, available FROM tasks')
	tasks = cursor.fetchall()
	cursor.close()
	db.close()
	
	print("{:<10} {:<40} {:<30} {:<15}".format('ID', 'Name', 'Path', 'Available'))
	for t in tasks:
		print("{:<10} {:<40} {:<30} {:<15}".format(t[0], t[1], t[2], 'true' if t[3] else 'false'))

def make_task_available(task_id):
	(db, cursor) = connect()
	cursor.execute('UPDATE tasks SET available = true WHERE id = %s', (task_id,))
	db.commit()
	cursor.close()
	db.close()

	print("Task made available!")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Command line parser")

	parser.add_argument('-c', '--create', action='store_true', help='Create a new task with a filename')
	parser.add_argument('-d', '--delete', type=int, help='Delete a task with an ID')
	parser.add_argument('-l', '--list', action='store_true', help='List all tasks')
	parser.add_argument('-a', '--list-all', action='store_true', help='List all tasks, including unavailable ones')
	parser.add_argument('-m', '--make-available', type=int, help='Make a task available')
	parser.add_argument('-r', '--rename', type=int, help='Rename a task')

	try:
		# Parse the arguments
		args = parser.parse_args()

		# Now you can check if the 'create', 'delete' or 'list' options were provided
		if args.create:
			create_task()
		elif args.delete is not None:
			delete_task(args.delete)
		elif args.list:
			list_tasks()
		elif args.list_all:
			list_all_tasks()
		elif args.rename:
			rename_task(args.rename)
		elif args.make_available:
			make_task_available(args.make_available)
		else:
			print("No valid arguments provided. Use -h for help.")
	except argparse.ArgumentError:
		print("Error parsing arguments")
		exit(1)

