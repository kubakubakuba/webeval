import psycopg2
from dotenv import load_dotenv
import os

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

def get_user(username):
	"""Get user info"""
	(db, cursor) = connect()
	cursor.execute('SELECT id, password, salt, username, verified, email FROM users WHERE username = %s', (username,))
	user = cursor.fetchone()
	cursor.close()
	db.close()
	return user

def is_admin(username):
	"""Check if user is admin"""
	(db, cursor) = connect()
	cursor.execute('SELECT admin FROM users WHERE username = %s', (username,))
	admin = cursor.fetchone()
	cursor.close()
	db.close()
	return admin

def get_task(task_id):
	"""Get a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT name FROM tasks WHERE id = %s AND available = true', (task_id,))
	task = cursor.fetchone()
	cursor.close()
	db.close()
	return task

def get_task_path(task_id):
	"""Get the path to a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT path FROM tasks WHERE id = %s AND available = true', (task_id,))
	task = cursor.fetchone()
	cursor.close()
	db.close()
	return task

def verify_manual(token, username):
	"""Verify a user manually."""
	(db, cursor) = connect()
	cursor.execute("UPDATE users SET verified = true WHERE token = %s AND username = %s", (token, username))
	success = cursor.rowcount > 0
	
	db.commit()
	cursor.close()
	db.close()
	
	return success

def verify_auto(token, user, email):
	"""Verify a user automatically."""
	(db, cursor) = connect()
	cursor.execute("UPDATE users SET verified = true WHERE token = %s AND username = %s AND email = %s", (token, user, email))
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

def add_verify_code(username, token):
	"""Add a verification code for a user."""
	(db, cursor) = connect()
	cursor.execute("UPDATE users SET token = %s WHERE username = %s", (token, username,))
	
	db.commit()
	cursor.close()
	db.close()

def set_new_password(username, hashed_password, token):
	"""Set a new password for a user."""
	(db, cursor) = connect()
	cursor.execute("UPDATE users SET password = %s, token = NULL WHERE username = %s AND token = %s", (hashed_password, username, token))
	success = cursor.rowcount > 0

	db.commit()
	cursor.close()
	db.close()

	return success

def get_best_scores(taskid):
	"""Get the best scores for a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT users.username, results.score_last, results.result_file, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s ORDER BY results.score_last ASC', (taskid,))
	scores = cursor.fetchall()
	cursor.close()
	db.close()
	return scores

def get_last_user_submission(taskid, userid):
	"""Get a user's submission for a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT result, result_file, score_last, time FROM results WHERE taskid = %s AND userid = %s', (taskid, userid))
	submission = cursor.fetchone()
	cursor.close()
	db.close()
	return submission

def get_last_user_code(taskid, userid):
	"""Get a user's last code for a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT last_source FROM results WHERE taskid = %s AND userid = %s', (taskid, userid))
	code = cursor.fetchone()
	cursor.close()
	db.close()
	return code

def submit(user_id, task_id, code):
	"""Submit a solution."""
	(db, cursor) = connect()
	#insert into submissions and into results last_source
	cursor.execute('INSERT INTO submissions (userid, taskid, file) VALUES (%s, %s, %s)', (user_id, task_id, code))
	#update results last_source for userid and taskid
	cursor.execute('''
		INSERT INTO results (userid, taskid, last_source, result) 
		VALUES (%s, %s, %s, -1) 
		ON CONFLICT (userid, taskid) DO UPDATE SET last_source = EXCLUDED.last_source, result = -1
	''', (user_id, task_id, code))
	db.commit()
	cursor.close()
	db.close()

def get_username(userid):
	"""Get the username of a user."""
	(db, cursor) = connect()
	cursor.execute('SELECT username FROM users WHERE id = %s', (userid,))
	username = cursor.fetchone()
	cursor.close()
	db.close()
	return username