# SETUP

## Install dependencies
install inside a python enviroment
```bash
pip install -r requirements.txt
```
## Configure .env file

### Configure database

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=bank
DB_USER=bank
DB_PASSWORD='bank'
DB_HOST=localhost
DB_PORT=5432
```
### Configure rate limit

```env
ANONYMOUS_USER_RATE_LIMIT=100/hour
AUTHENTICATED_USER_RATE_LIMIT=1000/day
LOGIN_RATE_LIMIT=5/minute
BALANCE_RATE_LIMIT=10/minute
TRANSACTION_RATE_LIMIT=10/minute
TRASFER_RATE_LIMIT=10/minute
```
## Start sever

```bash
python manage.py runserver
```