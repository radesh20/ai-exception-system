# 🚀 P2P Exception Management System

AI-powered system for **exception detection, analysis, human-in-the-loop review, and automated action execution** in Procure-to-Pay (P2P) processes.

---

## 🔹 Tech Stack

* **Backend:** Python + FastAPI
* **Frontend:** React
* **AI Layer:** Deep Agents / Azure OpenAI
* **Storage:** JSON (default) / SQLite / firebase (optional)
* **Process Data:** Celonis (optional)
* **Notifications:** Slack, Gmail, Teams, Outlookgit status
* **Execution:** Internal / ServiceNow

---

## 🔹 What the System Does

* Detects process exceptions
* Analyzes root cause using AI
* Classifies and prioritizes issues
* Decides:

  * ✅ Auto-resolve
  * 👤 Human review
* Learns from human feedback

---

## 🔹 Workflow

```
Celonis / Input Data
        ↓
Context Builder
        ↓
Root Cause Analysis
        ↓
Classifier
        ↓
Action Recommendation
        ↓
AUTO  → Execute
HUMAN → Notify + Dashboard
        ↓
Human Decision
        ↓
Learning Loop
```

---

## 🔹 Key Features

* Exception ingestion (Celonis / JSON)
* AI-based root cause analysis
* Classification:

  * payment_mismatch
  * quantity_mismatch
  * invoice_mismatch
  * goods_receipt_mismatch
  * tax_code_change
  * novel_exception
* Human review dashboard
* Learning from decisions
* Optional integrations (Slack, Gmail, Teams, Outlook)
* ServiceNow execution support

---

## 🔹 Project Structure

```
p2p_exception_system/
│
├── agents/           # AI agents (core logic)
├── api/              # FastAPI routes
├── frontend/         # React dashboard
├── models/           # Data models
├── store/            # Storage layer
├── notifications/    # Alerts (Slack, Gmail, etc.)
├── execution/        # Action execution
├── celonis/          # Celonis integration
├── data/             # Sample + DB
├── scripts/          # Setup scripts
├── tests/            # Unit tests
│
├── main.py
├── main_api.py
└── README.md
```

---

## 🔹 Prerequisites

### Required

* Python 3.10+
* Node.js 18+
* npm

### Optional

* Azure OpenAI
* Celonis
* Slack / Gmail / Teams
* ServiceNow

---

## 🔹 Installation

### 1. Clone Project

```
cd p2p_exception_system
```

### 2. Setup Backend

```
python -m venv venv
source venv/bin/activate   # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
```

### 3. Setup Frontend

```
cd frontend
npm install
cd ..
```

---

## 🔹 Configuration (.env)

Create `.env` file:

```
AZURE_OPENAI_ENABLED=false
CELONIS_ENABLED=false
STORAGE_BACKEND=json
EXECUTION_MODE=internal
CORS_ORIGINS=http://localhost:3000
```

(Extend based on integrations)

---

## 🔹 Run the Project

### ▶ Process Sample Data

```
python main.py
```

### ▶ Start Backend

```
python main_api.py
```

* API: http://localhost:8000
* Docs: http://localhost:8000/docs

### ▶ Start Frontend

```
cd frontend
npm start
```

* UI: http://localhost:3000

---

## 🔹 Frontend Modules

* **Dashboard** → KPIs
* **Incoming Issues** → All exceptions
* **AI Analysis** → Root cause + confidence
* **Pending Decisions** → Human review
* **Action History** → Executed actions
* **Learning Insights** → AI improvement
* **Settings** → Configurations

---

## 🔹 Decision Flow

1. Open exception
2. Review AI insights
3. Choose:

   * Approve
   * Reject
   * Modify
   * Escalate
4. Submit decision

👉 System updates learning automatically

---

## 🔹 Integrations (Optional)

* Slack → Alerts
* Gmail → Email notifications
* Teams → Webhook alerts
* Outlook → Microsoft Graph
* ServiceNow → Ticket execution

---

## 🔹 Storage

Default:

```
data/db/
```

Stores:

* exceptions
* decisions
* actions
* policies
* history

---

## 🔹 Learning Loop

* ✅ Approve → increases confidence
* ❌ Reject → reduces confidence
* ✏️ Modify → improves policy
* ⬆️ Escalate → marks as complex

👉 Result: **More automation over time**

---

## 🔹 API Endpoints (Important)

```
GET  /api/exceptions
POST /api/process
POST /api/decisions
GET  /api/actions
GET  /api/stats
GET  /api/learning
```

---

## 🔹 Run Tests

```
pytest tests/ -v
```

---

## 🔹 Troubleshooting

* Missing dotenv:

  ```
  pip install python-dotenv
  ```
* Backend not connecting:

  * Check port 8000
* Frontend not loading:

  * Check CORS

---

## 🔹 Simple Explanation (Interview)

👉 *“This system uses AI agents to analyze business process exceptions, automatically resolve low-risk issues, and route complex cases to humans, improving efficiency through continuous learning.”*

---
