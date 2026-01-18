"""Admin panel routes and functionality."""

from flask import Blueprint, render_template, request, redirect, session
from auth import admin_required
import db, os, re, csv, io

TASKS_DIR = None
TEMPLATES_DIR = None

def init_admin(tasks_dir, templates_dir):
	"""Initialize admin module with configuration."""
	global TASKS_DIR, TEMPLATES_DIR
	TASKS_DIR = tasks_dir
	TEMPLATES_DIR = templates_dir

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/reevaluate/<int:task_id>/<user_id>/<int:is_best>')
@admin_required
def reevaluate(task_id, user_id, is_best):
	"""Re-evaluate a specific task submission for a user."""
	db.reevaluate_task(task_id, user_id, is_best)
	return redirect('/task/' + str(task_id))


@admin_bp.route('/ban/<user_id>/')
@admin_required
def ban(user_id):
	"""Ban a user."""
	db.ban_user(user_id)
	return redirect('/admin/users')


@admin_bp.route('/unban/<user_id>/')
@admin_required
def unban(user_id):
	"""Unban a user."""
	db.unban_user(user_id)
	return redirect('/admin/users')


@admin_bp.route('/')
@admin_required
def admin():
	"""Main admin panel - dashboard with navigation."""
	# Check if submissions are disabled
	submit_disabled = False
	if os.path.exists("config/.submit.disable"):
		with open("config/.submit.disable", "r") as f:
			submit_disabled = f.read() == "true"
		
	return render_template('admin.html', sessions=session, submit_disabled=submit_disabled)


@admin_bp.route('/users')
@admin_required
def admin_users():
	"""User management page."""
	userid = session['user_id']
	
	users = db.get_users()
	all_users = [user for user in users]
	users = [user for user in users if user[0] != userid]

	# Order users by id
	users = sorted(users, key=lambda x: x[0])
	all_users = sorted(all_users, key=lambda x: x[0])
		
	return render_template('admin_users.html', sessions=session, users=users, all_users=all_users)


@admin_bp.route('/tasks')
@admin_required
def admin_tasks():
	"""Task management page."""
	tasks = db.list_tasks_with_filepath()
		
	return render_template('admin_tasks.html', sessions=session, tasks=tasks)


@admin_bp.route('/toggle/submit/')
@admin_required
def toggle_submit():
	"""Toggle submission availability globally."""
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


@admin_bp.route('/reorder/<string:order>/')
@admin_required
def reorder(order):
	"""Reorder tasks."""
	order_list = order.split(';')
	db.reorder_tasks(order_list)
	return redirect('/admin/tasks')


@admin_bp.route('/rename/<int:id>/<string:name>')
@admin_required
def rename(id, name):
	"""Rename a task."""
	db.rename_task(id, name)
	return redirect('/admin/tasks')


@admin_bp.route('/repath/<int:id>/<string:name>')
@admin_required
def repath(id, name):
	"""Change task file path."""
	name = os.path.join(TASKS_DIR, os.path.basename(name))
	db.task_change_path(id, name)
	return redirect('/admin/tasks')


@admin_bp.route('/available/<int:id>/<int:available>')
@admin_required
def change_available(id, available):
	"""Toggle task availability."""
	available = False if available == 0 else True
	db.set_task_availability(id, available)
	return redirect('/admin/tasks')


@admin_bp.route('/new/<string:path>/')
@admin_required
def new_task(path):
	"""Create a new task."""
	path = os.path.join(TASKS_DIR, os.path.basename(path))
	db.create_new_task(path)
	return redirect('/admin/tasks')


@admin_bp.route('/resetorg/<user_id>/')
@admin_required
def reset_org(user_id):
	"""Reset user organization."""
	db.reset_org(user_id)
	return redirect('/admin/users')


@admin_bp.route('/setgroup/<user_id>/<string:group>/')
@admin_required
def set_group(user_id, group):
	"""Set user group."""
	db.set_group(user_id, group)
	return redirect('/admin/users')


@admin_bp.route('/togglesubmit/<user_id>/<int:can_submit>/')
@admin_required
def toggle_can_submit(user_id, can_submit):
	"""Toggle whether a user can submit."""
	can_submit_bool = can_submit == 1
	db.set_can_submit(user_id, can_submit_bool)
	return redirect('/admin/users')


@admin_bp.route('/resetresults/<userid>/')
@admin_required
def reset_results(userid):
	"""Reset all results for a user."""
	db.reset_results_user(userid)
	return redirect('/admin/users')


@admin_bp.route('/apikeys', methods=['GET'])
@admin_required
def admin_api_keys():
	"""Display all API keys."""
	api_keys = db.get_api_keys()
	return render_template('admin_apikeys.html', sessions=session, api_keys=api_keys)


