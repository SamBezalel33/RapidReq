"""
=============================================================================
RAPIDREQ - Priority-Based Emergency Request & Dispatch System
FLASK BACKEND APPLICATION (app.py)
=============================================================================
Academic Project: Master's / Bachelor's Data Structures Demonstration
Architecture:
  User / Dispatcher Web Interface
        ↓
  Flask Web Controller (app.py)
        ↓
  EmergencyPriorityQueue (priority_queue.py)  <--- Core DS Engine
        ↓
  MySQL Persistence & Analytics (database.py)
=============================================================================
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import database
from priority_queue import EmergencyPriorityQueue

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "rapidreq_secret_key_2026_priority_dispatch")

# Instantiate the global Emergency Priority Queue
priority_queue = EmergencyPriorityQueue()


def sync_priority_queue_with_db():
    """
    Synchronizes the in-memory Priority Queue with pending records from MySQL.
    Loaded in arrival order (request_time ASC) so that the Priority Queue inserts
    each item in its proper priority position while preserving FIFO tie-breaking.
    """
    try:
        pending_records = database.get_pending_requests()
        priority_queue.load_from_list(pending_records)
        print(f"[QUEUE SYNC] Priority Queue synchronized with {priority_queue.size()} pending emergency requests.")
    except Exception as e:
        print(f"[QUEUE SYNC ERROR] Could not sync with database: {e}")


# =============================================================================
# FLASK WEB ROUTES
# =============================================================================

@app.route("/")
def index():
    """
    Home page introducing RAPIDREQ, explaining why Priority Queues are essential
    over standard FIFO queues in emergency response, with quick navigation cards.
    """
    summary = database.get_dashboard_summary()
    queue_preview = priority_queue.view_queue()[:3]
    return render_template("index.html", summary=summary, queue_preview=queue_preview)


@app.route("/submit", methods=["GET", "POST"])
def submit_request():
    """
    User Emergency Request Submission:
    - GET: Renders modern emergency submission form with auto-suggested Request ID.
    - POST: Validates input, inserts to MySQL, and enqueues to EmergencyPriorityQueue.
    """
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()
        emergency_type = request.form.get("emergency_type", "").strip()
        description = request.form.get("description", "").strip()
        priority_raw = request.form.get("priority", "").strip()
        custom_id = request.form.get("request_id", "").strip()

        # Validation
        if not name or not phone or not location or not emergency_type or not priority_raw:
            flash("All required fields must be filled out before submitting.", "danger")
            return redirect(url_for("submit_request"))

        # Phone number validation (at least 7 digits)
        if len(phone) < 7 or not any(c.isdigit() for c in phone):
            flash("Please provide a valid emergency contact phone number.", "warning")
            return redirect(url_for("submit_request"))

        try:
            priority = int(priority_raw)
            if priority not in [1, 2, 3, 4]:
                raise ValueError("Priority must be between 1 and 4.")
        except ValueError:
            flash("Invalid priority level selected. Must be 1 (Critical) to 4 (Low).", "danger")
            return redirect(url_for("submit_request"))

        request_id = custom_id if custom_id else database.generate_next_request_id()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        req_payload = {
            "request_id": request_id,
            "name": name,
            "phone": phone,
            "location": location,
            "emergency_type": emergency_type,
            "description": description,
            "priority": priority,
            "request_time": current_time
        }

        # Step 1: Save to MySQL database
        try:
            database.insert_request(req_payload)
        except Exception as e:
            flash(f"Database error while saving request: {str(e)}", "danger")
            return redirect(url_for("submit_request"))

        # Step 2: Enqueue into the in-memory Priority Queue
        priority_queue.add_request(
            request_id=request_id,
            name=name,
            phone=phone,
            location=location,
            emergency_type=emergency_type,
            description=description,
            priority=priority,
            request_time=current_time
        )

        priority_labels = {1: "Critical", 2: "High", 3: "Medium", 4: "Low"}
        flash(
            f"Emergency Request {request_id} ({emergency_type}) successfully logged! "
            f"Priority: {priority} ({priority_labels.get(priority)}) — Placed in Priority Queue at position #{priority_queue.size()}.",
            "success"
        )
        return redirect(url_for("dashboard"))

    # GET Request: Generate next sequential ID for convenience
    suggested_id = database.generate_next_request_id()
    return render_template("submit.html", suggested_id=suggested_id)


@app.route("/dashboard")
def dashboard():
    """
    Dispatcher Dashboard:
    - Summary KPI cards (Total, Pending, Active/Dispatched, Completed, Avg Response Time).
    - Current Priority Queue visualization showing exact dispatch priority.
    - Top pending request clearly highlighted with "DISPATCH NEXT" action.
    """
    summary = database.get_dashboard_summary()
    current_queue = priority_queue.view_queue()
    next_up = priority_queue.get_next_request()
    return render_template(
        "dashboard.html",
        summary=summary,
        queue=current_queue,
        next_request=next_up.to_dict() if next_up else None,
        queue_size=priority_queue.size()
    )


@app.route("/dispatch", methods=["GET", "POST"])
def dispatch_next():
    """
    DISPATCH NEXT ACTION:
    The central data-structure operation:
    1. Pops the highest-priority request from the Priority Queue (`dequeue`).
    2. Records dispatch timestamp.
    3. Calculates response time (dispatch_time - request_time in seconds).
    4. Updates MySQL record to 'Dispatched'.
    5. Redirects back to Dashboard with a success alert.
    """
    if priority_queue.is_empty():
        flash("Cannot dispatch: Priority Queue is currently empty! No pending requests.", "warning")
        return redirect(url_for("dashboard"))

    # Dequeue highest-priority emergency
    dispatched_node = priority_queue.dispatch_next()

    # Calculate response time
    now = datetime.now()
    dispatch_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Parse request time to compute delta
    response_time_seconds = 0
    try:
        if isinstance(dispatched_node.request_time, str):
            req_dt = datetime.strptime(dispatched_node.request_time, "%Y-%m-%d %H:%M:%S")
        else:
            req_dt = dispatched_node.request_time
        response_time_seconds = max(1, int((now - req_dt).total_seconds()))
    except Exception:
        response_time_seconds = 60  # Default fallback if parsing discrepancy

    # Update database
    database.update_dispatch_status(
        request_id=dispatched_node.request_id,
        dispatch_time=dispatch_time_str,
        response_time=response_time_seconds
    )

    priority_labels = {1: "Critical", 2: "High", 3: "Medium", 4: "Low"}
    flash(
        f"🚑 Dispatched Request {dispatched_node.request_id} ({dispatched_node.emergency_type})! "
        f"Priority: {dispatched_node.priority} - {priority_labels.get(dispatched_node.priority)}. "
        f"Response Time: {response_time_seconds} seconds.",
        "success"
    )
    return redirect(url_for("dashboard"))


@app.route("/complete/<request_id>", methods=["GET", "POST"])
def complete_request(request_id):
    """
    Marks a dispatched or pending emergency request as Completed.
    Removes it from the waiting queue if it was pending.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    priority_queue.remove_by_id(request_id)
    database.update_complete_status(request_id, now)

    flash(f"Emergency {request_id} has been marked as Completed.", "info")
    return redirect(request.referrer or url_for("requests_page"))


