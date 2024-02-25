## About

This web application was originally written to allow student to submit [bonus tasks](https://cw.fel.cvut.cz/b222/courses/b35apo/en/homeworks/bonus/start) for the course [B35APO](https://cw.fel.cvut.cz/b222/courses/b35apo/en/start),
but to also allow smaller hackathons to be organized.

The application is written in Python, using the Flask framework. Database is running on a PostgreSQL server. The evaluation system is using [QtRvSim](https://github.com/cvut/qtrvsim), which can be used for [interactive solution](https://comparch.edu.cvut.cz/qtrvsim/app/) of the tasks.

The code is publicly available on [GitLab](https://gitlab.fel.cvut.cz/b35apo/qtrvsim-eval-web).

## How to use the application

Create an account, and check the email that has arrived in your inbox (we do not save your email address).
After successfully verifying your email, you can log in and start submitting the available tasks.

If you are logged in, you can see your best (green) and latest (yellow) score, and you can also view the code you submitted.

When you want to submit a task, you can write the code directly in the integrated code editor (from a blank file, or click the reset button to start from a template).

After the evaluation, the result and output log will be displayed at the bottom of the page. If some errors occured, you can view them in the log.

#### Contact
The application is being maintained by:

Jakub Pelc - **[mail](mailto:webeval@swpelc.eu)** - **[swpelc.eu](https://swpelc.eu)**