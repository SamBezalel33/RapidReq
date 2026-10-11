"""
=============================================================================
RAPIDREQ - Priority-Based Emergency Request & Dispatch System
DATA STRUCTURE IMPLEMENTATION: Priority Queue with FIFO Tie-Breaking
=============================================================================

Academic Project: Data Structures Viva Demonstration
Core Concept:
  An Emergency Dispatch System cannot process requests purely on a First-Come,
  First-Served (FCFS) basis because a Critical accident (Priority 1) arriving
  at 10:05 AM must be treated before a Minor sprain (Priority 4) arriving at 10:00 AM.
  
  Therefore, RapidReq implements an explicit Priority Queue:
    - Priority 1 = Critical (Highest Urgency)
    - Priority 2 = High
    - Priority 3 = Medium
    - Priority 4 = Low (Lowest Urgency)
    
  Rule 1: Lower numerical priority value = Higher emergency urgency.
  Rule 2: For emergencies with IDENTICAL priority, preserve arrival order (FIFO).
          For example, if R202 (P1) arrives before R204 (P1), R202 is dispatched first.
=============================================================================
"""

from datetime import datetime


class EmergencyNode:
    """
    Represents an individual Emergency Request element within the Priority Queue.
    Stores the emergency payload, its priority rating, and an arrival sequence number
    used for deterministic FIFO tie-breaking.
    """
    def __init__(self, request_id, name, phone, location, emergency_type, description, priority, request_time=None, arrival_order=0):
        self.request_id = request_id
        self.name = name
        self.phone = phone
        self.location = location
        self.emergency_type = emergency_type
        self.description = description
        self.priority = int(priority)  # 1: Critical, 2: High, 3: Medium, 4: Low
        self.request_time = request_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.arrival_order = arrival_order  # Sequence counter for FIFO tie-breaker

    def to_dict(self):
        """Converts node data into a dictionary for JSON/template consumption."""
        priority_labels = {
            1: "Critical",
            2: "High",
            3: "Medium",
            4: "Low"
        }
        return {
            "request_id": self.request_id,
            "name": self.name,
            "phone": self.phone,
            "location": self.location,
            "emergency_type": self.emergency_type,
            "description": self.description,
            "priority": self.priority,
            "priority_label": priority_labels.get(self.priority, "Unknown"),
            "request_time": str(self.request_time),
            "arrival_order": self.arrival_order
        }

    def __repr__(self):
        return f"<EmergencyNode {self.request_id} | Priority {self.priority} | Seq {self.arrival_order}>"


