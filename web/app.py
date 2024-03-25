from flask import Flask, render_template, request, redirect, session, url_for
from flask_mail import Mail, Message
from markdown import markdown
from datetime import datetime
from hashlib import sha512
from dotenv import load_dotenv
import secrets, os, toml, random, string, re, json
import db as db
from util import score_results, user_total_score

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

def check_admin() -> bool:
	if 'logged_in' not in session:
		return redirect(url_for('login'))

	userid = session['user_id'] if 'user_id' in session else -1
	is_admin = db.is_admin_by_id(userid)
	is_admin = is_admin[0] if is_admin else False

	return is_admin

def send_email(subject, recipient, body, html):
	msg = Message(subject, recipients=recipient)
	msg.body = body
	msg.html = html
	mail.send(msg)

if __name__ == '__main__':
	app.run(debug=False)

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

		if token == "_banned_":
			token = None

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
	if token == "_banned_":
		token = None

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

		is_banned = db.is_banned(user[0])

		if user is None or is_banned:
			return redirect('/reset')

		user_id, hashed_password, salt, username, verified, email_hashed, token, display_name, country, organization, group, visibility = user

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

		is_banned = db.is_banned(user[0])

		if user is None or is_banned: #if user is banned prohibit the password change
			return redirect('/newpassword')

		user_id, hashed_password, salt, username, verified, email_hashed, token, display_name, country, organization, group, visibility = user

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

		user_id, hashed_password, salt, username, verified, email, token, display_name, country, organization, group, visibility = user

		if sha512((password + salt).encode()).hexdigest() == hashed_password:
			if verified == 0:
				if token == "_banned_":
					return render_template('banned.html', sessions=session)	
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
	if os.path.exists("config/.submit.disable"):
		with open("config/.submit.disable", "r") as f:
			if f.read() == "true":
				return render_template('disabled.html'), 403

	if 'logged_in' not in session:
			return redirect(url_for('login'))
	
	if request.method == 'POST':

		is_banned = db.is_user_banned(session['user_id'])
		if is_banned: #logout user
			return redirect('/logout')
		
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

		is_c_solution = task_data['task'].get('c_solution', False)

		task_description = task_data['task']['description']
		task_description = markdown(task_description)
		#cut the first line of the description
		task_description = task_description.split('\n', 1)[1]

		language = "riscv"

		if is_c_solution:
			language = "c"

		return render_template('submit.html', task_name=task_name, sessions=session, submission_code=submission_code, template_code=template_code, language=language, task_description=task_description)
	
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
	if 'c_solution' in task_data['task']:
		if task_data['task']['c_solution']:
			task_arguments = task_data['arguments']['run'] + " submission"

	makefile = task_data.get('make', None)
	makefile = None if makefile is None else makefile.get('Makefile', None)
	files = task_data.get('files', None)


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

	userid = session['user_id'] if 'user_id' in session else -1
	is_admin = db.is_admin_by_id(userid)
	is_admin = is_admin[0] if is_admin else False

	issue_url = None

	if result == 99:
		#parse GitlabIssue url from result file
		issue_url = re.findall("https:\/\/gitlab\.fel\.cvut\.cz\/.+", result_file, flags = re.MULTILINE)
		issue_url = issue_url[0] if issue_url else None

	return render_template('task.html', task=task_info, sessions=session, result=result, result_file=result_data,
						scores=scores, time=time, submission_found=submission_found, score=score, task_name=task_name,
						latest_score=latest_score, is_admin=is_admin, issue_url=issue_url, makefile=makefile, files=files)

@app.route('/view/<int:task_id>/<int:user_id>/<int:is_latest>')
def view_latest_for_user(task_id, user_id, is_latest):
	#check if the current user is admin or the userid is the same as the session user id
	curr_is_admin = check_admin()

	if session['user_id'] != user_id and not curr_is_admin:
		#throw 403
		return render_template('403.html'), 403
	
	code = db.get_user_code(task_id, user_id, is_latest)
	code = code[0] if code else ""

	best_or_latest = "Latest" if is_latest else "Best"

	task_name = db.get_task_name(task_id)
	task_name = task_name[0] if task_name else ""

	submission = db.get_last_user_submission(task_id, user_id)
	if submission:
		result, result_file, score, time = submission

	if is_latest == 2 and curr_is_admin: #allow this feature only in admin view
		code = result_file
		best_or_latest = "Evaluation log"

	return render_template('view.html', submission_code=code, task_id=task_id, user_id=user_id, is_latest=is_latest, sessions=session, best_or_latest=best_or_latest, task_name=task_name)

