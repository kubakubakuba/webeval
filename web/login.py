from flask import Blueprint, render_template, request, redirect, session
from flask_mail import Message
from hashlib import sha512
import secrets
import random
import string
import db

URL = None
mail = None

def init_login(base_url, mail_instance):
	"""Initialize login module with configuration."""
	global URL, mail
	URL = base_url
	mail = mail_instance

login_bp = Blueprint('login', __name__)


def send_email(subject, recipient, body, html):
	"""Send an email using Flask-Mail."""
	try:
		msg = Message(subject, recipients=recipient)
		msg.body = body
		msg.html = html
		mail.send(msg)
	except Exception as e:
		return False
	return True


def reset_token(username):
	"""Reset the verification token for a user."""
	db.reset_token(username)


@login_bp.route('/register', methods=['GET', 'POST'])
def register():
	"""Handle user registration."""
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		email = request.form['email']

		salt = secrets.token_hex(16)  # generate random salt for hashing password
		hashed_password = sha512((password + salt).encode()).hexdigest()
		hashed_email = sha512((email + salt).encode()).hexdigest()

		token = ''.join([''.join(random.choices(string.ascii_uppercase + string.digits, k=2)) for _ in range(4)])

		subject = "Verify your email address"
		recipients = [email]
		body = f"Click the link to verify your email address: {URL}/verify/{token}/{username}/{hashed_email}"
		token_parts = [token[i:i+2] for i in range(0, len(token), 2)]
		html = f"""
		<div style='max-width: 600px; margin: 30px auto; text-align: center;'>
			<h2 style='font-size: 20px; margin-bottom: 20px;'>Thanks for registering!</h2>
		</div>

		<div style='max-width: 600px; margin: 0 auto;'>
			<div style='border: 1px solid #ddd; padding: 20px; text-align: center;'>
				<h1 style='font-size: 24px; margin-bottom: 20px;'>Email Verification</h1>
				<table style='margin: 0 auto;'>
					<tr>
						{"".join([f"<td style='border: 1px solid #ddd; padding: 20px; font-size: 24px;'>{part}</td>" for part in token_parts])}
					</tr>
				</table>
				<p style='font-size: 16px; margin-bottom: 30px;'>Click the card below to verify your email address:</p>
				<a href='{URL}/verify/{token}/{username}/{hashed_email}' style='text-decoration: none; color: inherit;'>
					<div style='border: 1px solid #ddd; padding: 20px; cursor: pointer;'>
						<p style='font-size: 16px; margin: 0;'>Verify Email</p>
					</div>
				</a>

				<p style='text-align: center; font-size: 16px; margin-top: 30px;'>Or enter the code manually on the page: <a href='{URL}/verify'>{URL}/verify</a></p>
			</div>
		</div>
		"""

		sent = send_email(subject, recipients, body, html)
		
		if not sent:
			return redirect('/register#email_error')
		
		register_successful = db.register(username, hashed_password, hashed_email, salt, token)
		if register_successful:
			return redirect('/verify')
		else:
			return redirect('/register#username_taken')
	else:
		return render_template('register.html', sessions=session)


@login_bp.route('/verify', methods=['GET', 'POST'])
def verify_manual():
	"""Handle manual email verification with code entry."""
	if request.method == 'POST':
		token = request.form.get('verification0')
		token += request.form.get('verification1')
		token += request.form.get('verification2')
		token += request.form.get('verification3')

		if token == "_banned_":
			token = None

		username = request.form.get('username')
		
		success = db.verify_manual(token, username)
		if success:
			reset_token(username)
			return redirect('/login')
		else:
			return redirect('/verify')
	return render_template('verify.html')


@login_bp.route('/verify/<token>/<user>/<email>', methods=['GET'])
def verify_auto(token, user, email):
	"""Handle automatic email verification via link."""
	if token == "_banned_":
		token = None

	success = db.verify_auto(token, user, email)
	if success:
		reset_token(user)
		return redirect('/login')
	else:
		return redirect('/verify')


