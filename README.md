# 🚢 SmartPort AI  
**Real-Time Risk Monitoring & Maritime Delay Prediction**

SmartPort AI is an end-to-end **maritime risk intelligence system** designed to predict, monitor, and act on vessel delays in congested port environments.

It transforms raw AIS movement data into **actionable operational alerts**, identifying vessels at risk of exceeding the **critical 120-minute berthing delay window**, and delivering those insights in real time via a cloud-based dashboard and an AI-powered Telegram assistant.

The system runs continuously, combining **machine learning**, **cloud auditability**, and **natural-language decision support**.

![](images/smartport-image.png)

---

## 🎯 Project Purpose & Business Logic

Ports operate under tight berthing windows. Delays beyond **2 hours (120 minutes)** have cascading operational and economic impact.

**SmartPort AI exists to answer one question clearly and early:**

> *Which vessels are likely to exceed the 120-minute delay threshold, and what should we do about it?*

### Core Objectives
- **Predict** vessel delays exceeding 120 minutes  
- **Categorize risk automatically** (Critical / Warning / Normal)  
- **Notify operators in real time**  
- **Provide clear, explainable actions**, not just scores  

This makes the system **operational**, not just analytical.

---

## 🧠 High-Level System Overview

SmartPort AI is built as a **three-layer ecosystem**:

1. **ML Prediction Engine** – runs delay risk inference  
2. **Cloud Audit & Dashboard** – acts as the operational source of truth  
3. **Command & Control Interface** – Telegram bot with AI reasoning  

Data flows cleanly from prediction → audit → action.

---

## 🏗️ Architecture Overview

![SmartPort AI Architecture](images/architecture_diagram.png)

### 1. ML Engine (Local or Scheduled Execution)

- Processes AIS datasets  
- Engineers movement-based features such as:
  - speed variation  
  - movement stability  
  - heading changes  
- Runs an **XGBoost model** trained for delay risk classification  

**Output per vessel:**
- `risk_score` (0–1 probability)  
- `risk_level` (CRITICAL / WARNING / NORMAL)  
- Recommended operational action  

This layer is deterministic, fast, and auditable.

---

### 2. Cloud Audit & Operational Dashboard (Google Sheets)

Google Sheets is used intentionally as a **lightweight cloud data warehouse** and audit layer.

**Why Google Sheets?**
- Immediate visibility for operations teams  
- Built-in sharing and access control  
- Acts as a **Single Source of Truth**  

#### Key Characteristics
- Every prediction is logged with a **unique `prediction_id`**  
- IDs are generated using **SHA-256 hashing** to prevent duplicates  
- Ensures full traceability of:
  - when the model ran  
  - what it predicted  
  - what action was recommended  

This makes the system **auditable and explainable**, not a black box.

---

### 3. Command & Control: AI-Powered Telegram Bot

Deployed 24/7 on **Railway**, the Telegram bot is the operator’s interface.

It serves two roles:

#### 🔔 Proactive Watchman
- Scans the dashboard every 60 seconds  
- Detects new **CRITICAL** risk entries  
- Sends **consolidated alerts** (anti-spam by design)  

#### 🧠 Intelligent Analyst
- Powered by OpenAI  
- Operators can ask:
  - “Which vessels are at risk right now?”  
  - “What actions should I prioritize?”  
- Supports **English and Spanish**  
- Translates raw data into **plain operational language**  

This closes the loop between prediction and decision.

---

## 🚦 Risk Classification Logic

Each vessel prediction follows a clear decision map:

| Risk Level | Score Range | Operational Meaning | Suggested Action |
|-----------|-------------|---------------------|------------------|
| **CRITICAL** | > 0.80 | High likelihood of >120 min delay | Immediate intervention (reassign berth, escalate) |
| **WARNING** | 0.50 – 0.80 | Elevated risk | Monitor ETA / AIS closely |
| **NORMAL** | < 0.50 | Low risk | Routine operations |

This ensures **consistency and trust** in how alerts are generated.

---

## 📊 Dashboard Schema

The Google Sheets dashboard is structured for fast scanning and audits:

| Column | Description |
|-------|------------|
| `prediction_id` | Unique SHA-256 hash for traceability |
| `timestamp` | Exact execution time of prediction |
| `vessel_id` | Vessel identifier from AIS data |
| `risk_score` | Model confidence (0–1) |
| `risk_level` | CRITICAL / WARNING / NORMAL |
| `action` | Recommended operational response |

---

## 🛠️ Setup & Deployment

### ML Inference
Run locally or on schedule:
```bash
python execution.py
