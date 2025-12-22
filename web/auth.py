from flask import session, redirect, url_for, render_template, request
from functools import wraps
import db as db


def login_required(f):
	"""Decorator to require user to be logged in."""
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'logged_in' not in session:
			return redirect(url_for('login'))
		return f(*args, **kwargs)
	return decorated_function


def admin_required(f):
	"""Decorator to require user to be admin."""
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'logged_in' not in session:
			return redirect(url_for('login'))
		
		userid = session.get('user_id')
		if userid is None:
			return render_template('403.html'), 403
			
		is_admin = db.is_admin_by_id(userid)
		is_admin = is_admin[0] if is_admin else False
		
		if not is_admin:
			return render_template('403.html'), 403
		
		return f(*args, **kwargs)
	return decorated_function


def check_banned(f):
	"""Decorator to check if user is banned and log them out."""
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'user_id' in session:
			is_banned = db.is_user_banned(session['user_id'])
			if is_banned:
				session.clear()
				return redirect(url_for('login'))
		return f(*args, **kwargs)
	return decorated_function


def api_key_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		auth_header = request.headers.get('Authorization')
		
		if not auth_header or not auth_header.startswith('Bearer '):
			return {'error': 'Missing or invalid authorization header'}, 401
		
		api_key = auth_header.replace('Bearer ', '', 1)
		
		if not db.verify_api_key(api_key):
			return {'error': 'Invalid or inactive API key'}, 401
		
		return f(*args, **kwargs)
	return decorated_function

def user_api_key_required(f):
	"""Decorator to require a valid user API key for authentication."""
	@wraps(f)
	def decorated_function(*args, **kwargs):
		auth_header = request.headers.get('Authorization')
		
		if not auth_header or not auth_header.startswith('Bearer '):
			return {'error': 'Missing or invalid authorization header. Use: Authorization: Bearer <api_key>'}, 401
		
		api_key = auth_header.replace('Bearer ', '', 1)
		
		# Verify user API key and get user info
		user_info = db.verify_user_api_key(api_key)
		
		if not user_info:
			return {'error': 'Invalid, expired, or revoked API key'}, 401
		
		user_id, username, verified, can_submit = user_info
		
		if not verified:
			return {'error': 'User account is not verified'}, 403
		
		if not can_submit:
			return {'error': 'User account cannot submit tasks'}, 403
		
		# Pass user info to the wrapped function
		return f(user_id=user_id, username=username, *args, **kwargs)
	
	return decorated_function
