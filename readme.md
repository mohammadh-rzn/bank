# Docker setup guide

## .env and docker-compose

make sure .env database config matches docker-compose db enviroment

```env
DB_NAME=bank
DB_USER=bank
DB_PASSWORD=bank
```
```docker-compose
    environment:
      - POSTGRES_DB=bank
      - POSTGRES_USER=bank
      - POSTGRES_PASSWORD=bank
```
## opentelemetry settings
if the os is linux change OTLP_ENDPOINT in .env
```env
OTLP_ENDPOINT=http://172.17.0.1:4317
```
## build and run tracing and metric services

```bash
docker-compose -f docker-compose.otel.yml up -d
```
After successful run...

## build and run django project and database
```bash
docker-compose up -d
```
## running services localhost ports

backend: 8000

grafna: 3000

frontend: 4000

jaeger: 16686

## Grafna settings
go to localhost:3000
click on top left to open menu
on the menu click connections
search and click on prometheus
click add new data source
in connection add this url http://prometheus:9090
now go to home and click on + to  start a new dashboard with available metrics

