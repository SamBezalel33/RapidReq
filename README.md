# RAPIDREQ
### Priority-Based Emergency Request & Dispatch System
*An Academic Data Structures Project (Master's / Bachelor's Level)*

---

## 1. Project Title & Overview
**RAPIDREQ: Priority-Based Emergency Request & Dispatch System**

In modern emergency response management (Ambulance, Fire, Rescue), life-or-death scenarios arrive simultaneously. Processing emergency calls on a traditional First-Come, First-Served (FCFS / FIFO) basis leads to dangerous delays for critical patients. **RapidReq** replaces arrival-time dispatching with an explicit **Priority Queue**, ensuring that the most urgent emergencies are dispatched first while guaranteeing fair FIFO ordering among emergencies of equal severity.

---

## 2. Problem Statement
In real-world dispatch centers:
- Multiple 911 / 108 emergency requests arrive at the same time.
- All emergencies **do NOT have the same urgency**:
  - A multi-car highway accident with severe bleeding is far more time-critical than a minor ankle sprain or a fallen tree.
- A standard First-In, First-Out (FIFO) queue will force a Critical (Priority 1) cardiac arrest to wait behind low-priority incidents simply because the low-priority incident was logged 30 seconds earlier.
- Hence, the system requires a **Priority Queue** where urgency level governs the dispatch sequence.

---

## 3. Project Objective
1. Implement a custom, transparent **Priority Queue** in Python from scratch.
2. Demonstrate **Priority-Based Dispatching**:
   - `Priority 1`: Critical (Highest Urgency)
   - `Priority 2`: High
   - `Priority 3`: Medium
   - `Priority 4`: Low (Lowest Urgency)
3. Ensure **Deterministic FIFO Tie-Breaking**: When two emergencies share identical priority ratings, the one that arrived earlier is dispatched first.
4. Integrate the Priority Queue directly into a **Flask Web Application**, backed by a **MySQL Database** for persistent record keeping.
5. Provide real-time data visualization via **Chart.js** displaying incident patterns and response time metrics.

---

## 4. Why a Priority Queue is Used
| Data Structure | Processing Rule | Emergency Suitability | Why / Why Not? |
| :--- | :--- | :--- | :--- |
| **Standard Queue (FIFO)** | Arrived First = Processed First | ❌ Dangerous | A minor cat rescue arriving at 10:00 AM blocks a fatal heart attack arriving at 10:01 AM. |
| **Stack (LIFO)** | Arrived Last = Processed First | ❌ Unfair | Earliest callers get starved indefinitely. |
| **Priority Queue** | Highest Urgency = Processed First | ✅ Optimal & Safe | Critical cases jump ahead of minor cases. Tie-breaker ensures no starvation. |

---

## 5. Technology Stack
- **Backend**: Python 3.11+, Flask 3.x
- **Data Structure**: Custom Python `EmergencyPriorityQueue` class (`priority_queue.py`)
- **Database**: MySQL / MariaDB (via PyMySQL)
- **Frontend**: HTML5, CSS3 (Modern Responsive Flexbox/Grid), Vanilla JavaScript
- **Visualization**: Chart.js 4.x
- **Icons & Fonts**: Font Awesome 6, Google Inter & JetBrains Mono

---

## 6. Project Directory Structure
```text
Rapidreq/
│
├── app.py                  # Flask Application Controller & Web Routes
├── priority_queue.py       # Core Academic Priority Queue Implementation
├── database.py             # MySQL Database Access Layer & Aggregations
├── database.sql            # MySQL Database Creation Script & Sample Data
├── requirements.txt        # Python Dependencies (Flask, PyMySQL, python-dotenv)
├── README.md               # Complete Academic Documentation & Viva Guide
│
├── templates/
│   ├── base.html           # Master Layout (Sidebar, Navigation, Topbar, Flash Alerts)
│   ├── index.html          # Project Overview, Rationale & Workflow
│   ├── submit.html         # Emergency Incident Intake Form
│   ├── dashboard.html      # Dispatcher Live Control Room & Visual Priority Queue
│   ├── requests.html       # Emergency Request Management Table with Filters
│   ├── request_details.html# Forensic Dossier & Lifecycle Timeline
│   └── analytics.html      # Full Chart.js Analytics Dashboard (4 Real-Time Charts)
│
└── static/
    ├── css/
    │   └── style.css       # Custom Emergency Theme, Priority Colors & Animations
    └── js/
        └── dashboard.js    # Chart.js Visualizations & REST API Integrations
```

