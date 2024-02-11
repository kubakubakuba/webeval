from flask import Flask, render_template, request, redirect, session, url_for
from flask_mail import Mail, Message
from markdown import markdown
from datetime import datetime
from hashlib import sha512
from dotenv import load_dotenv
import secrets
import os
import toml
import db as db
import random
import string

load_dotenv("../.env")

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

URL = "https://eval.comparch.edu.cvut.cz"

mail = Mail(app)

def send_email(subject, recipient, body, html):
	msg = Message(subject, recipients=recipient)
	msg.body = body
	msg.html = html
	mail.send(msg)

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
		hashed_email = sha512((email + salt).encode()).hexdigest()

		token = ''.join([''.join(random.choices(string.ascii_uppercase + string.digits, k=2)) for _ in range(4)])

		subject = "Verify your email address"
		recipients = [email]
		body = f"Click the link to verify your email address: {URL}/verify/{token}/{username}/{hashed_email}"
		token_parts = [token[i:i+2] for i in range(0, len(token), 2)]
		html = f"""
		<div style='max-width: 600px; margin: 30px auto; text-align: center;'>
			<h2 style='font-size: 20px; margin-bottom: 20px;'>Thanks for registering!</h2>
		</div>

		<div style='max-width: 600px; margin: 0 auto;'>
			<div style='border: 1px solid #ddd; padding: 20px; text-align: center;'>
				<h1 style='font-size: 24px; margin-bottom: 20px;'>Email Verification</h1>
				<table style='margin: 0 auto;'>
					<tr>
						{"".join([f"<td style='border: 1px solid #ddd; padding: 20px; font-size: 24px;'>{part}</td>" for part in token_parts])}
					</tr>
				</table>
				<p style='font-size: 16px; margin-bottom: 30px;'>Click the card below to verify your email address:</p>
				<a href='{URL}/verify/{token}/{username}/{hashed_email}' style='text-decoration: none; color: inherit;'>
					<div style='border: 1px solid #ddd; padding: 20px; cursor: pointer;'>
						<p style='font-size: 16px; margin: 0;'>Verify Email</p>
					</div>
				</a>

				<p style='text-align: center; font-size: 16px; margin-top: 30px;'>Or enter the code manually on the page: <a href='{URL}/verify'>{URL}/verify</a></p>
			</div>
		</div>
		"""

		send_email(subject, recipients, body, html)
		register_successful = True

		register_successful = db.register(username, hashed_password, hashed_email, salt, token)
		if register_successful:
			return redirect('/verify')
		else:
			return redirect('/register#username_taken')
	else:
		return render_template('register.html', sessions=session)
	
@app.route('/verify', methods=['GET', 'POST'])
def verify_manual():
	if request.method == 'POST':
		token =  request.form.get('verification0')
		token += request.form.get('verification1')
		token += request.form.get('verification2')
		token += request.form.get('verification3')

		username = request.form.get('username')
		
		success = db.verify_manual(token, username)
		if success:
			reset_token(username)
			return redirect('/login')
		else:
			return redirect('/verify')
	return render_template('verify.html')

@app.route('/verify/<token>/<user>/<email>', methods=['GET'])
def verify_auto(token, user, email):
	success = db.verify_auto(token, user, email)
	if success:
		reset_token(user)
		return redirect('/login')
	else:
		return redirect('/verify')

def reset_token(username):
	db.reset_token(username)

@app.route('/reset', methods=['GET', 'POST'])
def reset():
	if request.method == 'POST':
		username = request.form['username']
		email = request.form['email']

		user = db.get_user(username)

		if user is None:
			return redirect('/reset')

		user_id, hashed_password, salt, username, verified, email_hashed = user

		if sha512((email + salt).encode()).hexdigest() != email_hashed:
			return redirect('/reset')

		token = ''.join([''.join(random.choices(string.ascii_uppercase + string.digits, k=2)) for _ in range(4)])

		subject = "Reset your password"
		recipients = [email]
		body = f"Click the link to reset your password: {URL}/newpassword"
		token_parts = [token[i:i+2] for i in range(0, len(token), 2)]
		html = f"""
		<div style='max-width: 600px; margin: 30px auto; text-align: center;'>
			<h2 style='font-size: 20px; margin-bottom: 20px;'>You have requested a password reset for you account.</h2>
		</div>

		<div style='max-width: 600px; margin: 0 auto;'>
			<div style='border: 1px solid #ddd; padding: 20px; text-align: center;'>
				<h1 style='font-size: 24px; margin-bottom: 20px;'>Reset Password</h1>
				<table style='margin: 0 auto;'>
					<tr>
						{"".join([f"<td style='border: 1px solid #ddd; padding: 20px; font-size: 24px;'>{part}</td>" for part in token_parts])}
					</tr>
				</table>
				<p style='font-size: 16px; margin-bottom: 30px;'>Click the card below to verify your email address:</p>
				<a href='{URL}/newpassword' style='text-decoration: none; color: inherit;'>
					<div style='border: 1px solid #ddd; padding: 20px; cursor: pointer;'>
						<p style='font-size: 16px; margin: 0;'>Reset Password</p>
					</div>
				</a>

				<p style='text-align: center; font-size: 16px; margin-top: 30px;'>Or enter the code manually on the page: <a href='{URL}/newpassword'>{URL}/newpassword</a></p>
			</div>
		</div>
		"""

		send_email(subject, recipients, body, html)

		db.add_verify_code(username, token)

		return redirect('/newpassword')
		
	else:
		return render_template('reset.html', sessions=session)

