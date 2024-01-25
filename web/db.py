import mysql.connector
from db_connect import db_config

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
	db.close()
	return tasks

def register(username, hashed_password, email, salt, token):
	"""Register a new user."""
	(db, cursor) = connect()
	#check if username is already taken
	cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
	user = cursor.fetchone()
	if user:
		cursor.close()
		db.close()
		return False
	cursor.execute('INSERT INTO users (username, password, email, salt, token) VALUES (%s, %s, %s, %s, %s)', (username, hashed_password, email, salt, token))
	db.commit()
	cursor.close()
	db.close()
	return True

def login(username):
	"""Login a user."""
	(db, cursor) = connect()
	cursor.execute('SELECT id, password, salt, username, verified FROM users WHERE username = %s', (username,))
	user = cursor.fetchone()
	cursor.close()
	db.close()
	return user

def submit(user_id, task_id, filepath):
	"""Submit a new task solution. Check if a submission for that same task by the same user exists, if so update it, otherwise create a new submission."""
	(db, cursor) = connect()

	# Check if a submission already exists
	#cursor.execute('SELECT * FROM submissions WHERE userid = %s AND taskid = %s AND evaluated = 0', (user_id, task_id))
	#submission = cursor.fetchone()
	#submission_id = submission[0] if submission else None

	#if submission:
		# Update the existing submission
	#	cursor.execute('UPDATE submissions SET filepath = %s WHERE id = %s', (filepath, submission_id,))
	#else:
		# Create a new submission
	cursor.execute('INSERT INTO submissions (userid, taskid, filepath, evaluated) VALUES (%s, %s, %s, %s)', (user_id, task_id, filepath, 0))

	db.commit()
	cursor.close()
	db.close()

def get_task(task_id):
	"""Get a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT name FROM tasks WHERE id = %s AND available = 1', (task_id,))
	task = cursor.fetchone()
	cursor.close()
	db.close()
	return task

def get_task_path(task_id):
	"""Get the path to a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT path FROM tasks WHERE id = %s AND available = 1', (task_id,))
	task = cursor.fetchone()
	cursor.close()
	db.close()
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

	db.close()
	return submission

def get_latest_score(taskid, user_id):
	"""Get the latest score for a specific user and taskid."""
	(db, cursor) = connect()
	cursor.execute('''
		SELECT s.userid, s.score, u.username 
		FROM submissions s
		INNER JOIN users u ON s.userid = u.id
		WHERE s.taskid = %s AND s.userid = %s 
		ORDER BY s.time DESC LIMIT 1
	''', (taskid, user_id))
	scores = cursor.fetchall()
	if scores:
		score = scores[0]
	else:
		score = None
	cursor.close()

	db.close()
	return score

def get_best_scores(taskid):
	"""Get the best scores of all users for a specific task."""
	(db, cursor) = connect()
	query = f"""
		SELECT s.userid, MIN(s.score), u.username
		FROM submissions s
		INNER JOIN users u ON s.userid = u.id
		WHERE s.taskid = %s AND s.score > 0 AND s.result = 0
		GROUP BY s.userid, u.username
	"""

	cursor.execute(query, (taskid,))
	results = cursor.fetchall()

	cursor.close()

	db.close()
	return results

def update_submission(evaluated, result, score, result_file, submission_id):
	(db, cursor) = connect()
	print(f"  updating submission {submission_id} with evaluated: {evaluated}, result: {result}, score: {score}, result_file: {result_file}")
	cursor.execute("UPDATE submissions SET evaluated = %s, result = %s, score = %s, result_file = %s WHERE id = %s", (evaluated, result, score, result_file, submission_id))
	db.commit()
	cursor.close()
	db.close()

def get_latest_submissions(count):
	"""Get all submissions."""
	(db, cursor) = connect()
	#select the earliest <count> submissions that have not been evaluated yet
	cursor.execute("SELECT taskid, filepath, userid, id FROM submissions WHERE evaluated = 0 ORDER BY id ASC LIMIT %s", (count,))
	submissions = cursor.fetchall()
	cursor.close()
	db.close()
	return submissions

def get_task_files(task_ids):
	"""Get task filenames"""
	(db, cursor) = connect()
	cursor.execute("SELECT id, path FROM tasks WHERE id IN (%s)" % (','.join(['%s'] * len(task_ids))), task_ids)
	task_files = cursor.fetchall()
	cursor.close()
	db.close()
	return task_files

def verify_manual(token, username):
	"""Verify a user manually."""
	(db, cursor) = connect()
	cursor.execute("UPDATE users SET verified = 1 WHERE token = %s AND username = %s", (token, username))
	success = cursor.rowcount > 0
	
	db.commit()
	cursor.close()
	db.close()
	
	return success

def verify_auto(token, user, email):
	"""Verify a user automatically."""
	(db, cursor) = connect()
	cursor.execute("UPDATE users SET verified = 1 WHERE token = %s AND username = %s AND email = %s", (token, user, email))
	success = cursor.rowcount > 0

	db.commit()
	cursor.close()
	db.close()

	return success

def reset_token(username):
	"""Reset a user's token."""
	(db, cursor) = connect()
	cursor.execute("UPDATE users SET token = NULL WHERE username = %s", (username,))
	db.commit()
	cursor.close()
	db.close()