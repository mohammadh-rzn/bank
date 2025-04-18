# Optimization

this file explains what optimization techniques used in detail

## Indexing

transaction model index include user for faster lookup and timestamp for faster ordering
username in user model is already indexed

## Background processing
using django-background-tasks library for background processing in login (to create 10 random transactions)

!!! remember to run worker !!!
```bash
python manage.py process_tasks
```
## Connection pool

using django-db-geventpool library for database connection pooling

## Optimization benchmarks

used benchmark tool is locust

two html files available in project root named before_optimizaion.html and after_optimiztion.html