@login_bp.route('/reset', methods=['GET', 'POST'])
def reset():
	"""Handle password reset request."""
	if request.method == 'POST':
		username = request.form['username']
		email = request.form['email']

		user = db.get_user(username)

		is_banned = db.is_banned(user[0])

		if user is None or is_banned:
			return redirect('/reset')

		user_id, hashed_password, salt, username, verified, email_hashed, token, display_name, country, organization, group, visibility = user

		if sha512((email + salt).encode()).hexdigest() != email_hashed:
			return redirect('/reset')

		token = ''.join([''.join(random.choices(string.ascii_uppercase + string.digits, k=2)) for _ in range(4)])

		subject = "Reset your password"
		recipients = [email]
		body = f"Click the link to reset your password: {URL}/newpassword"
		token_parts = [token[i:i+2] for i in range(0, len(token), 2)]
		html = f"""
		<div style='max-width: 600px; margin: 30px auto; text-align: center;'>
			<h2 style='font-size: 20px; margin-bottom: 20px;'>You have requested a password reset for you account.</h2>
		</div>

		<div style='max-width: 600px; margin: 0 auto;'>
			<div style='border: 1px solid #ddd; padding: 20px; text-align: center;'>
				<h1 style='font-size: 24px; margin-bottom: 20px;'>Reset Password</h1>
				<table style='margin: 0 auto;'>
					<tr>
						{"".join([f"<td style='border: 1px solid #ddd; padding: 20px; font-size: 24px;'>{part}</td>" for part in token_parts])}
					</tr>
				</table>
				<p style='font-size: 16px; margin-bottom: 30px;'>Click the card below to verify your email address:</p>
				<a href='{URL}/newpassword' style='text-decoration: none; color: inherit;'>
					<div style='border: 1px solid #ddd; padding: 20px; cursor: pointer;'>
						<p style='font-size: 16px; margin: 0;'>Reset Password</p>
					</div>
				</a>

				<p style='text-align: center; font-size: 16px; margin-top: 30px;'>Or enter the code manually on the page: <a href='{URL}/newpassword'>{URL}/newpassword</a></p>
			</div>
		</div>
		"""

		sent = send_email(subject, recipients, body, html)

		if not sent:
			return redirect('/reset#email_error')

		db.add_verify_code(username, token)

		return redirect('/newpassword')
	else:
		return render_template('reset.html', sessions=session)


@login_bp.route('/newpassword', methods=['GET', 'POST'])
def newpassword():
	"""Handle setting new password after reset."""
	if request.method == 'POST':
		token = request.form.get('verification0')
		token += request.form.get('verification1')
		token += request.form.get('verification2')
		token += request.form.get('verification3')

		username = request.form.get('username')
		email = request.form.get('email')
		password = request.form.get('password')

		user = db.get_user(username)

		is_banned = db.is_banned(user[0])

		if user is None or is_banned:  # if user is banned prohibit the password change
			return redirect('/newpassword')

		user_id, hashed_password, salt, username, verified, email_hashed, token, display_name, country, organization, group, visibility = user

		new_hashed_password = sha512((password + salt).encode()).hexdigest()

		if sha512((email + salt).encode()).hexdigest() != email_hashed:
			return redirect('/newpassword')
		
		success = db.set_new_password(username, new_hashed_password, token)

		if success:
			reset_token(username)
			return redirect('/login')
		else:
			return redirect('/newpassword')
	
	return render_template('newpassword.html')


@login_bp.route('/login', methods=['GET', 'POST'])
def login():
	"""Handle user login."""
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']

		user = db.get_user(username)

		if user is None:
			return render_template('invalid.html', redirect_url='/login')

		user_id, hashed_password, salt, username, verified, email, token, display_name, country, organization, group, visibility = user

		if sha512((password + salt).encode()).hexdigest() == hashed_password:
			if verified == 0:
				if token == "_banned_":
					return render_template('banned.html', sessions=session)
				return redirect('/verify')
			
			session['logged_in'] = True
			session['user_id'] = user_id
			session['username'] = username
			return redirect('/')
		else:
			return render_template('invalid.html', redirect_url='/login')
	else:
		return render_template('login.html', sessions=session)


@login_bp.route('/logout')
def logout():
	"""Handle user logout."""
	session.clear()
	return redirect('/login')