---

## 7. How the Priority Queue Works

The core logic lives inside [`priority_queue.py`](file:///c:/Users/acer/OneDrive/Desktop/Rapidreq/priority_queue.py):

### The Emergency Node
Each request in the queue is wrapped inside an `EmergencyNode`:
- `priority`: Integer value from `1` (Critical) down to `4` (Low).
- `arrival_order`: A sequence counter incremented on every enqueue to break ties deterministically.

### Enqueue Algorithm (`add_request`):
1. Increment `sequence_counter`.
2. Compare the incoming node's priority with existing nodes:
   - If `incoming.priority < existing.priority`, the incoming emergency is **more urgent** (since $1 < 2 < 3 < 4$). Insert `incoming` **before** `existing`.
   - If `incoming.priority == existing.priority`, continue traversing. The incoming request is placed **after** older requests of the same priority, guaranteeing **FIFO tie-breaking**.
3. If no lower-priority node is found, append to the end.

### Dequeue Algorithm (`dispatch_next`):
- Because the list is continuously maintained in priority order, the next highest-priority emergency is always at **index 0** (`queue[0]`).
- Pops index 0 in $O(1)$ amortized time.

### Peek Algorithm (`get_next_request`):
- Inspects `queue[0]` without popping, enabling the Dispatcher UI to preview the next dispatch candidate.

---

## 8. Complete System Flow
```text
USER SUBMITS EMERGENCY REQUEST
        ↓
FLASK BACKEND VALIDATION
        ↓
ASSIGN PRIORITY (1 to 4)
        ↓
ADD TO PRIORITY QUEUE (priority_queue.py)
        ↓
STORE IN MYSQL (`emergency_requests` status='Pending')
        ↓
DISPATCHER DASHBOARD (Shows Visual Priority Queue)
        ↓
DISPATCHER CLICKS "DISPATCH NEXT"
        ↓
DEQUEUE HIGHEST PRIORITY NODE
        ↓
CALCULATE RESPONSE TIME (dispatch_time - request_time)
        ↓
UPDATE MYSQL (status='Dispatched')
        ↓
CHART.JS REAL-TIME ANALYTICS REFRESH
```

---

## 9. How to Install and Run

### Step 1: Clone or Navigate to Directory
```powershell
cd "c:\Users\acer\OneDrive\Desktop\Rapidreq"
```

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Start MySQL Database
If using XAMPP:
1. Open XAMPP Control Panel and start **MySQL**, or run:
```powershell
& "C:\xampp\mysql\bin\mysqld.exe" --defaults-file="C:\xampp\mysql\bin\my.ini" --standalone
```
2. The application includes **Auto-Initialization**: when you run `python app.py`, it automatically creates the `rapidreq` database, creates the `emergency_requests` table, and seeds initial sample records if not already populated!

*(Optional manual import via MySQL CLI)*:
```powershell
mysql -u root -p < database.sql
```

### Step 4: Run the Flask Web Application
```powershell
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 10. Testing the Priority Queue (The Professor's Verification Test)

The project includes an automatic Viva Test Loader button in the sidebar (**"Load Viva Test Queue"**) or direct testing via `/reset-demo-queue`.

### Test Case Walkthrough:
Consider 4 emergency requests submitted in this arrival sequence:

| Step | Request ID | Caller | Emergency Type | Priority | Expected Position in Queue |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **R201** | Divya | Rescue | **3 (Medium)** | Initially #1 |
| 2 | **R202** | Arun | Accident | **1 (Critical)** | **Jumps to #1** ahead of R201 |
| 3 | **R203** | Priya | Medical Emergency | **2 (High)** | Inserts at #2 (Behind R202, ahead of R201) |
| 4 | **R204** | Karthik | Fire | **1 (Critical)** | Inserts at #2 (Behind R202 due to FIFO tie-break, ahead of R203 & R201) |

### Current Queue State in Dashboard:
1. 🔴 **R202** | Priority 1 (Critical) — *Arrived first among P1*
2. 🔴 **R204** | Priority 1 (Critical) — *Arrived second among P1*
3. 🟠 **R203** | Priority 2 (High)
4. 🟡 **R201** | Priority 3 (Medium)

### Clicking "DISPATCH NEXT" Sequentially:
- **1st Click**: Dispatches **R202** (Critical, earliest)
- **2nd Click**: Dispatches **R204** (Critical, second)
- **3rd Click**: Dispatches **R203** (High)
- **4th Click**: Dispatches **R201** (Medium)

*Notice: Even though R201 arrived first in chronological time, it was correctly dispatched LAST because its urgency was lower.*

---

## 11. Explanation of the 4 Dashboard Charts

Navigate to **Analytics & Charts** (`/analytics`) to view live visualizations:

1. **Emergency Requests by Type (Bar Chart)**:
   - **Data Source**: `SELECT emergency_type, COUNT(*) FROM emergency_requests GROUP BY emergency_type;`
   - **Insight**: Identifies whether Accidents, Fires, or Medical emergencies dominate dispatch load, assisting in resource allocation (e.g., fire trucks vs ambulances).

2. **Priority Distribution (Doughnut Chart)**:
   - **Data Source**: `SELECT priority, COUNT(*) FROM emergency_requests GROUP BY priority;`
   - **Insight**: Displays the ratio of Critical (P1) to Low (P4) cases. Shows why priority dispatching is vital—allowing critical slices to bypass lower categories.

3. **Requests by Hour of the Day (Line Chart)**:
   - **Data Source**: `SELECT HOUR(request_time), COUNT(*) FROM emergency_requests GROUP BY HOUR(request_time);`
   - **Insight**: Visualizes diurnal emergency volume curves to detect peak call windows.

4. **Average Response Time by Priority (Bar Chart)**:
   - **Data Source**: `SELECT priority, AVG(response_time) FROM emergency_requests GROUP BY priority;`
   - **Insight**: **Academic validation graph**. Proves that Critical (P1) cases achieve the lowest response times, while Low (P4) cases wait longer without compromising human safety.

---

## 12. Academic Defense & Viva Q&A Guide

**Q1: What is the main thesis of RapidReq?**
> *"Multiple emergency requests can arrive at the same time, but they have different urgency levels. Processing them only in arrival order may delay critical cases. Therefore, RapidReq uses a Priority Queue to process the most urgent emergency request first. The system manages emergency requests and dispatch records through a web application and visualizes the generated data through an analytics dashboard."*

**Q2: How do you handle emergencies with the same priority?**
> *"We maintain a sequence counter `arrival_order` upon each enqueue. When two emergencies share identical priority numbers, our Priority Queue compares their sequence counters to enforce strict FIFO ordering. This prevents starvation among equal-priority incidents."*

**Q3: How does the in-memory Priority Queue synchronize with MySQL?**
> *"Upon submission, the request is written to MySQL with status 'Pending' and immediately enqueued into the Priority Queue. When the Flask server starts, `sync_priority_queue_with_db()` loads all pending MySQL records in chronological order (`ORDER BY request_time ASC`), ensuring the in-memory queue accurately mirrors persistent storage."*

**Q4: How is Response Time computed?**
> *$$\text{Response Time} = \text{dispatch\_time} - \text{request\_time}$$*
> *Calculated in seconds when the dispatcher triggers `dispatch_next()`, and stored in MySQL to feed real-time Chart.js telemetry.*