class EmergencyPriorityQueue:
    """
    Custom Implementation of an Emergency Priority Queue.
    
    Data Structure Mechanism:
    - Internal storage: Python list `self.queue` maintained in sorted order.
    - Sorting criteria:
        Primary Key: `priority` (ASCENDING: 1 is top priority, 4 is lowest).
        Secondary Key: `arrival_order` (ASCENDING: earlier arrival gets processed first).
    - Dispatch operation: O(1) by removing from index 0 (`pop(0)`).
    - Enqueue operation: Insert into the correct position based on (priority, arrival_order).
    """

    def __init__(self):
        # The internal list storing EmergencyNode instances in sorted priority order
        self.queue = []
        # Monotonically increasing counter to preserve arrival sequence for FIFO tie-breaking
        self.sequence_counter = 0

    def is_empty(self):
        """
        Checks whether the priority queue is currently empty.
        Returns:
            bool: True if queue has 0 requests, False otherwise.
        """
        return len(self.queue) == 0

    def size(self):
        """
        Returns the total number of waiting requests in the queue.
        """
        return len(self.queue)

    def add_request(self, request_id, name, phone, location, emergency_type, description, priority, request_time=None):
        """
        Adds a new emergency request into the Priority Queue at its correct position.
        
        Algorithm (Priority Insertion):
        1. Increment the global arrival sequence counter.
        2. Create a new EmergencyNode with the request details and sequence number.
        3. Iterate through existing queue items:
           - Compare (new_node.priority) with (existing_node.priority).
           - Because lower number means higher priority:
             If new_node.priority < existing_node.priority:
                 Insert new_node BEFORE existing_node.
           - If priorities are equal:
             Since new_node arrived LATER than existing_node, new_node must come AFTER existing_node.
             We continue checking until we find an element with lower urgency (higher priority number).
        4. If no element with lower urgency is found, append to the very end.
        
        This guarantees:
        - Critical (P1) is always ahead of High (P2), Medium (P3), Low (P4).
        - Multiple P1 requests stay in exact arrival order (FIFO).
        """
        self.sequence_counter += 1
        new_node = EmergencyNode(
            request_id=request_id,
            name=name,
            phone=phone,
            location=location,
            emergency_type=emergency_type,
            description=description,
            priority=priority,
            request_time=request_time,
            arrival_order=self.sequence_counter
        )

        # If queue is empty, simply append the node
        if self.is_empty():
            self.queue.append(new_node)
            return new_node

        # Find the correct insertion point
        inserted = False
        for index, current_node in enumerate(self.queue):
            # If the new request has higher priority (smaller numerical value)
            if new_node.priority < current_node.priority:
                self.queue.insert(index, new_node)
                inserted = True
                break
            # If priority is identical, we do NOT insert before current_node,
            # because existing nodes arrived earlier (FIFO within same priority).

        # If not inserted yet, it belongs at the end of the queue
        if not inserted:
            self.queue.append(new_node)

        return new_node

    def get_next_request(self):
        """
        PEEK Operation:
        Inspects the next highest-priority emergency request WITHOUT removing it.
        Returns:
            EmergencyNode or None if queue is empty.
        """
        if self.is_empty():
            return None
        return self.queue[0]

    def dispatch_next(self):
        """
        DEQUEUE Operation:
        Removes and returns the highest-priority emergency request from the front.
        
        Returns:
            EmergencyNode or None if the queue is empty.
        """
        if self.is_empty():
            return None
        # Removes and returns the element at index 0 (Highest priority)
        dispatched_request = self.queue.pop(0)
        return dispatched_request

    def view_queue(self):
        """
        Returns all requests currently waiting in the Priority Queue as dictionaries.
        The returned list represents the exact order in which emergencies will be dispatched.
        """
        return [node.to_dict() for node in self.queue]

    def remove_by_id(self, request_id):
        """
        Removes a specific request from the waiting queue by its unique request_id
        (used if a request is cancelled or directly dispatched via individual action).
        """
        for index, node in enumerate(self.queue):
            if node.request_id == request_id:
                return self.queue.pop(index)
        return None

    def clear(self):
        """Clears all elements from the queue."""
        self.queue.clear()
        self.sequence_counter = 0

    def load_from_list(self, requests_list):
        """
        Populates the Priority Queue from an initial list of records (e.g. from MySQL).
        Preserves arrival ordering by processing in sequence.
        """
        self.clear()
        for req in requests_list:
            self.add_request(
                request_id=req["request_id"],
                name=req["name"],
                phone=req["phone"],
                location=req["location"],
                emergency_type=req["emergency_type"],
                description=req.get("description", ""),
                priority=req["priority"],
                request_time=req.get("request_time")
            )


# Self-test block when run standalone
if __name__ == "__main__":
    print("--- TESTING EMERGENCY PRIORITY QUEUE ---")
    pq = EmergencyPriorityQueue()
    
    # Test case from project specification:
    # R201 -> P3
    # R202 -> P1
    # R203 -> P2
    # R204 -> P1
    pq.add_request("R201", "Divya", "9876543210", "T Nagar", "Rescue", "Flood rescue", 3)
    pq.add_request("R202", "Arun", "9876543211", "Anna Nagar", "Accident", "Car crash", 1)
    pq.add_request("R203", "Priya", "9876543212", "Velachery", "Medical Emergency", "Cardiac arrest", 2)
    pq.add_request("R204", "Karthik", "9876543213", "Guindy", "Fire", "Factory fire", 1)
    
    print("\nCurrent Queue Order:")
    for pos, item in enumerate(pq.view_queue(), 1):
        print(f"  {pos}. {item['request_id']} | Priority {item['priority']} ({item['priority_label']}) | {item['emergency_type']}")
        
    print("\nDispatching sequentially:")
    while not pq.is_empty():
        dispatched = pq.dispatch_next()
        print(f"  Dispatched: {dispatched.request_id} (Priority {dispatched.priority})")
