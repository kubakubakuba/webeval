from flask import Blueprint, request
from datetime import datetime
from auth import api_key_required, user_api_key_required
import db
import os
import toml

TASKS_DIR = None
URL = None

def init_api(tasks_dir, base_url):
	"""Initialize API module with configuration."""
	global TASKS_DIR, URL
	TASKS_DIR = tasks_dir
	URL = base_url

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/submit', methods=['POST'])
@api_key_required
def api_submit():
	"""
	API endpoint to submit a task for a user.
	
	Request body (JSON):
	{
		"username": "user123",
		"task_id": 1,
		"code": "# Assembly or C code here"
	}
	
	Headers:
	Authorization: Bearer <api_key>
	
	Example curl:
	curl -X POST {URL}/api/submit \\
		-H "Authorization: Bearer <your_api_key>" \\
		-H "Content-Type: application/json" \\
		-d '{{"username": "user123", "task_id": 1, "code": "..."}}'
	"""
	try:
		data = request.get_json()
		
		if not data:
			return {'error': 'No JSON data provided'}, 400
		
		username = data.get('username')
		task_id = data.get('task_id')
		code = data.get('code')
		
		if not username or not task_id or not code:
			return {'error': 'Missing required fields: username, task_id, code'}, 400
		
		# Check if task exists and is available
		task = db.get_task(task_id)
		if not task:
			return {'error': f'Task {task_id} not found or not available'}, 404
		
		# Get user ID from username
		user_id = db.get_user_id_by_username(username)
		if not user_id:
			return {'error': f'User {username} not found'}, 404
		
		# Check if user is banned
		is_banned = db.is_banned(user_id)
		if is_banned:
			return {'error': 'User is banned'}, 403
		
		# Check if user is verified
		user = db.get_user_by_id(user_id)
		if not user or not user[4]:  # user[4] is verified field
			return {'error': 'User is not verified'}, 403
		
		# Check submission deadlines
		task_path = db.get_task_path(task_id)
		if task_path:
			task_path = os.path.join(TASKS_DIR, os.path.basename(task_path[0]))
			if os.path.exists(task_path):
				with open(task_path) as f:
					task_data = toml.load(f)
				
				# Check deadlines
				deadlines = task_data.get('task', {})
				start_date = deadlines.get('start_date')
				end_date = deadlines.get('end_date')
				
				if start_date:
					start_datetime = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
					if datetime.now() < start_datetime:
						return {'error': f'Task submissions not yet open. Opens at {start_date}'}, 403
				
				if end_date:
					end_datetime = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
					if datetime.now() > end_datetime:
						return {'error': f'Task submissions closed. Deadline was {end_date}'}, 403
		
		# Submit the code
		code = code.replace('\r\n', '\n')
		db.submit(user_id, task_id, code)
		
		return {
			'success': True,
			'message': 'Submission successful',
			'username': username,
			'task_id': task_id,
			'task_name': task[0],
			'timestamp': datetime.now().isoformat()
		}, 201
		
	except Exception as e:
		return {'error': f'Server error: {str(e)}'}, 500


# User API endpoints (with user API key authentication)

@api_bp.route('/user/tasks', methods=['GET'])
@user_api_key_required
def user_get_tasks(user_id, username):
	"""
	Get list of available tasks for the authenticated user.
	
	Headers:
	Authorization: Bearer <user_api_key>
	
	Returns list of tasks with id, name, and availability status.
	"""
	try:
		tasks = db.list_tasks()
		
		if not tasks:
			return {'tasks': []}, 200
		
		tasks_list = [{'id': task[0], 'name': task[1]} for task in tasks]
		
		return {
			'success': True,
			'username': username,
			'tasks': tasks_list
		}, 200
		
	except Exception as e:
		return {'error': f'Server error: {str(e)}'}, 500


