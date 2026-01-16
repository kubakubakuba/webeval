"""Task-related routes: submit, view task details, view submissions."""

from flask import Blueprint, render_template, request, redirect, session, Response
from markdown import markdown
from datetime import datetime
from auth import login_required, check_banned
import db
import os
import toml
import re

tasks_bp = Blueprint('tasks', __name__)

TASKS_DIR = None
TEMPLATES_DIR = None
check_submission_deadlines = None
check_admin = None

def init_tasks(tasks_dir, templates_dir, deadlines_func, admin_func):
	"""Initialize tasks module with configuration."""
	global TASKS_DIR, TEMPLATES_DIR, check_submission_deadlines, check_admin
	TASKS_DIR = tasks_dir
	TEMPLATES_DIR = templates_dir
	check_submission_deadlines = deadlines_func
	check_admin = admin_func


@tasks_bp.route('/submit/<int:task_id>', methods=['GET', 'POST'])
@login_required
@check_banned
def submit(task_id):
	"""Submit code for a task."""
	# Check if user has submit permission
	user_id = session['user_id']
	if not db.can_user_submit(user_id):
		return render_template('403.html'), 403
	
	if os.path.exists("config/.submit.disable"):
		with open("config/.submit.disable", "r") as f:
			if f.read() == "true":
				return render_template('disabled.html'), 403
	
	task = db.get_task(task_id)

	if task:
		task_name = task[0]
	else:
		return render_template('404.html'), 404
	
	# Read task file
	task_path = db.get_task_path(task_id)
	if task_path:
		task_path = os.path.join(TASKS_DIR, os.path.basename(task_path[0]))

	task_data = None
	if os.path.exists(task_path):
		with open(task_path) as f:
			task_data = toml.load(f)

	if request.method == 'POST':
		deadlines_check = check_submission_deadlines(task_data, task_name)
		
		if deadlines_check:
			return deadlines_check
		
		user_id = session['user_id']
		code = request.form['code'].replace('\r\n', '\n')

		time_uploaded = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

		db.submit(user_id, task_id, code)

		return redirect('/task/' + str(task_id))
	else:
		# If there is a submission for this task by the logged in user, read the submission file
		# Get user latest submission code
		submission_code = db.get_last_user_code(task_id, session['user_id'])
		submission_code = "" if submission_code is None else submission_code[0]

		template_path = task_data['task'].get('template', None)

		deadlines_check = check_submission_deadlines(task_data, task_name)
		
		if deadlines_check:
			return deadlines_check

		template_code = ""

		if template_path:
			# Support both absolute and relative paths
			if not os.path.isabs(template_path):
				template_path = os.path.join(TEMPLATES_DIR, os.path.basename(template_path))
			if os.path.exists(template_path):
				with open(template_path) as f:
					template_code = f.read()

		is_c_solution = task_data['task'].get('c_solution', False)

		task_description = task_data['task'].get('description', None)
		task_description = markdown(task_description)
		# Cut the first line of the description
		task_description = task_description.split('\n', 1)[1]

		language = "riscv"

		if is_c_solution:
			language = "c"

		# Get user's editor theme preference
		user_theme = db.get_user_setting(session['user_id'], 'editor_theme')

		return render_template('submit.html', task_name=task_name, task_id=task_id, sessions=session, submission_code=submission_code, template_code=template_code, language=language, task_description=task_description, user_theme=user_theme)


