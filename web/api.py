from flask import Blueprint, request
from datetime import datetime
from auth import api_key_required
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
