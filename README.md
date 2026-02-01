# Event Notification System (Python)

## 📌 Overview
The **Event Notification System** is a backend service built using **Python and FastAPI** that accepts
notification events via REST APIs and processes them **asynchronously** using
**FIFO queues and worker threads**.

The system is designed to demonstrate:
- Clean REST API design
- Thread-safe concurrency
- FIFO event processing
- Graceful shutdown handling
- Callback integration
- Dockerized deployment
- Comprehensive automated testing

---

## 🎯 Supported Event Types

| Event Type | Purpose | Processing Time |
|-----------|--------|-----------------|
| EMAIL | Send email notification | 5 seconds |
| SMS | Send SMS notification | 3 seconds |
| PUSH | Send push notification | 2 seconds |

Each event type:
- Has its **own FIFO queue**
- Has its **own worker thread**
- Is processed **independently and sequentially**

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

```text
                    ┌────────────────────────┐
                    │        Client          │
                    │  (REST API Consumer)   │
                    └──────────┬─────────────┘
                               │
                               │ POST /api/events
                               ▼
                    ┌────────────────────────┐
                    │        FastAPI         │
                    │   (API Layer)          │
                    │                        │
                    │ - Input validation     │
                    │ - Event creation       │
                    │ - Status API           │
                    └──────────┬─────────────┘
                               │
                               │ enqueue(event)
                               ▼
        ┌─────────────────────────────────────────────────┐
        │             EventQueueManager                   │
        │                                                 │
        │   ┌────────────┐  ┌────────────┐  ┌──────────┐  │
        │   │ EMAIL FIFO │  │ SMS FIFO   │  │ PUSH FIFO│  │
        │   └────────────┘  └────────────┘  └──────────┘  │
        └───────┬────────────────┬────────────────┬───────┘
                │                │                │
                ▼                ▼                ▼
      ┌────────────────┐ ┌──────────────────┐ ┌────────────────────┐
      │ EMAIL Worker   │ │ SMS Worker       │ │ PUSH Worker        │
      │ (Thread)       │ │ (Thread)         │ │ (Thread)           │
      │ FIFO processing│ │ FIFO processing  │ │ FIFO processing    │
      │ 5s delay       │ │ 3s delay         │ │ 2s delay           │
      └───────┬────────┘ └───────┬──────────┘ └───────┬────────────┘
              │                  │                    │
              ▼                  ▼                    ▼
     ┌────────────────────────────────────────────────────┐
     │             CallbackDispatcher                     │
     │  - POST success / failure callbacks                │
     └────────────────────────────────────────────────────┘
````

---

## 🧠 Design Principles

* Producer–Consumer pattern
* Single process, multi-threaded
* Thread-safe FIFO queues
* Strict FIFO ordering per event type
* No shared mutable state across workers
* Graceful shutdown without data loss

---

## 📂 Project Structure

```text
event-notification-system/
├── app/
│   ├── main.py                 # FastAPI app + lifecycle
│   ├── config.py               # Environment configuration
│   ├── logging/
│   │   └── logger.py
|   ├── lifecycle/
│   │   └── shutdown.py
│   └── notification/
│       ├── api.py              # REST endpoints
│       ├── models.py           # Domain models + validation
│       ├── queues.py           # FIFO queues
│       ├── workers.py          # Worker threads
│       ├── callbacks.py        # Callback dispatcher
│       ├── exceptions.py
│       └── services/
│           ├── processors.py   # Event processors
│           └── event_status_service.py
├── tests/
│   └── notification/
│       ├── test_api_events.py
│       ├── test_status_api.py
│       ├── test_queue_manager.py
│       ├── test_workers.py
│       ├── test_processors.py
|       ├── test_shutdown_manager.py
|       ├── conftest.py
│       ├── test_callbacks.py
│       └── test_event_status_service.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
├── .dockerignore
└── README.md
```

---

## 🔗 API Routes (Explicit)

All APIs are **namespaced under `/api`**.

### ➕ Create Event

**Route**

```http
POST /api/events
```

#### EMAIL Payload

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

#### SMS Payload

```json
{
  "eventType": "SMS",
  "payload": {
    "phoneNumber": "+911234567890",
    "message": "Your OTP is 123456"
  },
  "callbackUrl": "http://client-system.com/api/event-status"
}
```

#### PUSH Payload

```json
{
  "eventType": "PUSH",
  "payload": {
    "deviceId": "abc-123-xyz",
    "message": "Order shipped!"
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

Here is the corrected and properly formatted Markdown:

---

### ❌ Invalid Event Type

**Payload**

```json
{
  "eventType": "FAX",
  "payload": {},
  "callbackUrl": "http://example.com"
}
```

**Response — 422 Unprocessable Entity**

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "eventType"],
      "msg": "Input should be 'EMAIL', 'SMS' or 'PUSH'"
    }
  ]
}
```



Here is the corrected and properly formatted Markdown:

---

### ❌ Invalid Payload Data Types

**Payload**

```json
{
  "eventType": "PUSH",
  "payload": {
    "deviceId": ["not", "a", "string"],
    "message": "Hello"
  },
  "callbackUrl": "http://example.com"
}

```

**Response — 422 Unprocessable Entity**

```json
{
  "detail": "PUSH payload field 'deviceId' must be of type str, got list"
}

```

### ❌ Invalid Payload Data Types

**Payload**

```json
{
  "eventType": "EMAIL",
  "payload": {
    "recipient": "user@example.com",
    "message": "Hello"
  },
  "callbackUrl": "not-a-url"
}


