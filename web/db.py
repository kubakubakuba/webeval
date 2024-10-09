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
	cursor.execute('SELECT id, name FROM tasks WHERE available = true ORDER BY sequence ASC')
	tasks = cursor.fetchall()
	cursor.close()
	db.close()
	return tasks

def list_tasks_with_filepath():
	"""List all tasks with their file path."""
	(db, cursor) = connect()
	cursor.execute('SELECT id, name, path, available FROM tasks ORDER BY sequence ASC')
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
	cursor.execute('SELECT id, password, salt, username, verified, email, token, display_name, country, organization, "group", visibility FROM users WHERE username = %s', (username,))
	user = cursor.fetchone()
	cursor.close()
	db.close()
	return user

def get_user_by_id(userid):
	"""Get user info"""
	(db, cursor) = connect()
	cursor.execute('SELECT id, password, salt, username, verified, email, token, display_name, country, organization, "group", visibility FROM users WHERE id = %s', (userid,))
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

def is_admin_by_id(userid):
	"""Check if user is admin"""
	(db, cursor) = connect()
	cursor.execute('SELECT admin FROM users WHERE id = %s', (userid,))
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

def get_task_name(task_id):
	"""Get the name of a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT name FROM tasks WHERE id = %s AND available = true', (task_id,))
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
	return get_best_scores_for_verified(taskid)
	
	(db, cursor) = connect()
	cursor.execute('SELECT users.username, results.score_best, results.result_file, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s ORDER BY results.score_last ASC', (taskid,))
	scores = cursor.fetchall()
	cursor.close()
	db.close()
	return scores

def get_best_scores_for_verified(taskid):
	"""Get the best scores for a task for only verified users."""
	(db, cursor) = connect()
	cursor.execute('SELECT users.username, results.score_best, results.result_file, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true ORDER BY results.score_last ASC', (taskid,))
	scores = cursor.fetchall()
	cursor.close()
	db.close()
	return scores

def get_user_displaynames():
	"""Get all user display names."""
	(db, cursor) = connect()
	cursor.execute('SELECT username, display_name FROM users')
	displaynames = cursor.fetchall()
	cursor.close()
	db.close()
	return displaynames

def get_best_scores_for_verified_grouporg(taskid, group, organization, curr_user):
	"""Get the best scores for a task for only verified users, that have visibility set to public (0) or are at the same group or the same organization."""
	(db, cursor) = connect()
	cursor.execute('SELECT users.username, results.score_best, results.result_file, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND (users.visibility = 0 OR (users."group" = %s AND users.visibility = 2) OR (users.organization = %s AND users.visibility = 1) OR (users.id = %s)) ORDER BY results.score_last ASC', (taskid, group, organization, curr_user))
	scores = cursor.fetchall()
	cursor.close()
	db.close()
	return scores

def get_active_tasks():
	"""Get all active tasks."""
	(db, cursor) = connect()
	cursor.execute('SELECT id, name FROM tasks WHERE available = true ORDER BY sequence ASC')
	tasks = cursor.fetchall()
	cursor.close()
	db.close()
	return tasks

def get_best_only_scores(taskid):
	"""Get the best scores for a task."""
	(db, cursor) = connect()
	cursor.execute('SELECT users.username, results.score_best, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND results.score_best > 0 ORDER BY results.score_last ASC', (taskid,))
	scores = cursor.fetchall()
	cursor.close()
	db.close()
	return scores

def get_best_only_scores_for_public(taskid):
	"""Get the best scores for a task for public users."""
	(db, cursor) = connect()
	cursor.execute('SELECT users.username, results.score_best, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND users.visibility = 0 AND results.score_best > 0 ORDER BY results.score_best ASC', (taskid,))
	scores = cursor.fetchall()
	cursor.close()
	db.close()
	return scores

def get_best_only_scores_for_group(taskid, group):
	"""Get the best scores for a task for a group."""
	(db, cursor) = connect()
	cursor.execute('SELECT users.username, results.score_best, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND users."group" = %s AND users.visibility IN (2, 0) AND results.score_best > 0 ORDER BY results.score_last ASC', (taskid, group))
	scores = cursor.fetchall()
	cursor.close()
	db.close()
	return scores

def get_best_only_scores_for_org(taskid, org):
	"""Get the best scores for a task for an organization."""
	(db, cursor) = connect()
	cursor.execute('SELECT users.username, results.score_best, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND users.organization = %s AND users.visibility IN (1, 0) AND results.score_best > 0 ORDER BY results.score_last ASC', (taskid, org))
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

def get_users():
	"""Get all users."""
	(db, cursor) = connect()
	cursor.execute('SELECT id, username, email, verified, token, country, organization, "group", display_name FROM users')
	users = cursor.fetchall()
	cursor.close()
	db.close()
	return users

def get_user_code(taskid, userid, is_latest):
	"""Get a user's code for a task."""
	(db, cursor) = connect()
	if is_latest:
		cursor.execute('SELECT last_source FROM results WHERE taskid = %s AND userid = %s', (taskid, userid))
	else:
		cursor.execute('SELECT best_source FROM results WHERE taskid = %s AND userid = %s', (taskid, userid))
	code = cursor.fetchone()
	cursor.close()
	db.close()
	return code

