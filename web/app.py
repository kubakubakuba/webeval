from flask import Flask, render_template, request, redirect, session, url_for
from evaluator import evaluator_thread
from markdown import markdown
from datetime import datetime
from hashlib import sha512
from threading import Thread
import secrets
import os
import toml
import db


app = Flask(__name__)
app.secret_key = 'PsHYn26gGFi#&yfRB%B5SENWseYpat5#nQTv4yQjJC%qt*9Zy6o3ZRu389RmQkgF'

if __name__ == '__main__':
	app.run(debug=True)


@app.route('/')
def index():
	task = db.list_tasks()

	tasks = {}
	if task:
		for(i, t) in enumerate(task):
			task_id, task_name = t
			tasks[i] = (task_id, task_name)

	return render_template('index.html', sessions=session, tasks=tasks.values())

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		email = request.form['email']

		salt = secrets.token_hex(16) #generate random salt for hashing password
		hashed_password = sha512((password + salt).encode()).hexdigest()

		register_successful = db.register(username, hashed_password, email, salt)
		if register_successful:
			return redirect('/login')
		else:
			return redirect('/register#username_taken')
	else:
		return render_template('register.html', sessions=session)
	
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']

		user = db.login(username)

		if user:
			user_id, hashed_password, salt, username = user
			if sha512((password + salt).encode()).hexdigest() == hashed_password:
				session['logged_in'] = True
				session['user_id'] = user_id
				session['username'] = username
				return render_template('autoredirect.html')
			else:
				return 'Invalid username or password!'
		else:
			return 'Invalid username or password!'
	else:
		return render_template('login.html', sessions=session)	
	
@app.route('/logout')
def logout():
	session.clear()
	return redirect('/login')

@app.route('/submit/<int:task_id>', methods=['GET', 'POST'])
def submit(task_id):
	if 'logged_in' not in session:
			return redirect(url_for('login'))
	
	if request.method == 'POST':
		user_id = session['user_id']
		code = request.form['code'].replace('\r\n', '\n')

		directory = os.path.join('submissions', str(user_id))
		if not os.path.exists(directory):
			os.makedirs(directory)

		time_uploaded = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
		filename = time_uploaded + '.S'
		with open(os.path.join(directory, filename), 'w') as file:
			file.write(code)

		full_filepath = "submissions/" + str(user_id) + "/" + filename

		db.submit(user_id, task_id, full_filepath)

		return render_template('autoredirect.html')
	else:
		task = db.get_task(task_id)

		if task:
			task_name = task[0]

		else:
			return 'Task not found or not available to submit!'

		return render_template('submit.html', task_name=task_name, sessions=session)
	
@app.route('/task/<int:task_id>')
def task(task_id):
	submission_found = False
	result = None
	score = None
	result_file = None
	time = None
	result_data = None

	task = db.get_task_path(task_id)

	if task:
		task_path = task[0]
	else:
		return 'Task not found or not available to submit!'
	
	#check if toml file exists at the location

	if(not os.path.exists(task_path)):
		return 'Task not found or not available to submit!'
	
	#read toml file and get the task data

	with open(task_path) as f:
		task_data = toml.load(f)

	task_name = task_data['task']['name']
	task_description = task_data['task']['description']
	task_arguments = task_data['arguments']['run'] + " --asm submission.S"
	#parse task description as markdown
	task_description = markdown(task_description)

	inputs = task_data['inputs']

	if 'user_id' in session:
		user_id = session['user_id']
		submission = db.get_user_submissions(user_id, task_id)

		if submission:
			submission_found = True
			evaluated, result, score, result_file, time = submission

		result_data = ""
		#check if result file exists
		if result_file is not None:
			#result_file = result_file.decode() #if result_file is bytes for some reason
			if os.path.exists(result_file):
				with open(result_file) as f:
					result_data = f.read()
		else:
			result_data = None

	task_info = {
		'name': task_name,
		'description': task_description,
		'arguments': task_arguments,
		'inputs': inputs, 
		'id': task_id
	}

	scores = db.get_latest_scores(task_id)

	return render_template('task.html', task=task_info, sessions=session, result=result, result_file=result_data, score=score, time=time, submission_found=submission_found, scores=scores)