@app.route('/about')
def about():
	#read description.md from templates/
	description = None
	if os.path.exists("templates/description.md"):
		with open("templates/description.md") as f:
			description = f.read()
		description = markdown(description)

	return render_template('about.html', sessions=session, description=description)

@app.route('/admin/ban/<int:user_id>/')
def ban(user_id):
	
	is_admin = check_admin()

	if not is_admin:
		return render_template('403.html'), 403

	db.ban_user(user_id)

	return redirect('/admin')

@app.route('/admin/unban/<int:user_id>/')
def unban(user_id):
	
	is_admin = check_admin()

	if not is_admin:
		return render_template('403.html'), 403

	db.unban_user(user_id)

	return redirect('/admin')

@app.route('/admin/')
def admin():
	userid = session['user_id'] if 'user_id' in session else -1
	
	is_admin = check_admin()

	if not is_admin:
		return render_template('403.html'), 403

	users = db.get_users()
	#remove the current user from the list

	all_users = [user for user in users]

	users = [user for user in users if user[0] != userid]

	active_tasks = db.get_active_tasks()

	results = {}

	for task in active_tasks:
		task_id, task_name = task

		results[task_name] = db.get_best_only_scores(task_id)

	#for each task, mark the first 5 scores from 5 to 1 points, if some have same score, mark them with the same number
		
	results = score_results(results)

	#order users by id

	users = sorted(users, key=lambda x: x[0])

	#check if submissions are disabled
	submit_disabled = False
	if os.path.exists("config/.submit.disable"):
		with open("config/.submit.disable", "r") as f:
			submit_disabled = f.read() == "true"

	tasks = db.list_tasks_with_filepath()
		
	return render_template('admin.html', sessions=session, users=users, submissions=results, submit_disabled=submit_disabled, tasks=tasks, all_users=all_users)

@app.route('/admin/toggle/submit/')
def toggle_submit():
	
	is_admin = check_admin()

	if not is_admin:
		return render_template('403.html'), 403

	#if the file is empty, write "true" in in, else clear the file content

	disabled = False
	if os.path.exists("config/.submit.disable"):
		with open("config/.submit.disable", "r") as f:
			if f.read() == "true":
				disabled = True

	if os.path.exists("config/.submit.disable"):
			with open("config/.submit.disable", "w") as f:
				if disabled:
					f.write("false")
				else:
					f.write("true")

	return redirect('/admin')

@app.route('/admin/reorder/<string:order>/')
def reorder(order):
	
	is_admin = check_admin()

	if not is_admin:
		return render_template('403.html'), 403

	order_list = order.split(';')

	db.reorder_tasks(order_list)

	return redirect('/admin')

@app.route('/admin/rename/<int:id>/<string:name>')
def rename(id, name):
	
	is_admin = check_admin()

	if not is_admin:
		return render_template('403.html'), 403

	db.rename_task(id, name)

	return redirect('/admin')

@app.route('/admin/repath/<int:id>/<string:name>')
def repath(id, name):
	
	is_admin = check_admin()

	if not is_admin:
		return render_template('403.html'), 403

	name = "tasks/" + name

	db.task_change_path(id, name)

	return redirect('/admin')

@app.route('/admin/available/<int:id>/<int:available>')
def change_available(id, available):
	
	is_admin = check_admin()

	if not is_admin:
		return render_template('403.html'), 403

	available = False if available == 0 else True

	db.set_task_availability(id, available)

	return redirect('/admin')

@app.route('/admin/new/<string:path>/')
def new_task(path):
	
	is_admin = check_admin()

	if not is_admin:
		return render_template('403.html'), 403

	path = "tasks/" + path

	db.create_new_task(path)

	return redirect('/admin')

@app.route('/admin/resetorg/<int:user_id>/')
def reset_org(user_id):
	is_admin = check_admin()

	if not is_admin:
		return render_template('403.html'), 403

	db.reset_org(user_id)

	return redirect('/admin')

@app.route('/admin/setgroup/<int:user_id>/<string:group>/')
def set_group(user_id, group):
	is_admin = check_admin()

	if not is_admin:
		return render_template('403.html'), 403

	db.set_group(user_id, group)

	return redirect('/admin')