@app.route('/newpassword', methods=['GET', 'POST'])
def newpassword():
	if request.method == 'POST':
		token =  request.form.get('verification0')
		token += request.form.get('verification1')
		token += request.form.get('verification2')
		token += request.form.get('verification3')

		username = request.form.get('username')
		email = request.form.get('email')
		password = request.form.get('password')

		user = db.get_user(username)

		if user is None:
			return redirect('/newpassword')

		user_id, hashed_password, salt, username, verified, email_hashed = user

		new_hashed_password = sha512((password + salt).encode()).hexdigest()

		if sha512((email + salt).encode()).hexdigest() != email_hashed:
			return redirect('/newpassword')
		
		success = db.set_new_password(username, new_hashed_password, token)

		if success:
			reset_token(username)
			return redirect('/login')
		else:
			return redirect('/newpassword')
		
	return render_template('newpassword.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']

		user = db.get_user(username)

		if user is None:
			return render_template('invalid.html', redirect_url='/login')

		user_id, hashed_password, salt, username, verified, email = user

		if sha512((password + salt).encode()).hexdigest() == hashed_password:
			if verified == 0:
				return redirect('/verify')
			
			session['logged_in'] = True
			session['user_id'] = user_id
			session['username'] = username
			#return render_template('autoredirect.html')
			return redirect('/')
		else:
			return render_template('invalid.html', redirect_url='/login')
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

		time_uploaded = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

		db.submit(user_id, task_id, code)

		return redirect('/task/' + str(task_id))
	else:
		task = db.get_task(task_id)

		if task:
			task_name = task[0]

		else:
			return render_template('404.html'), 404

		#if there is a submission for this task by the logged in user, read the submission file
		#get user latest submission code
		submission_code = db.get_last_user_code(task_id, session['user_id'])
		submission_code = "" if submission_code is None else submission_code[0]
		#if os.path.exists(f"submissions/{session['user_id']}_{task_id}.S"):
		#	with open(f"submissions/{session['user_id']}_{task_id}.S") as f:
		#		submission_code = f.read()

		#read task file
		task_path = db.get_task_path(task_id)
		if task_path:
			task_path = task_path[0]

		task_data = None
		if os.path.exists(task_path):
			with open(task_path) as f:
				task_data = toml.load(f)

		template_path = task_data['task'].get('template', None)	

		template_code = ""

		if template_path:
			if os.path.exists(template_path):
				with open(template_path) as f:
					template_code = f.read()

		return render_template('submit.html', task_name=task_name, sessions=session, submission_code=submission_code, template_code=template_code)
	
@app.route('/task/<int:task_id>')
def task(task_id):
	submission_found = False
	result = None
	score = None
	result_file = None
	time = None
	result_data = None
	name = None

	task = db.get_task_path(task_id)

	if task:
		task_path = task[0]
	else:
		return render_template('404.html'), 404
	
	#check if toml file exists at the location

	if(not os.path.exists(task_path)):
		return render_template('404.html'), 404
	
	#read toml file and get the task data

	with open(task_path) as f:
		task_data = toml.load(f)

	task_name = task_data['task']['name']
	task_description = task_data['task']['description']
	task_arguments = task_data['arguments']['run'] + " --asm submission.S"
	#parse task description as markdown
	task_description = markdown(task_description)
	task_scoring = task_data['score']['description']

	inputs = task_data['inputs']

	latest_score = None

	if 'user_id' in session:
		user_id = session['user_id']
		submission = db.get_last_user_submission(task_id, user_id)
		if submission:
			submission_found = True
			result, result_file, score, time = submission
			name = db.get_username(user_id)
			name = None if name is None else name[0]

			#evaluated, result, score, result_file, time = submission
			latest_score = (user_id, score, name, 0)

		result_data = result_file

	task_info = {
		'name': task_name,
		'description': task_description,
		'arguments': task_arguments,
		'inputs': inputs, 
		'id': task_id,
		'scoring': task_scoring
	}

	# Get the best scores of all users for a specific task
	best_scores = db.get_best_scores(task_id)
	#add flag 1 (best) to the third argument of the tuple
	best_scores = [(score[3], score[1], score[0], 1) for score in best_scores]

	#check if latest score is already in best scores
	duplicate_score = []
	if latest_score is not None:
		duplicate_score = (latest_score[0], latest_score[1], latest_score[2], 1) #reflag to 1 (best)

	if duplicate_score in best_scores:
		latest_score = None

	scores = best_scores + ([latest_score] if latest_score else [])

	scores.sort(key=lambda x: x[1])

	latest_score = None if latest_score is None else latest_score[1]

	time = None if time is None else time.strftime('%d.%m. %Y %H:%M:%S')

	return render_template('task.html', task=task_info, sessions=session, result=result, result_file=result_data, scores=scores, time=time, submission_found=submission_found, score=score, task_name=task_name, latest_score=latest_score)

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404