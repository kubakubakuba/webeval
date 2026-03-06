"""
SSO Authentication Module for CTU FEL OpenID Connect
Handles SSO login, account linking, and callback processing.
"""

from flask import Blueprint, redirect, url_for, session, request, render_template, current_app
from authlib.integrations.flask_client import OAuth
import db
import os
from datetime import datetime, timezone

sso_bp = Blueprint('sso', __name__)

oauth = None
OIDC_CLIENT_ID = os.getenv('OIDC_CLIENT_ID')
OIDC_CLIENT_SECRET = os.getenv('OIDC_CLIENT_SECRET')
OIDC_SERVER_URL = os.getenv('OIDC_SERVER_URL', 'https://auth-test.fel.cvut.cz')  #default to test
OIDC_REDIRECT_URI = None

def init_sso(app):
	"""Initialize SSO OAuth client."""
	global oauth, OIDC_REDIRECT_URI
	
	oauth = OAuth(app)
	OIDC_REDIRECT_URI = os.getenv('OIDC_REDIRECT_URI', f"{os.getenv('BASE_URL')}/sso/callback")
	
	#register CTU FEL OIDC client
	oauth.register(
		name='ctu_fel',
		client_id=OIDC_CLIENT_ID,
		client_secret=OIDC_CLIENT_SECRET,
		server_metadata_url=f'{OIDC_SERVER_URL}/realms/fel/.well-known/openid-configuration',
		client_kwargs={
			'scope': 'openid'
		}
	)


@sso_bp.route('/login')
def sso_login():
	"""Initiate SSO login flow."""
	if not oauth:
		return render_template('error.html', error='SSO is not configured'), 500
	
	# Store intended action in session (login vs link)
	session['sso_action'] = request.args.get('action', 'login')
	
	# Use configured redirect URI (from env var) instead of generating from request
	redirect_uri = OIDC_REDIRECT_URI if OIDC_REDIRECT_URI else url_for('sso.sso_callback', _external=True)
	
	# Redirect to CTU FEL authorization page
	return oauth.ctu_fel.authorize_redirect(redirect_uri)


@sso_bp.route('/callback')
def sso_callback():
	"""Handle SSO callback after authentication."""
	if not oauth:
		return render_template('error.html', error='SSO is not configured'), 500
	
	try:
		# Get access token and user info
		token = oauth.ctu_fel.authorize_access_token()
		userinfo = token.get('userinfo')
		
		if not userinfo:
			return render_template('error.html', error='Failed to get user information from SSO'), 400
		
		# Extract claims
		sso_username = userinfo.get('preferred_username')
		given_name = userinfo.get('given_name', '')
		family_name = userinfo.get('family_name', '')
		full_name = userinfo.get('name', f"{given_name} {family_name}".strip())
		
		if not sso_username:
			return render_template('error.html', error='SSO did not provide username'), 400
		
		# Get intended action
		action = session.pop('sso_action', 'login')
		
		if action == 'link':
			# User is linking SSO to existing account
			return _handle_sso_link(sso_username, full_name)
		else:
			# User is logging in with SSO
			return _handle_sso_login(sso_username, full_name, given_name, family_name)
	
	except Exception as e:
		current_app.logger.error(f"SSO callback error: {str(e)}")
		return render_template('error.html', error=f'SSO authentication failed: {str(e)}'), 500


