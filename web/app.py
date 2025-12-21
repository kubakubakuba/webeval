from flask import Flask, render_template, session
from flask_mail import Mail
from markdown import markdown
from dotenv import load_dotenv
import os
import db
from util import check_submission_deadlines
import admin as admin_module
import login as login_module
import tasks as tasks_module
import scoreboard as scoreboard_module
import profile as profile_module
import api as api_module

# Load .env from /app/.env in Docker or ../.env locally
env_path = "/app/.env" if os.path.exists("/app/.env") else "../.env"
load_dotenv(env_path)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

URL = os.getenv('BASE_URL', 'https://eval.comparch.edu.cvut.cz')

USER_FILTER = ["reference"]

TEMPLATES_DIR = os.getenv('TEMPLATES_DIR', 'S_templates')
TASKS_DIR = os.getenv('TASKS_DIR', 'tasks')

mail = Mail(app)

def check_admin() -> bool:
	if 'logged_in' not in session:
		return False

	userid = session.get('user_id')
	if userid is None:
		return False
	is_admin = db.is_admin_by_id(userid)
	is_admin = is_admin[0] if is_admin else False

	return is_admin

admin_module.init_admin(TASKS_DIR)
app.register_blueprint(admin_module.admin_bp)

login_module.init_login(URL, mail)
app.register_blueprint(login_module.login_bp)

tasks_module.init_tasks(TASKS_DIR, TEMPLATES_DIR, check_submission_deadlines, check_admin)
app.register_blueprint(tasks_module.tasks_bp)

scoreboard_module.init_scoreboard(USER_FILTER, check_admin)
app.register_blueprint(scoreboard_module.scoreboard_bp)

app.register_blueprint(profile_module.profile_bp)

api_module.init_api(TASKS_DIR, URL)
app.register_blueprint(api_module.api_bp)

@app.route('/')
def index():
	task = db.list_tasks()

	tasks = {}
	if task:
		for(i, t) in enumerate(task):
			task_id, task_name = t
			tasks[i] = (task_id, task_name)

	return render_template('index.html', sessions=session, tasks=tasks.values())

@app.route('/about')
def about():
	#read description.md from templates/
	description = None
	if os.path.exists("templates/description.md"):
		with open("templates/description.md") as f:
			description = f.read()
		description = markdown(description)

	return render_template('about.html', sessions=session, description=description)

@app.errorhandler(400)
def page_bad_request(e):
	return render_template('400.html'), 400

@app.errorhandler(403)
def page_forbidden(e):
	return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

if __name__ == '__main__':
	app.run(debug=False)