@app.route('/scoreboard/')
def scoreboard():
	active_tasks = db.get_active_tasks()

	results = {}

	for task in active_tasks:
		task_id, task_name = task

		results[task_name] = db.get_best_only_scores_for_public(task_id)
	
	# for testing: results["Simple addition"] = [('test0', 10, 1), ('test1', 10, 2), ('test2', 11, 3), ('test3', 12, 4), ('test4', 12, 5), ('test5', 12, 6), ('test6', 12, 7), ('test7', 12, 8), ('test8', 12, 9), ('test9', 20, 10)]

	results = score_results(results)

	#get user ids from results

	#TODO: rewrite this later
	#('test0', 10, 1) the 3rd argument is the user id
	user_ids = {}
	for task in results:
		for result in results[task]:
			if result[0] not in user_ids:
				user_ids[result[0]] = 0
			user_ids[result[0]] = result[2]

	total_score = user_total_score(results)

	user_dict = None
	if 'user_id' in session:
		user_id = session['user_id']
		user = db.get_user_by_id(user_id)

		user_dict = {
			'id': user[0],
			'username': user[3],
			'display_name': user[7],
			'country': user[8],
			'organization': user[9],
			'group': user[10],
			'visibility': user[11]
		}

	return render_template('scoreboard.html', sessions=session, submissions=results, total_score=total_score, user_ids=user_ids, user=user_dict, grouporg=None)

@app.route('/scoreboard/grouporg/<int:type>/<string:grouporg>/')
def scoreboard_group(type, grouporg):
	active_tasks = db.get_active_tasks()

	is_admin = check_admin()

	results = {}

	user_id = session['user_id'] if 'user_id' in session else -1

	user = db.get_user_by_id(user_id)
	user_group = user[10] if user else None
	user_org = user[9] if user else None

	results = {}
	group_text = None

	if type == 0: #group
		if user_group != grouporg or not is_admin:
			return render_template('403.html'), 403
		
		group_text = "study group " + grouporg
		for task in active_tasks:
			task_id, task_name = task
			results[task_name] = db.get_best_only_scores_for_group(task_id, grouporg)

	else: #organization
		if user_org != grouporg or not is_admin:
			return render_template('403.html'), 403
		
		group_text = grouporg
		
		for task in active_tasks:
			task_id, task_name = task
			results[task_name] = db.get_best_only_scores_for_org(task_id, grouporg)

	results = score_results(results)

	user_ids = {}
	for task in results:
		for result in results[task]:
			if result[0] not in user_ids:
				user_ids[result[0]] = 0
			user_ids[result[0]] = result[2]

	total_score = user_total_score(results)

	return render_template('scoreboard.html', sessions=session, submissions=results, total_score=total_score, user_ids=user_ids, user=None, grouporg=group_text)

@app.route('/profile/')
def profile():
	userid = session['user_id'] if 'user_id' in session else -1

	if userid == -1:
		return redirect('/login')

	user = db.get_user_by_id(userid)

	#id, password, salt, username, verified, email, token, display_name, country, organization, group, visibility

	user_dict = {
		'id': user[0],
		'username': user[3],
		'display_name': user[7],
		'country': user[8],
		'organization': user[9],
		'group': user[10],
		'visibility': user[11]
	}

	return render_template('profile.html', sessions=session, user=user_dict)

@app.route('/profile/org/<string:country>/<string:org>')
def change_org(country, org):
	userid = session['user_id'] if 'user_id' in session else -1

	if userid == -1:
		return redirect('/login')

	organizations = None

	with app.open_resource('static/organizations.json') as f:
		organizations = json.load(f)

	if not any(o['name'] == org and o['country'] == country for o in organizations):
		return render_template('400.html'), 400

	db.set_org(userid, country, org)

	return redirect('/profile')
@app.route('/profile/displayname/<string:displayname>')
def change_displayname(displayname):
	userid = session['user_id'] if 'user_id' in session else -1

	if userid == -1:
		return redirect('/login')
	
	displayname = displayname[:32]
	
	db.change_displayname(userid, displayname)

	return redirect('/profile')

@app.route('/profile/privacy/<int:visibility>')
def change_privacy(visibility):
	userid = session['user_id'] if 'user_id' in session else -1

	if userid == -1:
		return redirect('/login')
	
	#check if visibility is in range 0-3

	if visibility < 0 or visibility > 3:
		return render_template('400.html'), 400

	db.change_privacy(userid, visibility)

	return redirect('/profile')

@app.errorhandler(400)
def page_bad_request(e):
	return render_template('400.html'), 400

@app.errorhandler(403)
def page_forbidden(e):
	return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404