def _handle_sso_login(sso_username, full_name, given_name, family_name):
	"""Handle SSO login - either login existing account, show selector, or show error."""
	# Check if accounts with this SSO exist
	users = db.get_all_users_by_sso('ctu_fel', sso_username)
	
	if not users:
		# No account linked to this SSO
		# Store SSO info temporarily for potential account creation/linking
		session['sso_temp'] = {
			'username': sso_username,
			'full_name': full_name,
			'given_name': given_name,
			'family_name': family_name,
			'provider': 'ctu_fel'
		}
		return redirect(url_for('sso.sso_not_linked'))
	
	elif len(users) == 1:
		# Single account found - log in directly
		user = users[0]
		user_id, username, display_name, organization, group, verified, can_submit = user
		
		if not verified:
			return render_template('error.html', error='Your account is not verified'), 403
		
		if not can_submit:
			return render_template('error.html', error='Your account is disabled'), 403
		
		# Set session
		session['logged_in'] = True
		session['user_id'] = user_id
		session['username'] = username
		session['login_method'] = 'sso'
		
		return redirect('/')
	
	else:
		# Multiple accounts found - show selector
		session['sso_accounts'] = {
			'sso_username': sso_username,
			'full_name': full_name,
			'accounts': [
				{
					'id': str(user[0]),
					'username': user[1],
					'display_name': user[2],
					'organization': user[3],
					'group': user[4],
					'verified': user[5],
					'can_submit': user[6]
				}
				for user in users
			]
		}
		return redirect(url_for('sso.sso_account_selector'))


def _handle_sso_link(sso_username, full_name):
	"""Handle linking SSO to currently logged-in account."""
	# User must be logged in to link
	if 'logged_in' not in session or 'user_id' not in session:
		return redirect(url_for('login.login'))
	
	user_id = session['user_id']
	
	# Link SSO to current account (allows multiple accounts per SSO)
	success = db.link_sso_to_user(user_id, 'ctu_fel', sso_username, full_name)
	
	if success:
		return redirect(url_for('profile.profile', sso_linked=True))
	else:
		return render_template('error.html', 
			error='Failed to link SSO account. Your account may already have SSO linked.'), 500


@sso_bp.route('/not-linked')
def sso_not_linked():
	"""Show page when SSO user doesn't have linked account."""
	sso_info = session.get('sso_temp')
	
	if not sso_info:
		return redirect(url_for('login.login'))
	
	return render_template('sso_not_linked.html', 
						 sso_username=sso_info['username'],
						 sessions=session)


@sso_bp.route('/account-selector')
def sso_account_selector():
	"""Show account selector when multiple accounts are linked to SSO."""
	accounts_data = session.get('sso_accounts')
	
	if not accounts_data:
		return redirect(url_for('login.login'))
	
	return render_template('sso_account_selector.html', 
						 sso_username=accounts_data['sso_username'],
						 accounts=accounts_data['accounts'],
						 sessions=session)


@sso_bp.route('/select-account/<user_id>')
def sso_select_account(user_id):
	"""Select an account from the account selector."""
	accounts_data = session.get('sso_accounts')
	
	if not accounts_data:
		return redirect(url_for('login.login'))
	
	# Verify the user_id is in the list of accounts
	selected_account = None
	for account in accounts_data['accounts']:
		if account['id'] == user_id:
			selected_account = account
			break
	
	if not selected_account:
		return render_template('error.html', error='Invalid account selection'), 400
	
	if not selected_account['verified']:
		return render_template('error.html', error='Selected account is not verified'), 403
	
	if not selected_account['can_submit']:
		return render_template('error.html', error='Selected account is disabled'), 403
	
	# Set session
	session['logged_in'] = True
	session['user_id'] = user_id
	session['username'] = selected_account['username']
	session['login_method'] = 'sso'
	
	# Clear temporary SSO data
	session.pop('sso_accounts', None)
	
	return redirect('/')


@sso_bp.route('/unlink', methods=['POST'])
def sso_unlink():
	"""Unlink SSO from currently logged-in account."""
	if 'logged_in' not in session or 'user_id' not in session:
		return redirect(url_for('login.login'))
	
	user_id = session['user_id']
	
	# Check if user has password login enabled
	user = db.get_user_by_id(user_id)
	if user and len(user) > 12:  # Check if SSO fields exist
		# Get password_login_enabled from user tuple
		sso_status = db.get_user_sso_status(user_id)
		if sso_status and not sso_status['password_login_enabled']:
			return render_template('error.html', 
				error='Cannot unlink SSO: password login is disabled. Enable password login first.'), 400
	
	# Unlink SSO
	success = db.unlink_sso_from_user(user_id)
	
	if success:
		return redirect(url_for('profile.profile', sso_unlinked=True))
	else:
		return render_template('error.html', error='Failed to unlink SSO'), 500
