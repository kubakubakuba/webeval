from flask import Blueprint, render_template, session
from util import score_results, user_total_score
import db

get_filtered_users = None
check_admin = None

def init_scoreboard(filter_func, admin_func):
	"""Initialize scoreboard module with configuration."""
	global get_filtered_users, check_admin
	get_filtered_users = filter_func
	check_admin = admin_func

scoreboard_bp = Blueprint('scoreboard', __name__)

@scoreboard_bp.route('/scoreboard/')
def scoreboard():
	"""Display public scoreboard."""
	active_tasks = db.get_active_tasks()

	results = {}

	filtered_users = get_filtered_users()
	
	for task in active_tasks:
		task_id, task_name = task

		results[task_name] = db.get_best_only_scores_for_public(task_id)
		results[task_name] = [result for result in results[task_name] if result[0] not in filtered_users]

	results = score_results(results)

	# Get user ids from results
	user_ids = {}
	for task in results:
		for result in results[task]:
			if result[0] not in user_ids:
				user_ids[result[0]] = 0
			user_ids[result[0]] = result[2]

	total_score = user_total_score(results)

	user_dict = None
	if 'user_id' in session:
		user_id = session['user_id']
		user = db.get_user_by_id(user_id)

		user_dict = {
			'id': user[0],
			'username': user[3],
			'display_name': user[7],
			'country': user[8],
			'organization': user[9],
			'group': user[10],
			'visibility': user[11]
		}

	displaynames = db.get_user_displaynames()
	displaynames = {user[0]: user[1] for user in displaynames}

	return render_template('scoreboard.html', sessions=session, submissions=results, total_score=total_score, user_ids=user_ids, user=user_dict, grouporg=None, displaynames=displaynames)


@scoreboard_bp.route('/scoreboard/grouporg/<int:type>/<string:grouporg>/')
def scoreboard_group(type, grouporg):
	"""Display scoreboard filtered by group or organization."""
	active_tasks = db.get_active_tasks()

	is_admin = check_admin()

	results = {}

	user_id = session.get('user_id')

	user = db.get_user_by_id(user_id) if user_id else None
	user_group = user[10] if user else None
	user_org = user[9] if user else None

	results = {}
	group_text = None

	if type == 0:  # group
		if user_group != grouporg and not is_admin:
			return render_template('403.html'), 403
		
		group_text = "study group " + grouporg
		filtered_users = get_filtered_users()
		for task in active_tasks:
			task_id, task_name = task
			results[task_name] = db.get_best_only_scores_for_group(task_id, grouporg)
			results[task_name] = [result for result in results[task_name] if result[0] not in filtered_users]

	elif type == 1:  # organization
		if user_org != grouporg and not is_admin:
			return render_template('403.html'), 403
		
		group_text = grouporg
		filtered_users = get_filtered_users()
		
		for task in active_tasks:
			task_id, task_name = task
			results[task_name] = db.get_best_only_scores_for_org(task_id, grouporg)
			results[task_name] = [result for result in results[task_name] if result[0] not in filtered_users]

	else:
		return render_template('400.html'), 400

	results = score_results(results)

	user_ids = {}
	for task in results:
		for result in results[task]:
			if result[0] not in user_ids:
				user_ids[result[0]] = 0
			user_ids[result[0]] = result[2]

	total_score = user_total_score(results)

	displaynames = db.get_user_displaynames()
	displaynames = {user[0]: user[1] for user in displaynames}

	return render_template('scoreboard.html', sessions=session, submissions=results, total_score=total_score, user_ids=user_ids, user=None, grouporg=group_text, displaynames=displaynames)
