from flask import Blueprint, render_template, request, redirect, session, current_app, jsonify
from auth import login_required
import db
import json
import secrets
from datetime import datetime, timedelta

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


def get_allowed_privacy_levels(user):
	has_group = user[10] is not None and user[10].strip() != ''
	has_org = user[9] is not None and user[9].strip() != ''
	
	if has_group and has_org:
		#both group and org - can use PUBLIC, STUDY_GROUP, or ORG (cannot use PRIVATE)
		return [0, 1, 2]
	elif has_group:
		#study group only - can use PUBLIC or STUDY_GROUP (cannot use PRIVATE or ORG)
		return [0, 2]
	elif has_org:
		#org only - can use PUBLIC or ORG (cannot use PRIVATE or STUDY_GROUP)
		return [0, 1]
	else:
		#no affiliation - can use PRIVATE and PUBLIC (cannot use STUDY_GROUP or ORG)
		return [0, 3]


@profile_bp.route('/')
@login_required
def profile():
	"""Display user profile."""
	userid = session['user_id']

	user = db.get_user_by_id(userid)

	# Get user theme from settings
	user_theme = db.get_user_setting(userid, 'editor_theme') or 'default'

	user_dict = {
		'id': user[0],
		'username': user[3],
		'display_name': user[7],
		'country': user[8],
		'organization': user[9],
		'group': user[10],
		'visibility': user[11]
	}
	
	# Get allowed privacy levels based on user's group/org membership
	allowed_privacy = get_allowed_privacy_levels(user)
	
	# Get user restrictions from settings
	can_change_display_name = db.get_user_setting(userid, 'can_change_display_name')
	if can_change_display_name is None:
		can_change_display_name = True
	else:
		can_change_display_name = can_change_display_name == 'true' or can_change_display_name is True
	
	can_access_api_keys = db.get_user_setting(userid, 'can_access_api_keys')
	if can_access_api_keys is None:
		can_access_api_keys = True
	else:
		can_access_api_keys = can_access_api_keys == 'true' or can_access_api_keys is True

	return render_template('profile.html', sessions=session, user=user_dict, user_theme=user_theme, 
		allowed_privacy=allowed_privacy, can_change_display_name=can_change_display_name, 
		can_access_api_keys=can_access_api_keys)


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
	
	# Check if user is allowed to change display name
	can_change_display_name = db.get_user_setting(userid, 'can_change_display_name')
	if can_change_display_name is not None:
		can_change_display_name = can_change_display_name == 'true' or can_change_display_name is True
	else:
		can_change_display_name = True
	
	if not can_change_display_name:
		return render_template('403.html'), 403
	
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
	
	# Get user info to check allowed privacy levels
	user = db.get_user_by_id(userid)
	allowed_privacy = get_allowed_privacy_levels(user)
	
	# Check if the requested visibility is allowed for this user
	if visibility not in allowed_privacy:
		return render_template('403.html'), 403

	db.change_privacy(userid, visibility)

	return redirect('/profile')


@profile_bp.route('/api-key', methods=['GET'])
@login_required
def api_key():
	"""Display user's API key management page."""
	userid = session['user_id']
	
	# Check if user is allowed to access API keys
	can_access_api_keys = db.get_user_setting(userid, 'can_access_api_keys')
	if can_access_api_keys is not None:
		can_access_api_keys = can_access_api_keys == 'true' or can_access_api_keys is True
	else:
		can_access_api_keys = True
	
	if not can_access_api_keys:
		return render_template('403.html'), 403
	
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


@profile_bp.route('/theme/<theme_name>', methods=['POST'])
@login_required
def save_theme(theme_name):
	"""Save user's preferred editor theme."""
	userid = session['user_id']
	
	valid_themes = ['default', 'monokai', 'dracula', 'material', 'material-darker', 'solarized', 'nord', 'gruvbox-dark', 'twilight', 'ambiance', 'vitesse-dark']
	
	if theme_name not in valid_themes:
		return jsonify({'error': 'Invalid theme'}), 400
	
	if db.set_user_setting(userid, 'editor_theme', theme_name):
		return jsonify({'success': True, 'theme': theme_name}), 200
	else:
		return jsonify({'error': 'Failed to save theme'}), 500
