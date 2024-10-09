#!/bin/bash
set -e

source $VENV_DIR/bin/activate

if [ -d /home/qtrvsim-eval-web ]; then
	git clone https://gitlab.fel.cvut.cz/b35apo/qtrvsim-eval-web.git
fi

if [ -f /home/qtrvsim-eval-web/scripts/create_database.sh ]; then
	chmod +x /home/qtrvsim-eval-web/scripts/create_database.sh
	/home/qtrvsim-eval-web/scripts/create_database.sh
fi

ls -la

cd qtrvsim-eval-web/web

ls -la

exec gunicorn -w 3 -b 0.0.0.0:8000 app:app