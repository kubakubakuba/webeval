import os
import hmac
import hashlib
import toml
import requests
import db
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import urllib.parse

git_bp = Blueprint('git', __name__)

GIT_MAPPING = {}
GIT_CONFIG_PATH = None

def init_git(config_dir):
	global GIT_MAPPING, GIT_CONFIG_PATH
	
	GIT_CONFIG_PATH = os.path.join(config_dir, 'git_mapping.toml')
	
	if os.path.exists(GIT_CONFIG_PATH):
		try:
			with open(GIT_CONFIG_PATH) as f:
				GIT_MAPPING = toml.load(f)
			print(f" [GIT] Loaded mapping from {GIT_CONFIG_PATH}")
		except Exception as e:
			print(f" [GIT] Error loading mapping: {e}")
	else:
		print(f" [GIT] Warning: Configuration file not found at {GIT_CONFIG_PATH}")

def verify_signature(req):
	secret = os.getenv('GIT_WEBHOOK_SECRET')
	if not secret:
		print(" [GIT] Error: GIT_WEBHOOK_SECRET not set in .env")
		return False
		
	gh_signature = req.headers.get('X-Hub-Signature-256')
	if gh_signature:
		expected_signature = 'sha256=' + hmac.new(
			key=secret.encode('utf-8'), 
			msg=req.data, 
			digestmod=hashlib.sha256
		).hexdigest()
		if hmac.compare_digest(gh_signature, expected_signature):
			return True

	gl_token = req.headers.get('X-Gitlab-Token')
	if gl_token:
		if hmac.compare_digest(gl_token, secret):
			return True
			
	return False

def get_task_id_for_path(file_path):
	tasks = GIT_MAPPING.get('tasks', [])
	
	for task in tasks:
		if task['path'] == file_path:
			return task['task_id']
	
	return None

def fetch_file_content(repo_full_name, commit_sha, file_path, project_id=None):
	config = GIT_MAPPING.get('config', {})
	tokens = GIT_MAPPING.get('tokens', [])

	template = config.get('url_template')

	namespace_p = repo_full_name.split("/")
	namespace = namespace_p[0] if namespace_p else None

	org_token = None
	for t in tokens:
		if t.get("name") == namespace:
			org_token = t.get("token")
			#with open("/tmp/fetch_url.txt", "a") as f:
			#	f.write(f"\ngot token: {org_token}\n")
			break

	if not template:
		print(" [GIT] Error: 'url_template' missing in git_mapping.toml")
		return None

	encoded_path = urllib.parse.quote(file_path, safe='')

	url = template.format(
		repo_full_name=repo_full_name,
		commit_sha=commit_sha,
		file_path=file_path,
		project_id=project_id,
		encoded_path=encoded_path
	)

	#with open("/tmp/fetch_url.txt", "a") as f:
	#	f.write(f"\n\n{url}\n")
	#	f.write(f"project_id: {project_id}\n")
	
	try:
		headers = {}
		
		if "gitlab" in url:
			headers['Authorization'] = f"Bearer {org_token}"
			headers['PRIVATE-TOKEN'] = org_token
		else:
			token = os.getenv('GITHUB_TOKEN')
			headers['Authorization'] = f"token {token}"

		response = requests.get(url, headers=headers)
		if response.status_code == 200:
			return response.text
		else:
			print(f" [GIT] Failed to fetch file {url}: HTTP {response.status_code}")
	except Exception as e:
		print(f" [GIT] Error fetching file: {e}")
	return None

def process_submission_logic(username, task_id, code):
	try:
		user_id = db.get_user_id_by_username(username)
		if not user_id:
			return False, f'User {username} not found'
		
		is_admin = db.is_admin_by_id(user_id)
		is_admin = is_admin[0] if is_admin else False

		task = db.get_task(task_id, is_admin=is_admin)
		if not task:
			return False, f'Task {task_id} not found or not available'

		if db.is_banned(user_id):
			return False, 'User is banned'

		user = db.get_user_by_id(user_id)
		if not user or not user[4]: # user[4] is verified field
			return False, 'User is not verified'

		TASKS_DIR = os.getenv('TASKS_DIR', 'tasks')
		task_path_entry = db.get_task_path(task_id)
		
		if task_path_entry:
			task_file_path = os.path.join(TASKS_DIR, os.path.basename(task_path_entry[0]))
			if os.path.exists(task_file_path):
				with open(task_file_path) as f:
					task_data = toml.load(f)
				
				deadlines = task_data.get('task', {})
				start_date = deadlines.get('start_date')
				end_date = deadlines.get('end_date')
				
				now = datetime.now()
				
				if start_date:
					start_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
					if now < start_dt:
						return False, f'Task submissions not yet open. Opens at {start_date}'
				
				if end_date:
					end_dt = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
					if now > end_dt:
						return False, f'Task submissions closed. Deadline was {end_date}'

		code = code.replace('\r\n', '\n')
		db.submit(user_id, task_id, code)
		return True, "Submission successful"

	except Exception as e:
		return False, f"Server error: {str(e)}"

@git_bp.route('/webhook', methods=['POST'])
def handle_webhook():
	#with open("/tmp/webhook.txt", "a") as f:
	#	f.write(f"{request.get_data(as_text=True)}\n\n")

	if not verify_signature(request):
		return jsonify({'error': 'Invalid signature or secret not configured'}), 401
	
	data = request.get_json()
	if not data:
		return jsonify({'message': 'No JSON data'}), 400
	
	if 'commits' not in data:
		return jsonify({'message': 'Event ignored (not a push)'}), 200

	repo_data = data.get('repository')
	project_data = data.get('project')
	if repo_data is None:
		return jsonify({'message': 'No repository data found'}), 400

	repo_name = repo_data.get('name')
	repo_full_name = None
	project_id = None

	if project_data is not None:
		if 'path_with_namespace' in project_data:
			repo_full_name = project_data.get('path_with_namespace')
			project_id = project_data.get('id')

	if repo_full_name is None:
		if 'full_name' in repo_data:
			repo_full_name = repo_data.get('full_name')
	#repo_full_name = repo_data.get('full_name') or repo_data.get('path_with_namespace')
	
	postfix = GIT_MAPPING.get('org', {}).get('postfix', '')
	username = f"{repo_name}{postfix}"

	results = []

	for commit in data['commits']:
		commit_sha = commit['id']
		changed_files = commit.get('added', []) + commit.get('modified', [])
		
		for file_path in changed_files:
			task_id = get_task_id_for_path(file_path)
			
			if task_id:
				print(f" [GIT] Processing {file_path} for user {username} (Task {task_id})")
				
				code_content = fetch_file_content(repo_full_name, commit_sha, file_path, project_id)
				
				if code_content:
					success, msg = process_submission_logic(username, task_id, code_content)
					results.append({
						'file': file_path,
						'task_id': task_id,
						'status': 'success' if success else 'error',
						'message': msg
					})
				else:
					results.append({
						'file': file_path, 
						'status': 'error', 
						'message': 'Failed to fetch file content'
					})

	return jsonify({
		'status': 'processed',
		'username': username,
		'results': results
	}), 200
