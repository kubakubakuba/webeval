#!/usr/bin/sh
DATABASE_NAME="qtrvsim_web_eval"

sudo -u postgres pg_dump -U postgres -h localhost -d $DATABASE_NAME --schema-only -f qtrvsim_web_eval.sql