def ban_user(userid):
	"""Ban a user."""
	#set a verified to false and token to "_banned_"
	(db, cursor) = connect()
	cursor.execute('UPDATE users SET verified = false, token = %s WHERE id = %s', ("_banned_", userid))
	db.commit()
	cursor.close()
	db.close()
	return True

def unban_user(userid):
	"""Unban a user."""
	#set a verified to true and token to NULL
	(db, cursor) = connect()
	cursor.execute('UPDATE users SET verified = true, token = NULL WHERE id = %s', (userid,))
	db.commit()
	cursor.close()
	db.close()
	return True

def is_user_banned(userid):
	"""Check if a user is banned."""
	#if user is not verified and token is "_banned_" then user is banned
	(db, cursor) = connect()
	cursor.execute('SELECT verified, token FROM users WHERE id = %s', (userid,))
	user = cursor.fetchone()
	cursor.close()
	db.close()
	return user[0] == False and user[1] == "_banned_"

def reorder_tasks(order):
	"""Reorder tasks."""
	#order is the list of which the ids should be placed
	#for each id, set the sequence to the order[i]
	#ids start from 1, but the list starts from 0 index

	(db, cursor) = connect()
	for i in range(len(order)):
		cursor.execute('UPDATE tasks SET sequence = %s WHERE id = %s', (i+1, order[i]))
	
	db.commit()
	cursor.close()
	db.close()

def rename_task(taskid, newname):
	"""Rename a task."""
	(db, cursor) = connect()
	cursor.execute('UPDATE tasks SET name = %s WHERE id = %s', (newname, taskid))
	db.commit()
	cursor.close()
	db.close()

def task_change_path(taskid, newpath):
	"""Change the path of a task."""
	(db, cursor) = connect()
	cursor.execute('UPDATE tasks SET path = %s WHERE id = %s', (newpath, taskid))
	db.commit()
	cursor.close()
	db.close()

def get_unavailable_tasks():
	"""Get all unavailable tasks."""
	(db, cursor) = connect()
	cursor.execute('SELECT id, name FROM tasks WHERE available = false ORDER BY sequence ASC')
	tasks = cursor.fetchall()
	cursor.close()
	db.close()
	return tasks

def set_task_availability(taskid, available):
	"""Set the availability of a task."""
	assert available == True or available == False

	(db, cursor) = connect()
	cursor.execute('UPDATE tasks SET available = %s WHERE id = %s', (available, taskid))
	db.commit()
	cursor.close()
	db.close()

def create_new_task(path):
	"""Create a new task."""
	(db, cursor) = connect()
	cursor.execute('INSERT INTO tasks (name, path, available) VALUES (%s, %s, true)', (path, path))
	db.commit()
	cursor.close()
	db.close()

def reset_org(user_id):
	"""Reset the organization and country of a user."""
	(db, cursor) = connect()
	cursor.execute('UPDATE users SET organization = NULL, country = NULL WHERE id = %s', (user_id,))
	db.commit()
	cursor.close()
	db.close()

def set_org(user_id, country, org):
	"""Set the organization and country of a user."""
	(db, cursor) = connect()
	cursor.execute('UPDATE users SET organization = %s, country = %s WHERE id = %s', (org, country, user_id))
	db.commit()
	cursor.close()
	db.close()

def change_displayname(user_id, displayname):
	"""Change the display name of a user."""
	(db, cursor) = connect()
	cursor.execute('UPDATE users SET display_name = %s WHERE id = %s', (displayname, user_id))
	db.commit()
	cursor.close()
	db.close()

def set_group(user_id, group):
	"""Change the group of a user."""
	(db, cursor) = connect()
	cursor.execute('UPDATE users SET "group" = %s WHERE id = %s', (group, user_id))
	db.commit()
	cursor.close()
	db.close()

def change_privacy(user_id, privacy):
	"""Change the privacy of a user."""
	(db, cursor) = connect()
	cursor.execute('UPDATE users SET visibility = %s WHERE id = %s', (privacy, user_id))
	db.commit()
	cursor.close()
	db.close()

def reset_results_user(user_id):
	"""Reset the results of a user."""
	# SELECT score_best, score_last, result, taskid FROM results WHERE userid = 4;
	# score_best | score_last | result | taskid
	#------------+------------+--------+--------
	#          0 |          0 |      1 |      5
	#          4 |          4 |      0 |      1
	#set the result to 0 for every task
	(db, cursor) = connect()
	cursor.execute('UPDATE results SET result = 100, score_best = 0, score_last = 0 WHERE userid = %s', (user_id,))
	db.commit()
	cursor.close()
	db.close()

def is_banned(user_id):
	"""Check if a user is banned."""
	(db, cursor) = connect()
	cursor.execute('SELECT verified, token FROM users WHERE id = %s', (user_id,))
	user = cursor.fetchone()
	cursor.close()
	db.close()
	return user[0] == False and user[1] == "_banned_"