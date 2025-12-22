from flask import Blueprint, render_template, request, redirect, session, current_app, jsonify
from auth import login_required
import db
import json
import secrets
from datetime import datetime, timedelta

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/')
@login_required
def profile():
	"""Display user profile."""
	userid = session['user_id']

	user = db.get_user_by_id(userid)

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


@profile_bp.route('/org/<string:country>/<string:org>')
@login_required
def change_org(country, org):
	"""Change user's organization and country."""
	userid = session['user_id']

	organizations = None

	with current_app.open_resource('static/organizations.json') as f:
		organizations = json.load(f)

	if not any(o['name'] == org and o['country'] == country for o in organizations):
		return render_template('400.html'), 400

	db.set_org(userid, country, org)

	return redirect('/profile')


@profile_bp.route('/displayname/<string:displayname>')
@profile_bp.route('/displayname/', defaults={'displayname': ''})
@login_required
def change_displayname(displayname):
	"""Change user's display name."""
	userid = session['user_id']
	
	# Empty string means delete display name
	if displayname:
		displayname = displayname[:32]
	else:
		displayname = None
	
	db.change_displayname(userid, displayname)

	return redirect('/profile')


@profile_bp.route('/privacy/<int:visibility>')
@login_required
def change_privacy(visibility):
	"""Change user's privacy/visibility settings."""
	userid = session['user_id']
	
	# Check if visibility is in range 0-3
	if visibility < 0 or visibility > 3:
		return render_template('400.html'), 400

	db.change_privacy(userid, visibility)

	return redirect('/profile')


@profile_bp.route('/api-key', methods=['GET'])
@login_required
def api_key():
	"""Display user's API key management page."""
	userid = session['user_id']
	user = db.get_user_by_id(userid)
	
	# Get current API key and expiry
	api_key_info = db.get_user_api_key(userid)
	api_key = api_key_info[0] if api_key_info else None
	api_key_expiry = api_key_info[1] if api_key_info else None
	
	# Check if key is expired
	is_expired = False
	if api_key_expiry:
		is_expired = datetime.now() > api_key_expiry.replace(tzinfo=None)
	
	user_dict = {
		'id': user[0],
		'username': user[3],
	}
	
	return render_template('profile_apikey.html', 
		sessions=session, 
		user=user_dict, 
		api_key=api_key,
		api_key_expiry=api_key_expiry,
		is_expired=is_expired)


@profile_bp.route('/api-key/generate', methods=['POST'])
@login_required
def generate_api_key():
	"""Generate a new API key for the user."""
	userid = session['user_id']
	
	# Generate a secure random API key (64 characters)
	new_api_key = secrets.token_urlsafe(48)  # 48 bytes = 64 characters in base64
	
	# Set expiry to 30 days from now
	expiry_date = datetime.now() + timedelta(days=30)
	
	# Save to database
	if db.generate_user_api_key(userid, new_api_key, expiry_date):
		return redirect('/profile/api-key')
	else:
		return render_template('400.html'), 400


@profile_bp.route('/api-key/revoke', methods=['POST'])
@login_required
def revoke_api_key():
	"""Revoke the user's API key."""
	userid = session['user_id']
	
	if db.revoke_user_api_key(userid):
		return redirect('/profile/api-key')
	else:
		return render_template('400.html'), 400
