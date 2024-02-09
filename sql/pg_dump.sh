#!/usr/bin/sh
pg_dump -U postgres -h localhost -d qtrvsim_web_eval --schema-only -f qtrvsim_web_eval.sql