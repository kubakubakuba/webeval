# QtRVSim online evaluation

The app will be written in Flask and will be using a MySQL database.

## Roadmap:
- [x] Users are able to register
- [x] Users are able to login
- [x] List of tasks is displayed on the homepage
- [x] Tasks are displayed on their separate pages which the homepage links to
- [x] Logged in users are able to submit solutions on the submit page (with the task number)
- [x] The submission form has a textarea for the task solution (library CodeMirror for assembly highlighting)
- [x] After submitting, the file will be saved in a folder, and a new record will be created in the submission table
- [x] A file will be evaluated and the submission closed, results will be saved in results file
- [x] The results will be displayed on the submission page
- [ ] Automatic evaluator, which periodically checks for new submissions and evaluates them
- [ ] On each task page, a leaderboard will be shown with the users best submissions (in cycles), made by a request (to the submissions table) for that task
- [ ] Each user will only have the best submission listed (or the latest more probably)

## Database structure (subject to change):
### Users table
- user id (primary, auto increment, int)
- username (varchar)
- user password hash (varchar)
- user password salt (varchar)
- user email (varchar) -> maybe not needed

### Submissions table
- submission id (primary, auto increment, int)
- username (varchar)
- task id (varchar)
- filepath (vacrchar) -> path to the submission file
- evaluated (bool, default false)
- result (varchar, default NULL) -> possibly a link to an evaluation result (with errors), or JSON file in the database directly
- score (int, default -1) -> score in cycles, if negative, task has not been evaluated, or has errors
- time (datetime) -> time of submission

Users submits a task -> a submission is created. An evaluator evaluates the tasks in the order they came in the database.
After a task is evaluated, it is marked as evaluated, so it is not evaluated more than one time. An evaluation log is created.
(the log may be deleted, once a new submission is sibmitted on the same task, as well as the old submission file created by the user, -> this may or may not be required in order to save some space on the server and in the database).

### Tasks table
- task id (primary, auto increment, int)
- task name (varchar)
- task path (varchar)
- available (bool) -> if the task is available to submit

~~Database are currently running on local XAMPP server, will be migrated to a VPS when possible.~~

Database is running on a remote VPS (omega.swpelc.eu, 158.101.208.70:3306)
Testing app is running on the same server on port 5000 [here](https://omega.swpelc.eu:5000). 

<img src="rsrc/riscvdb.png" width="550">

## Task creation
Tasks will be stored in toml format, with structure similar to this one (subject to change):

```toml
[task]
name = "Example Task Name"

description = '''
# Task Title

This is a **description** of the task. Here, you can include:

- Objectives
- Detailed instructions
- Any relevant information in Markdown format

Write a [bubble sort](https://en.wikipedia.org/wiki/Bubble_sort).
'''

[arguments]
run = "--asm submission.S"

[[inputs]]
data_in = "9 8 7 6 5 4 3 2 1"
data_out = "1 2 3 4 5 6 7 8 9"
description = "Reversed sequence"

[[inputs]]
data_in = "4 9 6 4 7 8 5 1 5 5"
data_out = "1 4 4 5 5 5 6 7 8 9"
description = "Sequence with duplicates"
```
The inputs and ouputs, are the data, which the program will be tested on. (should they be stored in a separate file, or can just be stores as a string here?)
Arguments are the flags, which will be passed to the qtrvsim. User also sees the --asm submission.S flag for their information.

## Task evaluation log
~~The task evaluation log will be stored in a JSON file, with structure similar to this one (subject to change):~~

```json
{
	"taskid": "task id",
	"user": "username",
	"submission": "submission id",
	"timestamp": "2023-01-01 00:00:00",
	"error_log": "error log\nline 2\nline 3",
	"result": "accepted/rejected",
	"score": "score in cycles"
}
```
This is curently implemented as a plaintext file, from which result are read using regex.
Probably will be better to transfer this to a JSON file, which will be easier to parse in the future.

## Acknowledgements
- [Flask](https://flask.palletsprojects.com/en/3.0.x/)
- [CodeMirror](https://codemirror.net/)
- [Bootstrap](https://getbootstrap.com/)
- [QtRVSim](https://github.com/cvut/qtrvsim)
