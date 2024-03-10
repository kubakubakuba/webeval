def score_results(results):
	for task in results:
		#mark the first 5 scores
		for i in range(5):
			if i < len(results[task]):
				if i > 0 and results[task][i][1] == results[task][i-1][1]:
					results[task][i] = (results[task][i][0], results[task][i][1], results[task][i][2], results[task][i-1][3])
				else:
					results[task][i] = (results[task][i][0], results[task][i][1], results[task][i][2], 5-i)

		#mark the rest of the scores
		for i in range(5, len(results[task])):
			if results[task][i][1] == results[task][i-1][1]:
				results[task][i] = (results[task][i][0], results[task][i][1], results[task][i][2], results[task][i-1][3])
			else:
				results[task][i] = (results[task][i][0], results[task][i][1], results[task][i][2], 0)

	return results
