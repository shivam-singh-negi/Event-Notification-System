

````markdown
# Event Notification System (Python)

## 📌 Overview
This project implements an **Event Notification System** using the **Python stack**.  
It exposes a REST API to accept notification events and processes them **asynchronously**
using **FIFO queues** and **background worker threads**.

The system supports the following notification types:
- **EMAIL**
- **SMS**
- **PUSH**

Each event type is processed independently while preserving **FIFO ordering per event type**.

---

## 🎯 Key Features
- REST API built with **FastAPI**
- Asynchronous processing using **worker threads**
- Separate FIFO queues per notification type
- Event status tracking (`PENDING`, `COMPLETED`, `FAILED`)
- Callback notification on completion or failure
- Graceful shutdown handling
- Centralized logging with service-specific loggers
- Fully dockerized (API exposed on **port 8080**)
- Comprehensive automated test suite

---

## 🧠 Architecture Summary

- **Single microservice**
- **Single process**
- **Multiple worker threads**
- **In-memory FIFO queues**
- **No persistent storage (by design)**

The architecture follows the **Producer–Consumer pattern** and is optimized for
clarity, correctness, and testability.

---

## 📂 Project Structure

```text
event-notification-system/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── logging/
│   │   └── logger.py
│   └── notification/
│       ├── api.py
│       ├── models.py
│       ├── queues.py
│       ├── workers.py
│       ├── callbacks.py
│       ├── exceptions.py
│       └── services/
│           ├── processors.py
│           └── event_status_service.py
├── tests/
│   └── notification/
│       ├── test_api_events.py
│       ├── test_status_api.py
│       ├── test_queue_manager.py
│       ├── test_workers.py
│       ├── test_processors.py
│       ├── test_callbacks.py
│       └── test_event_status_service.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
````

---

## 🚀 API Usage

### Create Event

**Endpoint**

```
POST /api/events
```

**Request Body**

```json
{
  "eventType": "EMAIL",
  "payload": {
    "recipient": "user@example.com",
    "message": "Welcome!"
  },
  "callbackUrl": "http://client-system.com/api/event-status"
}
```

**Response (202 Accepted)**

```json
{
  "eventId": "uuid",
  "message": "Event accepted for processing"
}
```

---

### Get Event Status

**Endpoint**

```
GET /api/events/{eventId}/status
```

**Response**

```json
{
  "eventId": "uuid",
  "status": "PENDING"
}
```

Possible statuses:

* `PENDING`
* `COMPLETED`
* `FAILED`

---

### Health Check

**Endpoint**

```
GET /health
```

**Response**

```json
{
  "status": "ok"
}
```

---

## ⏱️ Processing Rules

| Event Type | Simulated Processing Time |
| ---------- | ------------------------- |
| EMAIL      | 5 seconds                 |
| SMS        | 3 seconds                 |
| PUSH       | 2 seconds                 |

* Events are processed **FIFO per event type**
* Random failure simulation is applied
* Callback is triggered on success or failure

---

## 🔔 Callback Payload

### Success

```json
{
  "eventId": "e123",
  "status": "COMPLETED",
  "eventType": "EMAIL",
  "processedAt": "2026-01-31T12:34:56Z"
}
```

### Failure

```json
{
  "eventId": "e123",
  "status": "FAILED",
  "eventType": "EMAIL",
  "errorMessage": "Simulated processing failure",
  "processedAt": "2026-01-31T12:34:56Z"
}
```

---

## 🛑 Graceful Shutdown

On shutdown:

1. API stops accepting new events
2. Workers stop polling after queues drain
3. In-flight events finish processing
4. Worker threads exit cleanly

---


## 🐳 Running with Docker

### Build and Run

```bash
docker compose up --build
```

### API Available At

```
http://localhost:8080/api/events
```

---

## 🧪 Testing

Run all tests locally with:

```bash
pytest -v
```
