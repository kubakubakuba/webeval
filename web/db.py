import psycopg2
from dotenv import load_dotenv
import os
import json

# Load .env from /app/.env in Docker or ../.env locally
env_path = "/app/.env" if os.path.exists("/app/.env") else "../.env"
load_dotenv(env_path)

db_config = {
	'user': os.getenv('DB_USER'),
	'password': os.getenv('DB_PASSWORD'),
	'host': os.getenv('DB_HOST'),
	'database': os.getenv('DB_DATABASE'),
	'port': os.getenv('DB_PORT'),
	'sslmode': os.getenv('DB_SSLMODE', 'prefer'),
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

def can_user_submit(userid):
	"""Check if user can submit tasks"""
	(db, cursor) = connect()
	cursor.execute('SELECT can_submit FROM users WHERE id = %s', (userid,))
	result = cursor.fetchone()
	cursor.close()
	db.close()
	return result[0] if result else False

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

def get_task_path_admin(task_id):
	"""Get the path to a task (admin - no availability check)."""
	(db, cursor) = connect()
	cursor.execute('SELECT path FROM tasks WHERE id = %s', (task_id,))
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

def get_best_scores_for_verified_grouporg(taskid, group, organization, curr_user, is_admin=False):
	"""Get the best scores for a task for only verified users, that have visibility set to public (0) or are at the same group or the same organization."""
	(db, cursor) = connect()
	# Use COALESCE to handle NULL curr_user (anonymous users) - compare against a UUID that won't match any real user
	if is_admin:
		# Admin can see all results regardless of visibility
		cursor.execute('SELECT users.username, results.score_best, results.result_file, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND results.score_best IS NOT NULL AND results.score_best > 0 ORDER BY results.score_best ASC', (taskid,))
	else:
		cursor.execute('SELECT users.username, results.score_best, results.result_file, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND results.score_best IS NOT NULL AND results.score_best > 0 AND (users.visibility = 0 OR (users."group" = %s AND users.visibility = 2) OR (users.organization = %s AND users.visibility = 1) OR (users.id = COALESCE(%s::uuid, \'00000000-0000-0000-0000-000000000000\'::uuid))) ORDER BY results.score_best ASC', (taskid, group, organization, curr_user))
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
	cursor.execute('SELECT users.username, results.score_best, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND results.score_best > 0 ORDER BY results.score_best ASC', (taskid,))
	scores = cursor.fetchall()
	cursor.close()
	db.close()
	return scores

def get_best_only_scores_for_public(taskid, is_admin=False):
	"""Get the best scores for a task for public users."""
	(db, cursor) = connect()
	if is_admin:
		# Admin can see all results
		cursor.execute('SELECT users.username, results.score_best, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND results.score_best > 0 ORDER BY results.score_best ASC', (taskid,))
	else:
		cursor.execute('SELECT users.username, results.score_best, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND users.visibility = 0 AND results.score_best > 0 ORDER BY results.score_best ASC', (taskid,))
	scores = cursor.fetchall()
	cursor.close()
	db.close()
	return scores

def get_best_only_scores_for_group(taskid, group, is_admin=False):
	"""Get the best scores for a task for a group."""
	(db, cursor) = connect()
	if is_admin:
		# Admin can see all results in the group
		cursor.execute('SELECT users.username, results.score_best, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND users."group" = %s AND results.score_best > 0 ORDER BY results.score_last ASC', (taskid, group))
	else:
		cursor.execute('SELECT users.username, results.score_best, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND users."group" = %s AND users.visibility IN (2, 0) AND results.score_best > 0 ORDER BY results.score_last ASC', (taskid, group))
	scores = cursor.fetchall()
	cursor.close()
	db.close()
	return scores

def get_best_only_scores_for_org(taskid, org, is_admin=False):
	"""Get the best scores for a task for an organization."""
	(db, cursor) = connect()
	if is_admin:
		# Admin can see all results in the organization
		cursor.execute('SELECT users.username, results.score_best, results.userid FROM results INNER JOIN users ON results.userid = users.id WHERE results.taskid = %s AND users.verified = true AND users.organization = %s AND results.score_best > 0 ORDER BY results.score_last ASC', (taskid, org))
	else:
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
	cursor.execute('SELECT id, username, email, verified, token, country, organization, "group", display_name, can_submit FROM users')
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
	# Get the next sequence number (max + 1)
	cursor.execute('SELECT COALESCE(MAX(sequence), 0) + 1 FROM tasks')
	next_sequence = cursor.fetchone()[0]
	cursor.execute('INSERT INTO tasks (name, path, available, sequence) VALUES (%s, %s, true, %s)', (path, path, next_sequence))
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

def set_can_submit(user_id, can_submit):
	"""Set whether a user can submit solutions."""
	(db, cursor) = connect()
	cursor.execute('UPDATE users SET can_submit = %s WHERE id = %s', (can_submit, user_id))
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
	#set the result to NULL for every task so the trigger can update best score on next submission
	(db, cursor) = connect()
	cursor.execute('UPDATE results SET result = 100, score_best = NULL, score_last = NULL WHERE userid = %s', (user_id,))
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

def reevaluate_task(task_id, user_id, is_best):
	"""Reevaluate a task for a user."""
	(db, cursor) = connect()
	#insert the latest or best source code

	source = None

	if is_best:
		cursor.execute('SELECT best_source FROM results WHERE taskid = %s AND userid = %s', (task_id, user_id))
		source = cursor.fetchone()

	else:
		cursor.execute('SELECT last_source FROM results WHERE taskid = %s AND userid = %s', (task_id, user_id))
		source = cursor.fetchone()

	if source:
		cursor.execute('INSERT INTO submissions (userid, taskid, file) VALUES (%s, %s, %s)', (user_id, task_id, source))
		# Also update last_source in results so the evaluator can properly update best_source via trigger
		cursor.execute('UPDATE results SET result = -1, score_best = NULL, score_last = NULL, best_source = NULL, last_source = %s WHERE taskid = %s AND userid = %s', (source[0], task_id, user_id))
	else:
		cursor.execute('UPDATE results SET result = -1, score_best = NULL, score_last = NULL, best_source = NULL, last_source = NULL WHERE taskid = %s AND userid = %s', (task_id, user_id))

	db.commit()
	cursor.close()
	db.close()

def batch_import_users(users_data):
	"""
	Batch import users from CSV data.
	
	Args:
		users_data: List of dictionaries with keys: email, username, display_name, country, organization, group, visibility, can_submit
		
	Returns:
		Tuple of (success_list, error_list)
		success_list: List of successfully imported users
		error_list: List of error messages
	"""
	import uuid
	import hashlib
	
	errors = []
	success = []
	
	# Validation phase - check all data before importing
	(db, cursor) = connect()
	
	try:
		# Check for duplicate emails and usernames in the CSV itself
		emails = [u['email'].lower() for u in users_data]
		usernames = [u['username'].lower() for u in users_data]
		
		if len(emails) != len(set(emails)):
			errors.append("Duplicate emails found in CSV file")
			
		if len(usernames) != len(set(usernames)):
			errors.append("Duplicate usernames found in CSV file")
		
		# Validate each user
		for idx, user_data in enumerate(users_data, start=1):
			line_prefix = f"Line {idx}"
			
			# Required fields
			if not user_data.get('email'):
				errors.append(f"{line_prefix}: Email is required")
				continue
				
			if not user_data.get('username'):
				errors.append(f"{line_prefix}: Username is required")
				continue
			
			# Email format validation (basic)
			email = user_data['email'].strip()
			if '@' not in email or '.' not in email:
				errors.append(f"{line_prefix}: Invalid email format: {email}")
				
			# Username validation
			username = user_data['username'].strip()
			if len(username) < 3:
				errors.append(f"{line_prefix}: Username must be at least 3 characters: {username}")
			
			# Visibility validation
			visibility = user_data.get('visibility', '0').strip()
			if visibility not in ['0', '1', '2', '3']:
				errors.append(f"{line_prefix}: Visibility must be 0-3 (0=Public, 1=Organization, 2=Group, 3=Private), got: {visibility}")
			
			# can_submit validation
			can_submit = user_data.get('can_submit', '1').strip()
			if can_submit not in ['0', '1']:
				errors.append(f"{line_prefix}: can_submit must be 0 or 1, got: {can_submit}")
			
			# Check if email already exists in database
			cursor.execute('SELECT id FROM users WHERE LOWER(email) = LOWER(%s)', (email,))
			if cursor.fetchone():
				errors.append(f"{line_prefix}: Email already exists: {email}")
			
			# Check if username already exists in database
			cursor.execute('SELECT id FROM users WHERE LOWER(username) = LOWER(%s)', (username,))
			if cursor.fetchone():
				errors.append(f"{line_prefix}: Username already exists: {username}")
		
		# If there are any errors, don't import anything
		if errors:
			cursor.close()
			db.close()
			return (success, errors)
		
		# Import phase - all validation passed
		for user_data in users_data:
			# Get values with defaults
			email = user_data['email'].strip()
			username = user_data['username'].strip()
			display_name = user_data.get('display_name', '').strip() or None
			country = user_data.get('country', '').strip() or None
			organization = user_data.get('organization', '').strip() or None
			group = user_data.get('group', '').strip() or None
			visibility = int(user_data.get('visibility', '0').strip())
			can_submit = user_data.get('can_submit', '1').strip() == '1'
			
			# Generate salt and token
			salt = hashlib.sha512(os.urandom(64)).hexdigest()
			token = uuid.uuid4().hex
			
			# Hash the email with the salt
			# Email is stored hashed for privacy, password is set to same hash (user must reset)
			hashed_email = hashlib.sha512((email + salt).encode()).hexdigest()
			
			# Insert user (verified=false, they need to reset password)
			# Both email and password fields contain the hashed email
			cursor.execute('''
				INSERT INTO users 
				(email, password, salt, token, verified, username, admin, display_name, country, organization, "group", visibility, can_submit)
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
				RETURNING id
			''', (hashed_email, hashed_email, salt, token, True, username, False, display_name, country, organization, group, visibility, can_submit))
			
			user_id = cursor.fetchone()[0]
			
			success.append({
				'username': username,
				'email': email,
				'id': str(user_id),
				'display_name': display_name,
				'country': country,
				'organization': organization,
				'group': group,
				'visibility': str(visibility)
			})
		
		db.commit()
		
	except Exception as e:
		db.rollback()
		errors.append(f"Database error: {str(e)}")
	
	finally:
		cursor.close()
		db.close()
	
	return (success, errors)

def create_api_key(created_by, description=None):
	"""Create a new API key."""
	import secrets
	api_key = secrets.token_urlsafe(48)  # 64 characters when base64 encoded
	
	(db, cursor) = connect()
	try:
		cursor.execute(
			'INSERT INTO api_keys (key, created_by, description) VALUES (%s, %s, %s) RETURNING id, key, created_at',
			(api_key, created_by, description)
		)
		result = cursor.fetchone()
		db.commit()
		return result
	except Exception as e:
		db.rollback()
		return None
	finally:
		cursor.close()
		db.close()

def get_api_keys():
	"""Get all API keys."""
	(db, cursor) = connect()
	cursor.execute('''
		SELECT api_keys.id, api_keys.key, api_keys.created_by, users.username, 
		       api_keys.created_at, api_keys.last_used, api_keys.description, api_keys.active
		FROM api_keys 
		INNER JOIN users ON api_keys.created_by = users.id
		ORDER BY api_keys.created_at DESC
	''')
	keys = cursor.fetchall()
	cursor.close()
	db.close()
	return keys

def verify_api_key(key):
	"""Verify an API key and update last_used timestamp."""
	(db, cursor) = connect()
	try:
		cursor.execute(
			'SELECT id, created_by, active FROM api_keys WHERE key = %s',
			(key,)
		)
		result = cursor.fetchone()
		
		if result and result[2]:  # Check if key exists and is active
			# Update last_used timestamp
			cursor.execute(
				'UPDATE api_keys SET last_used = NOW() WHERE id = %s',
				(result[0],)
			)
			db.commit()
			return True
		
		return False
	finally:
		cursor.close()
		db.close()

def delete_api_key(key_id):
	"""Delete an API key."""
	(db, cursor) = connect()
	try:
		cursor.execute('DELETE FROM api_keys WHERE id = %s', (key_id,))
		db.commit()
		return True
	except Exception as e:
		db.rollback()
		return False
	finally:
		cursor.close()
		db.close()

def toggle_api_key(key_id):
	"""Toggle the active status of an API key."""
	(db, cursor) = connect()
	try:
		cursor.execute('UPDATE api_keys SET active = NOT active WHERE id = %s', (key_id,))
		db.commit()
		return True
	except Exception as e:
		db.rollback()
		return False
	finally:
		cursor.close()
		db.close()

def get_user_id_by_username(username):
	"""Get user ID by username."""
	(db, cursor) = connect()
	cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
	result = cursor.fetchone()
	cursor.close()
	db.close()
	return result[0] if result else None

def update_api_key_description(key_id, description):
	"""Update the description of an API key."""
	(db, cursor) = connect()
	try:
		cursor.execute('UPDATE api_keys SET description = %s WHERE id = %s', (description, key_id))
		db.commit()
		return True
	except Exception as e:
		db.rollback()
		return False
	finally:
		cursor.close()
		db.close()

# User API Key functions

def generate_user_api_key(user_id, api_key, expiry_date):
	"""Generate or update a user's API key with expiry date."""
	(db, cursor) = connect()
	try:
		cursor.execute(
			'UPDATE users SET user_api_key = %s, user_api_key_expiry = %s WHERE id = %s',
			(api_key, expiry_date, user_id)
		)
		db.commit()
		return True
	except Exception as e:
		db.rollback()
		return False
	finally:
		cursor.close()
		db.close()

def get_user_api_key(user_id):
	"""Get user's API key and expiry date."""
	(db, cursor) = connect()
	try:
		cursor.execute(
			'SELECT user_api_key, user_api_key_expiry FROM users WHERE id = %s',
			(user_id,)
		)
		result = cursor.fetchone()
		return result
	finally:
		cursor.close()
		db.close()

def verify_user_api_key(api_key):
	"""Verify a user API key and return user info if valid and not expired."""
	(db, cursor) = connect()
	try:
		cursor.execute(
			'SELECT id, username, verified, can_submit FROM users WHERE user_api_key = %s AND user_api_key_expiry > NOW()',
			(api_key,)
		)
		result = cursor.fetchone()
		return result
	finally:
		cursor.close()
		db.close()

def revoke_user_api_key(user_id):
	"""Revoke (delete) a user's API key."""
	(db, cursor) = connect()
	try:
		cursor.execute(
			'UPDATE users SET user_api_key = NULL, user_api_key_expiry = NULL WHERE id = %s',
			(user_id,)
		)
		db.commit()
		return True
	except Exception as e:
		db.rollback()
		return False
	finally:
		cursor.close()
		db.close()


def get_user_setting(user_id, setting_key):
	"""Get a specific setting from user's settings JSONB column."""
	(db, cursor) = connect()
	try:
		cursor.execute(
			'SELECT settings->>%s FROM users WHERE id = %s',
			(setting_key, user_id)
		)
		result = cursor.fetchone()
		return result[0] if result else None
	except Exception as e:
		return None
	finally:
		cursor.close()
		db.close()


def set_user_setting(user_id, setting_key, setting_value):
	"""Set a specific setting in user's settings JSONB column."""
	(db, cursor) = connect()
	try:
		cursor.execute(
			'UPDATE users SET settings = jsonb_set(settings, %s, %s) WHERE id = %s',
			('{' + setting_key + '}', json.dumps(setting_value), user_id)
		)
		db.commit()
		return True
	except Exception as e:
		db.rollback()
		return False
	finally:
		cursor.close()
		db.close()