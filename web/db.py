import mysql.connector

db_config = {
	'user': 'qtrvsim',
	'password': 'QtRVSim_Admin!',
	'host': '158.101.208.70',
	'database': 'qtrvsim_web_eval',
	'port': 3306
}

def connect():
	"""Connect to the database."""
	db = mysql.connector.connect(**db_config)
	cursor = db.cursor()
	return (db, cursor)

def list_tasks():
	"""List all tasks."""
	(db, cursor) = connect()
	cursor.execute('SELECT id, name FROM tasks WHERE available = 1')
	tasks = cursor.fetchall()
	cursor.close()
	return tasks

def register(username, hashed_password, email, salt):
	"""Register a new user."""
	(db, cursor) = connect()
	#check if username is already taken
	cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
	user = cursor.fetchone()
	if user:
		cursor.close()
		return False
	cursor.execute('INSERT INTO users (username, password, email, salt) VALUES (%s, %s, %s, %s)', (username, hashed_password, email, salt))
	db.commit()
	cursor.close()
	return True

def login(username):
	"""Login a user."""
	(db, cursor) = connect()
	cursor.execute('SELECT id, password, salt, username FROM users WHERE username = %s', (username,))
	user = cursor.fetchone()
	cursor.close()
	return user

def submit(user_id, task_id, filepath):
	"""Submit a new task solution. Check if a submission for that same task by the same user exists, if so update it, otherwise create a new submission."""
	(db, cursor) = connect()

	# Check if a submission already exists
	cursor.execute('SELECT * FROM submissions WHERE userid = %s AND taskid = %s AND evaluated = 0', (user_id, task_id))
	submission = cursor.fetchone()
	submission_id = submission[0] if submission else None

	if submission:
		# Update the existing submission
		cursor.execute('UPDATE submissions SET filepath = %s WHERE id = %s', (filepath, submission_id,))
	else:
		# Create a new submission
		cursor.execute('INSERT INTO submissions (userid, taskid, filepath) VALUES (%s, %s, %s)', (user_id, task_id, filepath))

	db.commit()
	cursor.close()

def get_task(task_id):
	"""Get a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT name FROM tasks WHERE id = %s AND available = 1', (task_id,))
	task = cursor.fetchone()
	cursor.close()
	return task

def get_task_path(task_id):
	"""Get the path to a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT path FROM tasks WHERE id = %s AND available = 1', (task_id,))
	task = cursor.fetchone()
	cursor.close()
	return task

def get_user_submissions(user_id, task_id):
	"""Get all submissions of a user for a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT evaluated, result, score, result_file, time FROM submissions WHERE userid = %s AND taskid = %s ORDER BY time DESC LIMIT 1', (user_id, task_id))
	submissions = cursor.fetchall()
	if submissions:
		submission = submissions[0]
	else:
		submission = None
	cursor.close()
	return submission

def get_latest_scores(taskid):
	"""Get the latest scores of all users for a specific task."""
	(db, cursor) = connect()
	query = f"""
	SELECT s.userid, 
		CASE 
			WHEN MAX(s.time) = s.time AND s.evaluated = 1 AND s.result = 0 THEN s.score
			ELSE NULL
		END AS score,
		u.username
	FROM submissions s
	INNER JOIN users u ON s.userid = u.id
	WHERE s.taskid = {taskid}
	GROUP BY s.userid, u.username
	"""

	cursor.execute(query)
	results = cursor.fetchall()

	cursor.close()

	return results