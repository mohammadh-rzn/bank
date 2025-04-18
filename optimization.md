# 🚀 Backend Optimization Report

This document outlines the performance improvements and scalability measures implemented on Day 5 of the AI Trial Project.

---

## ✅ Summary of Optimizations

| Optimization Area         | Techniques Applied                                    |
|---------------------------|--------------------------------------------------------|
| API Performance           | Query indexing, caching, connection pooling           |
| Abuse Prevention          | Rate limiting via DRF throttle classes                |
| Background Processing     | Async transaction generation using django-background-tasks |
| Observability             | Structured logging, Prometheus metrics, Grafana dashboards |
| Test Coverage             | Unit and integration tests with functional validation |
| Performance Benchmarking  | Load testing with Locust (before/after comparisons)   |

---

## 🔍 Indexing

To optimize query performance on the Transaction model:

- Added **index on `user` foreign key** for fast filtering
- Added **index on `timestamp`** to improve ordering performance
- `username` in the User model was already indexed by Django

These changes significantly reduce lookup latency for balance and transaction views.

---

## ⚙️ Background Processing

### Why?
To offload transaction generation logic from the login request for better responsiveness.

### How?
Used `django-background-tasks` to create 1–10 random transactions in the background:

```bash
python manage.py process_tasks
```

- Triggered on login
- Runs independently of main request lifecycle
- Simplifies async integration without needing Celery

---

## 🌐 Database Connection Pooling

### Library Used
- `django-db-geventpool`

### Benefits
- Efficient reuse of DB connections
- Handles concurrent user access under load
- Simple plug-in for PostgreSQL via `DATABASES` configuration

---

## 🔒 Rate Limiting

### Approach
Used **Django REST Framework's** throttling mechanism:

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/day',
        'anon': '10/minute',
    }
}
```

### Purpose
- Prevent brute force or API abuse
- Improves backend stability under stress

---

## 🧠 Caching Strategy

### Tool
- In-memory caching via Django cache framework (Redis-ready)

### Example
Cached user balance queries for 60 seconds:

```python
    cached_data = get_cached_user_balance(request.user.id)
    if cached_data is not None:
        return Response(cached_data)
    data = {'balance':request.user.balance}
    cache_user_balance(request.user.id, data)
    return Response(data)
```

### Outcome
- Reduced repeated DB hits
- Faster balance retrieval for logged-in users

---

## 🧪 Benchmark Results (via Locust)

| Metric                  | Before Optimization | After Optimization |
|------------------------|---------------------|--------------------|
| Requests/sec (RPS)     | 36.1                | 36.4               |
| Average Response Time  | 32.11ms             | 25.21ms            |
| 95% Response Time      | 78ms                | 74ms               |
| Error Rate             | 0.02/sec            | 0.0/sec            |

### Observations
- 21% decrease in latency
- drop in error rate due to pooling and async work

---

## 🧪 Testing Strategy

- Coverage includes:
  - Balance endpoint
  - Transaction endpoint
  - Login + background task trigger
  - Error handling and edge cases (e.g., overdraw attempts)

- Tools: Django TestCase + DRF APIClient


---

## 📈 Observability

- Integrated Prometheus exporters
- Custom Grafana dashboard with:
  - Request latency
  - DB pool usage
  - Task queue activity
  - Error logs (structured)

---

## 🧠 Technical Justifications

| Decision Area             | Choice Made                     | Justification |
|---------------------------|----------------------------------|---------------|
| Background Processing     | `django-background-tasks`       | Simpler than Celery, adequate for small scale |
| DB Pooling                | `django-db-geventpool`          | Easy drop-in for PostgreSQL, proven concurrency benefits |
| Caching                   | Django in-memory (extendable to Redis) | Avoided Redis dependency for trial; extensible |
| Rate Limiting             | DRF Throttle Classes             | Lightweight, built-in, production-proven |
| Benchmarking              | Locust                          | Realistic, programmable load simulation |

---

## ✅ Conclusion

All critical backend components were optimized for:
- Performance 🚀
- Scalability 📈
- Reliability 🔁
- Security 🔐

Next steps: Scale to multi-node deployment with Redis and Celery for production-grade resilience.