@admin_bp.route('/apikeys/create', methods=['POST'])
@admin_required
def create_api_key():
	"""Generate a new API key."""
	description = request.form.get('description', '').strip()
	# Sanitize description: limit length and remove potentially harmful characters
	if description:
		description = re.sub(r'[<>\"\'&]', '', description)[:255]
	created_by = session['user_id']
	
	result = db.create_api_key(created_by, description if description else None)
	
	if result:
		return redirect('/admin/apikeys')
	else:
		return redirect('/admin/apikeys#error')


@admin_bp.route('/apikeys/delete/<int:key_id>', methods=['POST', 'GET'])
@admin_required
def delete_api_key(key_id):
	"""Delete an API key."""
	db.delete_api_key(key_id)
	return redirect('/admin/apikeys')


@admin_bp.route('/apikeys/toggle/<int:key_id>', methods=['POST', 'GET'])
@admin_required
def toggle_api_key(key_id):
	"""Toggle an API key's active status."""
	db.toggle_api_key(key_id)
	return redirect('/admin/apikeys')


@admin_bp.route('/apikeys/description/<int:key_id>', methods=['POST'])
@admin_required
def update_api_key_description(key_id):
	"""Update an API key's description."""
	description = request.form.get('description', '').strip()
	# Sanitize description
	if description:
		description = re.sub(r'[<>\"\'&]', '', description)[:255]
	db.update_api_key_description(key_id, description if description else None)
	return redirect('/admin/apikeys')


@admin_bp.route('/import', methods=['GET', 'POST'])
@admin_required
def admin_import_users():
	"""Batch import users from CSV file."""
	if request.method == 'GET':
		return render_template('admin_import.html')
	
	# POST - handle file upload
	if 'csvFile' not in request.files:
		return render_template('admin_import.html', errors=['No file uploaded'])
	
	file = request.files['csvFile']
	
	if file.filename == '':
		return render_template('admin_import.html', errors=['No file selected'])
	
	if not file.filename.endswith('.csv'):
		return render_template('admin_import.html', errors=['File must be a CSV file'])
	
	try:
		# Read and parse CSV
		stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
		csv_reader = csv.reader(stream, delimiter=';')
		
		users_data = []
		for row_num, row in enumerate(csv_reader, start=1):
			# Skip empty rows
			if not row or all(cell.strip() == '' for cell in row):
				continue
			
			# Expect 7-8 columns: email;username;display_name;country;organization;group;visibility;can_submit
			# can_submit is optional and defaults to 1 (allow)
			if len(row) < 7:
				return render_template('admin_import.html', 
					errors=[f'Line {row_num}: Invalid format - expected 7-8 columns (semicolon-separated), got {len(row)}'])
			
			users_data.append({
				'email': row[0].strip(),
				'username': row[1].strip(),
				'display_name': row[2].strip(),
				'country': row[3].strip(),
				'organization': row[4].strip(),
				'group': row[5].strip(),
				'visibility': row[6].strip(),
				'can_submit': row[7].strip() if len(row) > 7 else '1'
			})
		
		if not users_data:
			return render_template('admin_import.html', errors=['CSV file is empty'])
		
		# Check if dry run
		dry_run = 'dryRun' in request.form
		
		if dry_run:
			# Validation only
			errors = []
			(db_conn, cursor) = db.connect()
			try:
				for idx, user_data in enumerate(users_data, start=1):
					line_prefix = f"Line {idx}"
					
					if not user_data.get('email') or '@' not in user_data['email']:
						errors.append(f"{line_prefix}: Invalid email: {user_data.get('email', 'empty')}")
					
					if not user_data.get('username') or len(user_data['username']) < 3:
						errors.append(f"{line_prefix}: Invalid username: {user_data.get('username', 'empty')}")
					
					if user_data.get('visibility') not in ['0', '1', '2', '3']:
						errors.append(f"{line_prefix}: Invalid visibility (must be 0-3): {user_data.get('visibility', 'empty')}")
					
					if user_data.get('can_submit', '1') not in ['0', '1']:
						errors.append(f"{line_prefix}: Invalid can_submit (must be 0 or 1): {user_data.get('can_submit', 'empty')}")
					
					# Check existing users
					if user_data.get('email'):
						cursor.execute('SELECT id FROM users WHERE LOWER(email) = LOWER(%s)', (user_data['email'],))
						if cursor.fetchone():
							errors.append(f"{line_prefix}: Email already exists: {user_data['email']}")
					
					if user_data.get('username'):
						cursor.execute('SELECT id FROM users WHERE LOWER(username) = LOWER(%s)', (user_data['username'],))
						if cursor.fetchone():
							errors.append(f"{line_prefix}: Username already exists: {user_data['username']}")
			finally:
				cursor.close()
				db_conn.close()
			
			if errors:
				return render_template('admin_import.html', errors=errors)
			else:
				# Return info message with user data for preview
				return render_template('admin_import.html', 
					info={
						'message': 'DRY RUN: Validation passed - no users were imported', 
						'count': len(users_data),
						'users': users_data
					})
		else:
			# Actual import
			(success, errors) = db.batch_import_users(users_data)
			
			if errors:
				return render_template('admin_import.html', errors=errors)
			else:
				return render_template('admin_import.html', 
					success={'count': len(success), 'users': success})
	
	except Exception as e:
		return render_template('admin_import.html', errors=[f'Error processing file: {str(e)}'])


