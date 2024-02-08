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

def get_latest_submissions(count):
	"""Fetch the earliest <count> submissions from the database."""
	(db, cursor) = connect()
	cursor.execute('SELECT id, taskid, file, evaluated, userid FROM submissions WHERE evaluated = false ORDER BY id ASC LIMIT %s', (count,))
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

def update_submission(submission_id):
	(db, cursor) = connect()
	cursor.execute("UPDATE submissions SET evaluated = true WHERE id = %s", (submission_id, ))
	db.commit()
	cursor.close()
	db.close()

def update_result(userid, taskid, score_last, result, result_file):
	(db, cursor) = connect()
	#update or insert
	cursor.execute('''
		INSERT INTO results (userid, taskid, score_last, result, result_file)
		VALUES (%s, %s, %s, %s, %s)
		ON CONFLICT (userid, taskid) DO UPDATE SET
		score_last = %s, result = %s, result_file = %s
	''', (userid, taskid, score_last, result, result_file, score_last, result, result_file))
	db.commit()
	cursor.close()
	db.close()
