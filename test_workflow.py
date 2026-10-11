"""
=============================================================================
RAPIDREQ - Academic Test Suite & Workflow Verification
=============================================================================
This script programmatically simulates the exact Viva demonstration:
1. Submits 4 emergency requests with mixed priorities:
     - R201 -> Priority 3 (Medium)
     - R202 -> Priority 1 (Critical)
     - R203 -> Priority 2 (High)
     - R204 -> Priority 1 (Critical)
2. Verifies the internal Priority Queue ordering.
3. Simulates clicking "Dispatch Next" 4 times through the Flask endpoint.
4. Verifies that the dispatch order strictly matches:
     Expected: R202 -> R204 -> R203 -> R201
5. Verifies MySQL database updates and API analytics responses.
=============================================================================
"""

import sys
import app
import database

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def run_verification_test():
    print("=" * 65)
    print(" 🚑 RAPIDREQ: ACADEMIC WORKFLOW VERIFICATION TEST")
    print("=" * 65)

    client = app.app.test_client()

    # Step 0: Clean any previous test entries
    conn = database.get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM emergency_requests WHERE request_id IN ('R201', 'R202', 'R203', 'R204');")
    conn.close()

    app.priority_queue.clear()

    # Step 1: Submit requests in specified arrival order
    print("\n[Step 1] Submitting 4 Emergencies in arrival sequence:")
    requests_to_submit = [
        {"request_id": "R201", "name": "Divya", "phone": "9876543201", "location": "Velachery, Chennai", "emergency_type": "Rescue", "description": "Flood water entered ground floor", "priority": "3"},
        {"request_id": "R202", "name": "Arun", "phone": "9876543202", "location": "Anna Nagar, Chennai", "emergency_type": "Accident", "description": "Critical car collision, head injury", "priority": "1"},
        {"request_id": "R203", "name": "Priya", "phone": "9876543203", "location": "T Nagar, Chennai", "emergency_type": "Medical Emergency", "description": "Severe cardiac pain", "priority": "2"},
        {"request_id": "R204", "name": "Karthik", "phone": "9876543204", "location": "Guindy, Chennai", "emergency_type": "Fire", "description": "Factory blaze outbreak", "priority": "1"}
    ]

    for req in requests_to_submit:
        resp = client.post("/submit", data=req, follow_redirects=True)
        assert resp.status_code == 200, f"Submission failed for {req['request_id']}"
        print(f"  ✓ Submitted {req['request_id']} | Type: {req['emergency_type']:<17} | Assigned Priority: {req['priority']}")

    # Step 2: Inspect In-Memory Priority Queue
    print("\n[Step 2] Inspecting Priority Queue Order in Memory:")
    current_q = app.priority_queue.view_queue()
    for idx, item in enumerate(current_q, 1):
        print(f"  Position #{idx}: {item['request_id']} (Priority {item['priority']} - {item['priority_label']}) [Seq: {item['arrival_order']}]")

    # Step 3: Sequentially dispatch through /dispatch route
    print("\n[Step 3] Dispatching via Flask '/dispatch' Endpoint:")
    actual_dispatch_order = []

    for click in range(1, 5):
        next_candidate = app.priority_queue.get_next_request()
        candidate_id = next_candidate.request_id if next_candidate else "EMPTY"
        resp = client.post("/dispatch", follow_redirects=True)
        assert resp.status_code == 200, "Dispatch route failed"
        actual_dispatch_order.append(candidate_id)
        print(f"  Click #{click} on 'DISPATCH NEXT' -> Dispatched: {candidate_id}")

    # Step 4: Validate Order Match
    expected_order = ["R202", "R204", "R203", "R201"]
    print("\n" + "-" * 65)
    print(f"  Actual Dispatch Order:   {actual_dispatch_order}")
    print(f"  Expected Dispatch Order: {expected_order}")
    print("-" * 65)

    assert actual_dispatch_order == expected_order, f"Order mismatch! Got {actual_dispatch_order}"
    print("  >>> SUCCESS: Priority Queue & Tie-Breaker match 100%! <<<")

    # Step 5: Check Database Persistence
    print("\n[Step 5] Checking MySQL Record Updates:")
    for rid in expected_order:
        rec = database.get_request_by_id(rid)
        assert rec is not None, f"Record {rid} missing from MySQL"
        assert rec["status"] == "Dispatched", f"Record {rid} status should be Dispatched, got {rec['status']}"
        print(f"  ✓ {rid} in MySQL: Status = {rec['status']} | Dispatch Time = {rec['dispatch_time']} | Response Time = {rec['response_time']}s")

    # Step 6: Verify Chart.js Analytics API
    print("\n[Step 6] Testing Chart.js Analytics API (/api/analytics):")
    api_resp = client.get("/api/analytics")
    assert api_resp.status_code == 200
    analytics_data = api_resp.get_json()
    print(f"  ✓ By Type: {len(analytics_data['by_type'])} categories returned")
    print(f"  ✓ Priority Distribution: {len(analytics_data['by_priority'])} priority levels returned")
    print(f"  ✓ Hourly Volume: {len(analytics_data['by_hour'])} active hours returned")
    print(f"  ✓ Avg Response Time: {len(analytics_data['resp_by_priority'])} priority categories returned")

    print("\n" + "=" * 65)
    print(" 🎉 ALL TESTS PASSED: RAPIDREQ SYSTEM IS 100% OPERATIONAL!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_verification_test()