```

**Response — 422 Unprocessable Entity**

```json
{
  "eventType": "EMAIL",
  "payload": {
    "recipient": "user@example.com",
    "message": "Hello"
  },
  "callbackUrl": "not-a-url"
}


```

**Payload**

```json
{
  "eventType": "PUSH",
  "payload": {
    "deviceId": ["not", "a", "string"],
    "message": "Hello"
  },
  "callbackUrl": "http://example.com"
}

```

**Response — 422 Unprocessable Entity**

```json
{
  "detail": "PUSH payload field 'deviceId' must be of type str, got list"
}

```
---

### 📊 Event Status API

**Route**

```http
GET /api/events/{eventId}/status
```

**Response**

```json
{
  "eventId": "uuid",
  "status": "PENDING"
}
```

Here is the properly formatted Markdown:

---

### ❌ Unknown Event ID

**Request**

```bash
GET /api/events/unknown-id/status
```

**Response — 404 Not Found**

```json
{
  "detail": "Event not found"
}
```


Statuses:

* `PENDING`
* `COMPLETED`
* `FAILED`


| Scenario                | HTTP Status  | Behavior                |
| ----------------------- | ------------ | ----------------------- |
| Invalid request payload | 422          | Rejected before enqueue |
| Unsupported event type  | 422          | Rejected                |
| Invalid callback URL    | 422          | Rejected                |
| Processing failure      | 202 → FAILED | Callback sent           |
| Processing sucess       | 202 → success| Callback sent           |
| Unknown event status    | 404          | Safe failure            |

---

### ❤️ Health Check

**Route**

```http
GET /health
```

---

## 🌍 How to Run the Application
📥 Clone the Repository

```bash
git clone <your-repository-url>
cd event-notification-system
```

### 🧑‍💻 Run Locally (Without Docker)

#### 1️⃣ Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate        # Windows
```

#### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

#### 3️⃣ Configure environment

Edit `.env` if needed:

```env
APP_PORT=8000
LOG_LEVEL=INFO
FAILURE_RATE=0.1
EMAIL_PROCESSING_TIME=5
SMS_PROCESSING_TIME=3
PUSH_PROCESSING_TIME=2
```

#### 4️⃣ Start server

```bash
uvicorn app.main:app --reload
```

#### 5️⃣ API URLs (Local)

```text
POST http://127.0.0.1:8000/api/events
GET  http://127.0.0.1:8000/api/events/{eventId}/status
GET  http://127.0.0.1:8000/health
```

---

### 🐳 Run with Docker

#### 1️⃣ Build & start container

```bash
docker compose up --build
```

#### 2️⃣ API URLs (Docker)

```text
POST http://localhost:8080/api/events
GET  http://localhost:8080/api/events/{eventId}/status
GET  http://localhost:8080/health
```

## 🔔 Callback Payloads

### ✅ Success

```json
{
  "eventId": "e123",
  "eventType": "EMAIL",
  "status": "COMPLETED",
  "processedAt": "2026-01-31T12:34:56Z"
}
```

### ❌ Failure

```json
{
  "eventId": "e123",
  "eventType": "EMAIL",
  "status": "FAILED",
  "errorMessage": "Simulated processing failure",
  "processedAt": "2026-01-31T12:34:56Z"
}
```

---

## 🛑 Graceful Shutdown

On shutdown (`Ctrl+C` / `SIGTERM`):

1. Shutdown signal is raised
2. Workers stop polling for new events
3. Existing queues are fully drained
4. In-progress events finish processing
5. Callbacks are sent
6. Worker threads exit cleanly

---

## ⚙️ Environment Configuration (.env)

```env
APP_PORT=8080
LOG_LEVEL=INFO

# Failure simulation
FAILURE_RATE=0.1

# Processing delays (seconds)
EMAIL_PROCESSING_TIME=5
SMS_PROCESSING_TIME=3
PUSH_PROCESSING_TIME=2
```

All behavior is configurable via environment variables.

---

## 🧪 Testing

Run all tests:

```bash
pytest -v
```

---

## ✅ Testing Coverage Checklist

### API Layer

* ✔ Valid event submission
* ✔ Invalid event type
* ✔ Missing payload fields
* ✔ Invalid payload types
* ✔ Invalid callback URL
* ✔ Status API correctness

### Queue Handling

* ✔ Correct queue assignment by event type
* ✔ FIFO order preservation
* ✔ Queue isolation

### Event Processing

* ✔ Correct processing delay per event type
* ✔ Random failure simulation
* ✔ Failure does not crash workers

### Failure Handling

* ✔ Event marked FAILED
* ✔ Callback triggered on failure
* ✔ Processing continues after failure

### Graceful Shutdown

* ✔ No new events accepted
* ✔ In-flight events complete
* ✔ Queues drained
* ✔ Worker threads terminate cleanly

---

## 🧾 Evaluation Criteria Mapping

| Skill Area        | Demonstrated By               |
| ----------------- | ----------------------------- |
| REST APIs         | FastAPI endpoints, validation |
| Concurrency       | Thread-safe queues, workers   |
| Async Processing  | FIFO worker threads           |
| Callback Handling | Robust HTTP callbacks         |
| Graceful Shutdown | ShutdownManager + lifecycle   |
| Dockerization     | Dockerfile + Compose          |
| Unit Testing      | Pytest coverage of core logic |

---

## 📌 Final Notes

This project intentionally avoids:

* External message brokers
* Persistent storage
* Unnecessary async complexity


---

👨‍💻 **Author:** Shivam
📦 **Tech Stack:** Python, FastAPI, Pytest, Docker

```