@app.route("/requests")
def requests_page():
    """
    Emergency Requests Management Table:
    Displays all emergency requests with multi-parameter filtering:
    - Priority (1, 2, 3, 4)
    - Emergency Type (Accident, Medical Emergency, Fire, Rescue, Other)
    - Status (Pending, Dispatched, Completed)
    """
    priority_filter = request.args.get("priority", "")
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")

    records = database.get_all_requests(
        priority=priority_filter if priority_filter else None,
        emergency_type=type_filter if type_filter else None,
        status=status_filter if status_filter else None
    )

    return render_template(
        "requests.html",
        requests=records,
        current_priority=priority_filter,
        current_type=type_filter,
        current_status=status_filter
    )


@app.route("/request/<request_id>")
def request_details(request_id):
    """
    Displays comprehensive details of a single emergency request.
    """
    record = database.get_request_by_id(request_id)
    if not record:
        flash(f"Emergency request '{request_id}' not found.", "danger")
        return redirect(url_for("requests_page"))
    return render_template("request_details.html", req=record)


@app.route("/analytics")
def analytics_page():
    """
    Dedicated Analytics View displaying 4 Chart.js charts:
    1. Requests by Emergency Type (Bar chart)
    2. Priority Distribution (Doughnut chart)
    3. Requests by Hour of the Day (Line chart)
    4. Average Response Time by Priority (Bar chart)
    """
    summary = database.get_dashboard_summary()
    return render_template("analytics.html", summary=summary)