@tasks_bp.route('/task/<int:task_id>')
def task(task_id):
	"""Display task details and submissions."""
	submission_found = False
	result = None
	score = None
	result_file = None
	time = None
	result_data = None
	name = None

	task = db.get_task_path(task_id)

	if task:
		task_path = os.path.join(TASKS_DIR, os.path.basename(task[0]))
	else:
		return render_template('404.html'), 404
	
	# Check if toml file exists at the location
	if not os.path.exists(task_path):
		return render_template('404.html'), 404
	
	# Read toml file and get the task data
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

	# Parse task description as markdown
	task_description = markdown(task_description, extensions=['codehilite'])
	task_scoring = task_data['score']['description']

	task_submit_start_time = task_data['task'].get('submit_start', None)
	task_submit_end_time = task_data['task'].get('submit_end', None)

	deadlines = None

	if task_submit_start_time or task_submit_end_time:
		from datetime import timezone
		deadlines = {}
		if task_submit_start_time:
			utc_time = datetime.strptime(task_submit_start_time, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
			deadlines["start"] = utc_time.astimezone()
		if task_submit_end_time:
			utc_time = datetime.strptime(task_submit_end_time, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
			deadlines["end"] = utc_time.astimezone()

	inputs = task_data.get('inputs', None)

	latest_score = None

	user = None

	if 'user_id' in session:
		user_id = session['user_id']
		user = db.get_user_by_id(user_id)
		submission = db.get_last_user_submission(task_id, user_id)
		if submission:
			submission_found = True
			result, result_file, score, time = submission
			name = db.get_username(user_id)
			name = None if name is None else name[0]

			latest_score = (user_id, score, name, 0)

		result_data = result_file

	task_info = {
		'name': task_name,
		'description': task_description,
		'arguments': task_arguments,
		'inputs': inputs, 
		'id': task_id,
		'scoring': task_scoring,
		'deadlines': deadlines
	}

	# Check admin status early since we need it for score queries
	userid = session['user_id'] if 'user_id' in session else None
	is_admin = db.is_admin_by_id(userid) if userid is not None else False
	is_admin = is_admin[0] if is_admin else False

	# Get the best scores of all users for a specific task
	organization = user[9] if user is not None else "___none__"
	group = user[10] if user is not None else "___none__"
	curr_user = user[0] if user is not None else None

	best_scores = db.get_best_scores_for_verified_grouporg(task_id, group, organization, curr_user, is_admin)
	# Add flag 1 (best) to the third argument of the tuple
	best_scores = [(score[3], score[1], score[0], 1) for score in best_scores]

	# Check if latest score is the same as best score (score value only)
	# If latest and best have the same score value, only show best (green)
	# If they differ, show both (best in green, latest in yellow)
	# Also filter out latest_score if the score is None (not yet evaluated)
	if latest_score is not None and latest_score[1] is not None:
		best_score_values = {(score[0], score[1]) for score in best_scores}  # (userid, score) tuples
		latest_tuple = (latest_score[0], latest_score[1])
		if latest_tuple in best_score_values:
			latest_score = None

	scores = best_scores + ([latest_score] if latest_score and latest_score[1] is not None else [])

	# Filter out any scores with None values before sorting
	scores = [s for s in scores if s[1] is not None]
	scores.sort(key=lambda x: x[1])

	latest_score = None if latest_score is None else latest_score[1]

	time = None if time is None else time.strftime('%d.%m. %Y %H:%M:%S')

	issue_url = None

	if result == 99:
		# Parse GitlabIssue url from result file
		issue_url = re.findall("https:\/\/gitlab\.fel\.cvut\.cz\/.+", result_file, flags=re.MULTILINE)
		issue_url = issue_url[0] if issue_url else None

	displaynames = db.get_user_displaynames()
	displaynames = {user[0]: user[1] for user in displaynames}
	
	can_submit = db.can_user_submit(userid) if userid is not None else False
	
	# Check if submissions are within the deadline window
	if can_submit and deadlines:
		from datetime import timezone
		current_time = datetime.now(timezone.utc)
		if deadlines.get("start") and current_time < deadlines["start"].astimezone(timezone.utc):
			can_submit = False
		if deadlines.get("end") and current_time > deadlines["end"].astimezone(timezone.utc):
			can_submit = False

	# Get user's editor theme preference
	user_theme = db.get_user_setting(userid, 'editor_theme') if userid else 'default'
	user_theme = user_theme or 'default'

	return render_template('task.html', task=task_info, sessions=session, result=result, result_file=result_data,
scores=scores, time=time, submission_found=submission_found, score=score, task_name=task_name,
latest_score=latest_score, is_admin=is_admin, issue_url=issue_url, makefile=makefile, files=files, displaynames=displaynames, can_submit=can_submit, user_theme=user_theme)


@tasks_bp.route('/download/<int:task_id>/<user_id>/<int:is_best>')
@login_required
def download_submission(task_id, user_id, is_best):
	"""Download submission file for a specific user (best or latest)."""
	# Check if the current user is admin or the userid is the same as the session user id
	curr_is_admin = check_admin()

	if str(session['user_id']) != str(user_id) and not curr_is_admin:
		return render_template('403.html'), 403
	
	# Get the source code
	code = db.get_user_code(task_id, user_id, 0 if is_best else 1)
	code = code[0] if code else ""

	# Get username
	username = db.get_username(user_id)
	username = username[0] if username else "user"

	# Determine filename suffix
	suffix = "best" if is_best else "latest"
	
	response = Response(code, mimetype='text/plain')
	response.headers['Content-Disposition'] = f'attachment; filename=task{task_id}_{username}_{suffix}.txt'
	return response


@tasks_bp.route('/view/<int:task_id>/<user_id>/<int:is_latest>')
@login_required
def view_latest_for_user(task_id, user_id, is_latest):
	"""View submission for a specific user (latest or best)."""
	# Check if the current user is admin or the userid is the same as the session user id
	curr_is_admin = check_admin()

	if str(session['user_id']) != str(user_id) and not curr_is_admin:
		return render_template('403.html'), 403
	
	code = db.get_user_code(task_id, user_id, is_latest)
	code = code[0] if code else ""

	best_or_latest = "Latest" if is_latest else "Best"

	task_name = db.get_task_name(task_id)
	task_name = task_name[0] if task_name else ""

	submission = db.get_last_user_submission(task_id, user_id)
	if submission:
		result, result_file, score, time = submission

	if is_latest == 2 and curr_is_admin:  # Allow this feature only in admin view
		code = result_file
		best_or_latest = "Evaluation log"

	# Get user's editor theme preference
	user_theme = db.get_user_setting(session.get('user_id'), 'editor_theme') if 'user_id' in session else None

	return render_template('view.html', submission_code=code, task_id=task_id, user_id=user_id, is_latest=is_latest, sessions=session, best_or_latest=best_or_latest, task_name=task_name, user_theme=user_theme)
