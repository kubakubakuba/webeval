#!/usr/bin/sh
DATABASE_NAME="qtrvsim_web_eval"

pg_dump -U qtrvsim -h localhost -d $DATABASE_NAME --schema-only -f qtrvsim_web_eval.sql