# =============================================================================
# JSON REST API ENDPOINTS (For Dynamic Chart.js and Live Updates)
# =============================================================================

@app.route("/api/dashboard")
def api_dashboard():
    """
    Returns dashboard statistics and Priority Queue state as JSON.
    Used by JavaScript to update the interface asynchronously.
    """
    summary = database.get_dashboard_summary()
    queue = priority_queue.view_queue()
    return jsonify({
        "summary": summary,
        "queue": queue,
        "queue_size": len(queue),
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/analytics")
def api_analytics():
    """
    Returns aggregated real MySQL data for Chart.js:
    - Requests by Type
    - Priority Distribution
    - Requests by Hour
    - Average Response Time by Priority
    """
    data = database.get_analytics_data()
    return jsonify(data)


@app.route("/api/queue")
def api_queue():
    """
    Returns the live Priority Queue contents.
    """
    return jsonify({
        "size": priority_queue.size(),
        "queue": priority_queue.view_queue()
    })


@app.route("/reset-demo-queue")
def reset_demo_queue():
    """
    Helper route for Viva/Lab Evaluation:
    Resets the database and seeds the exact test case from project specification:
    R201 -> Priority 3
    R202 -> Priority 1
    R203 -> Priority 2
    R204 -> Priority 1
    """
    # Reset table
    conn = database.get_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM emergency_requests WHERE request_id IN ('R201', 'R202', 'R203', 'R204');")
    conn.close()

    priority_queue.clear()

    # Insert test items in arrival sequence
    test_cases = [
        {"request_id": "R201", "name": "Divya", "phone": "9876543201", "location": "Velachery", "emergency_type": "Rescue", "description": "Flood assistance", "priority": 3},
        {"request_id": "R202", "name": "Arun", "phone": "9876543202", "location": "Anna Nagar", "emergency_type": "Accident", "description": "Car collision", "priority": 1},
        {"request_id": "R203", "name": "Priya", "phone": "9876543203", "location": "T Nagar", "emergency_type": "Medical Emergency", "description": "Chest pain", "priority": 2},
        {"request_id": "R204", "name": "Karthik", "phone": "9876543204", "location": "Guindy", "emergency_type": "Fire", "description": "Factory blaze", "priority": 1},
    ]

    for item in test_cases:
        item["request_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        database.insert_request(item)
        priority_queue.add_request(
            request_id=item["request_id"],
            name=item["name"],
            phone=item["phone"],
            location=item["location"],
            emergency_type=item["emergency_type"],
            description=item["description"],
            priority=item["priority"],
            request_time=item["request_time"]
        )

    flash("Demonstration dataset loaded (R201 [P3], R202 [P1], R203 [P2], R204 [P1]). Ready for Dispatch sequence testing!", "success")
    return redirect(url_for("dashboard"))


# =============================================================================
# APPLICATION STARTUP INITIALIZATION
# =============================================================================

# Ensure DB and queue are ready upon module import/startup
database.init_db()
sync_priority_queue_with_db()


if __name__ == "__main__":
    print("\n=======================================================")
    print(" 🚑 RAPIDREQ: Priority-Based Emergency Dispatch System ")
    print("    Running on: http://127.0.0.1:5000                   ")
    print("=======================================================\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
