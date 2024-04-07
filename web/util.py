def user_total_score(results) -> dict:
	total_points = {}
	
	for task in results:
		for result in results[task]:
			if result[0] not in total_points:
				total_points[result[0]] = 0
			total_points[result[0]] += result[3]

	#sort the total_points
	total_points = [(k, total_points[k]) for k in sorted(total_points, key=total_points.get, reverse=True)]

	return total_points
	

def score_task(results) -> list:
	new_results = []

	if len(results) == 0:
		return []

	worst_best_score = results[len(results)-1][1] if len(results) < 5 else results[4][1]

	results_bellow_equal_worst = [result for result in results if result[1] <= worst_best_score]
	rest = [result for result in results if result[1] > worst_best_score]

	#get the minimum of the results_bellow_equal_worst and score them with 6 (append), then remove them, get the minimum and so on until possible
	
	points_awarded = 6

	while len(results_bellow_equal_worst) > 0:
		min_score = min(results_bellow_equal_worst, key=lambda x: x[1])

		for result in [res for res in results_bellow_equal_worst if res[1] == min_score[1]]:
			new_results.append((result[0], result[1], result[2], points_awarded))
			results_bellow_equal_worst.remove(result)

		points_awarded -= 1

	#add zero to every result[3]
	for result in rest:
		new_results.append((result[0], result[1], result[2], 0))


	#sort the results by the points awarded
	new_results.sort(key=lambda x: x[3], reverse=True)
	return new_results		

def score_results(results) -> dict:
	#get the score of the fifth
	
	for task in results:
		results[task] = score_task(results[task])

	#old_way
	# for task in results:
	# 	#mark the first 5 scores
	# 	for i in range(5):
	# 		if i < len(results[task]):
	# 			if i > 0 and results[task][i][1] == results[task][i-1][1]:
	# 				results[task][i] = (results[task][i][0], results[task][i][1], results[task][i][2], results[task][i-1][3])
	# 			else:
	# 				results[task][i] = (results[task][i][0], results[task][i][1], results[task][i][2], 5-i)

	# 	#mark the rest of the scores
	# 	for i in range(5, len(results[task])):
	# 		if results[task][i][1] == results[task][i-1][1]:
	# 			results[task][i] = (results[task][i][0], results[task][i][1], results[task][i][2], results[task][i-1][3])
	# 		else:
	# 			results[task][i] = (results[task][i][0], results[task][i][1], results[task][i][2], 0)

	return results