@api_bp.route('/user/task/<int:task_id>', methods=['GET'])
@user_api_key_required
def user_get_task(user_id, username, task_id):
	"""
	Get detailed information about a specific task.
	
	Headers:
	Authorization: Bearer <user_api_key>
	
	Returns task details including description, deadlines, and template code.
	"""
	try:
		task = db.get_task(task_id)
		
		if not task:
			return {'error': f'Task {task_id} not found or not available'}, 404
		
		task_name = task[0]
		
		# Read task file
		task_path = db.get_task_path(task_id)
		if not task_path:
			return {'error': 'Task path not found'}, 404
		
		task_path = os.path.join(TASKS_DIR, os.path.basename(task_path[0]))
		
		if not os.path.exists(task_path):
			return {'error': 'Task file not found'}, 404
		
		with open(task_path) as f:
			task_data = toml.load(f)
		
		task_info = task_data.get('task', {})
		
		# Get template code if available
		template_code = None
		template_path = task_info.get('template')
		if template_path:
			if not os.path.isabs(template_path):
				template_path = os.path.join(os.path.dirname(TASKS_DIR), 'S_templates', os.path.basename(template_path))
			if os.path.exists(template_path):
				with open(template_path) as f:
					template_code = f.read()
		
		# Get user's last submission if any
		last_submission = db.get_last_user_code(task_id, user_id)
		last_code = last_submission[0] if last_submission else None
		
		# Get user's score for this task
		result = db.get_last_user_submission(task_id, user_id)
		score_last = result[2] if result else None
		score_best = None  # get_last_user_submission doesn't return best score
		
		# Get best score separately if needed
		if result:
			# Query for best score from results table
			(db_conn, cursor) = db.connect()
			cursor.execute('SELECT score_best FROM results WHERE taskid = %s AND userid = %s', (task_id, user_id))
			best = cursor.fetchone()
			score_best = best[0] if best else None
			cursor.close()
			db_conn.close()
		
		return {
			'success': True,
			'task_id': task_id,
			'task_name': task_name,
			'description': task_info.get('description'),
			'start_date': task_info.get('start_date'),
			'end_date': task_info.get('end_date'),
			'is_c_solution': task_info.get('c_solution', False),
			'template_code': template_code,
			'last_submission': last_code,
			'score_last': score_last,
			'score_best': score_best
		}, 200
		
	except Exception as e:
		return {'error': f'Server error: {str(e)}'}, 500


@api_bp.route('/user/submit', methods=['POST'])
@user_api_key_required
def user_submit(user_id, username):
	"""
	Submit code for a task using user API key authentication.
	
	Request body (JSON):
	{
		"task_id": 1,
		"code": "# Assembly or C code here"
	}
	
	Headers:
	Authorization: Bearer <user_api_key>
	
	Example curl:
	curl -X POST {URL}/api/user/submit \\
		-H "Authorization: Bearer <your_user_api_key>" \\
		-H "Content-Type: application/json" \\
		-d '{{"task_id": 1, "code": "..."}}'
	"""
	try:
		data = request.get_json()
		
		if not data:
			return {'error': 'No JSON data provided'}, 400
		
		task_id = data.get('task_id')
		code = data.get('code')
		
		if not task_id or not code:
			return {'error': 'Missing required fields: task_id, code'}, 400
		
		# Check if task exists and is available
		task = db.get_task(task_id)
		if not task:
			return {'error': f'Task {task_id} not found or not available'}, 404
		
		task_name = task[0]
		
		# Read task file for deadline checking
		task_path = db.get_task_path(task_id)
		if task_path:
			task_path = os.path.join(TASKS_DIR, os.path.basename(task_path[0]))
			if os.path.exists(task_path):
				with open(task_path) as f:
					task_data = toml.load(f)
				
				# Check deadlines
				deadlines = task_data.get('task', {})
				start_date = deadlines.get('start_date')
				end_date = deadlines.get('end_date')
				
				if start_date:
					start_datetime = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
					if datetime.now() < start_datetime:
						return {'error': f'Task submissions not yet open. Opens at {start_date}'}, 403
				
				if end_date:
					end_datetime = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
					if datetime.now() > end_datetime:
						return {'error': f'Task submissions closed. Deadline was {end_date}'}, 403
		
		# Submit the code
		code = code.replace('\r\n', '\n')
		db.submit(user_id, task_id, code)
		
		return {
			'success': True,
			'message': 'Submission successful',
			'username': username,
			'task_id': task_id,
			'task_name': task_name,
			'timestamp': datetime.now().isoformat()
		}, 201
		
	except Exception as e:
		return {'error': f'Server error: {str(e)}'}, 500