@admin_bp.route('/editor')
@admin_required
def task_editor():
	"""Task editor page."""
	tasks = db.list_tasks_with_filepath()
	user_theme = db.get_user_setting(session['user_id'], 'editor_theme')
	return render_template('admin_editor.html', sessions=session, tasks=tasks, user_theme=user_theme)


@admin_bp.route('/editor/load/<int:task_id>')
@admin_required
def load_task_file(task_id):
	"""Load task file content."""
	import json
	
	filepath = db.get_task_path_admin(task_id)
	if not filepath:
		return json.dumps({'error': 'Task not found'}), 404
	
	# Construct full path using TASKS_DIR
	filepath = os.path.join(TASKS_DIR, filepath[0])
	
	try:
		with open(filepath, 'r') as f:
			content = f.read()
		return json.dumps({'content': content, 'filepath': filepath})
	except Exception as e:
		return json.dumps({'error': str(e)}), 500


@admin_bp.route('/editor/save/<int:task_id>', methods=['POST'])
@admin_required
def save_task_file(task_id):
	"""Save task file content."""
	import json
	
	filepath = db.get_task_path_admin(task_id)
	if not filepath:
		return json.dumps({'error': 'Task not found'}), 404
	
	# Construct full path using TASKS_DIR
	filepath = os.path.join(TASKS_DIR, filepath[0])
	content = request.form.get('content', '')
	
	try:
		with open(filepath, 'w') as f:
			f.write(content)
		return json.dumps({'success': True, 'message': 'File saved successfully'})
	except Exception as e:
		return json.dumps({'error': str(e)}), 500


@admin_bp.route('/templates')
@admin_required
def templates_editor():
	"""Templates editor page."""
	import glob
	
	# Get all template files
	templates = []
	if os.path.exists(TEMPLATES_DIR):
		for filepath in glob.glob(os.path.join(TEMPLATES_DIR, '*')):
			if os.path.isfile(filepath):
				filename = os.path.basename(filepath)
				templates.append(filename)
	
	templates.sort()
	user_theme = db.get_user_setting(session['user_id'], 'editor_theme')
	return render_template('admin_templates.html', sessions=session, templates=templates, user_theme=user_theme)


@admin_bp.route('/templates/load/<path:filename>')
@admin_required
def load_template_file(filename):
	"""Load template file content."""
	import json
	
	# Sanitize filename to prevent directory traversal
	filename = os.path.basename(filename)
	filepath = os.path.join(TEMPLATES_DIR, filename)
	
	if not os.path.exists(filepath) or not os.path.isfile(filepath):
		return json.dumps({'error': 'Template not found'}), 404
	
	try:
		with open(filepath, 'r') as f:
			content = f.read()
		return json.dumps({'content': content, 'filepath': filepath})
	except Exception as e:
		return json.dumps({'error': str(e)}), 500


@admin_bp.route('/templates/save/<path:filename>', methods=['POST'])
@admin_required
def save_template_file(filename):
	"""Save template file content."""
	import json
	
	# Sanitize filename to prevent directory traversal
	filename = os.path.basename(filename)
	filepath = os.path.join(TEMPLATES_DIR, filename)
	content = request.form.get('content', '')
	
	try:
		with open(filepath, 'w') as f:
			f.write(content)
		return json.dumps({'success': True, 'message': 'File saved successfully'})
	except Exception as e:
		return json.dumps({'error': str(e)}), 500


@admin_bp.route('/templates/create', methods=['POST'])
@admin_required
def create_template_file():
	"""Create a new template file."""
	import json
	
	filename = request.form.get('filename', '').strip()
	
	if not filename:
		return json.dumps({'error': 'Filename is required'}), 400
	
	# Sanitize filename
	filename = os.path.basename(filename)
	
	if not filename.endswith('.S') and not filename.endswith('.c'):
		return json.dumps({'error': 'Template must have .S or .c extension'}), 400
	
	filepath = os.path.join(TEMPLATES_DIR, filename)
	
	if os.path.exists(filepath):
		return json.dumps({'error': 'File already exists'}), 400
	
	try:
		# Create empty file
		with open(filepath, 'w') as f:
			f.write('')
		return json.dumps({'success': True, 'message': 'File created successfully', 'filename': filename})
	except Exception as e:
		return json.dumps({'error': str(e)}), 500
