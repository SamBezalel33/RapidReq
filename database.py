"""
=============================================================================
RAPIDREQ - Priority-Based Emergency Request & Dispatch System
DATABASE ACCESS LAYER (MySQL / PyMySQL with Automatic Fallback & Recovery)
=============================================================================
Handles all database operations:
- Connection management to MySQL (with XAMPP defaults: root / empty password)
- Automatic detection and start of XAMPP MySQL if offline
- Seamless SQLite local fallback if MySQL is unavailable
- Automatic database and table initialization
- CRUD operations for emergency requests
- Aggregation queries for Chart.js real-time analytics
=============================================================================
"""

import os
import sys
import time
import subprocess
import sqlite3
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor

# MySQL Configuration (Configurable via environment variables)
DB_HOST = os.environ.get("MYSQL_HOST", "localhost")
DB_USER = os.environ.get("MYSQL_USER", "root")
DB_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
DB_NAME = os.environ.get("MYSQL_DB", "rapidreq")
DB_PORT = int(os.environ.get("MYSQL_PORT", 3306))
# On Vercel/Linux the app directory is read-only; use /tmp for SQLite
if os.name == "nt":
    SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapidreq.db")
else:
    SQLITE_DB_PATH = "/tmp/rapidreq.db"

# Global track of active engine: "mysql" or "sqlite"
CURRENT_ENGINE = "mysql"


def _try_start_xampp_mysql():
    """
    Attempts to start XAMPP MySQL if installed locally and not running.
    Only runs on Windows — skipped entirely on Vercel/Linux.
    """
    if os.name != "nt":
        return False  # Not Windows (e.g. Vercel Linux), skip XAMPP lookup
    xampp_candidates = [
        r"C:\xampp\mysql\bin\mysqld.exe",
        r"D:\xampp\mysql\bin\mysqld.exe"
    ]
    for exe in xampp_candidates:
        if os.path.exists(exe):
            ini = os.path.join(os.path.dirname(exe), "my.ini")
            try:
                flags = 0x08000000 | 0x00000008
                cmd = [exe, f"--defaults-file={ini}", "--standalone"] if os.path.exists(ini) else [exe, "--standalone"]
                subprocess.Popen(cmd, creationflags=flags)
                time.sleep(2.5)
                return True
            except Exception as e:
                print(f"[DB AUTO-START] Notice: Could not launch local mysqld: {e}")
    return False


# SQLite Compatibility Wrappers to provide identical DictCursor & %s syntax interface
class _SQLiteCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        clean_sql = sql.replace("%s", "?")
        if params is None:
            return self._cursor.execute(clean_sql)
        return self._cursor.execute(clean_sql, tuple(params))

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(r) for r in rows]

    def fetchone(self):
        row = self._cursor.fetchone()
        return dict(row) if row else None

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class _SQLiteConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _SQLiteCursorWrapper(self._conn.cursor())

    def close(self):
        try:
            self._conn.commit()
            self._conn.close()
        except Exception:
            pass


def _get_sqlite_connection():
    """Returns a wrapped SQLite connection with custom functions mimicking MySQL."""
    conn = sqlite3.connect(SQLITE_DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row

    def _sql_hour(val):
        if not val:
            return 0
        try:
            return datetime.strptime(str(val)[:19], "%Y-%m-%d %H:%M:%S").hour
        except Exception:
            return 0

    conn.create_function("HOUR", 1, _sql_hour)
    return _SQLiteConnectionWrapper(conn)


def get_connection(include_db=True, allow_auto_start=True):
    """
    Establishes and returns a database connection.
    Tries MySQL first. If MySQL is unreachable, tries launching XAMPP MySQL once.
    If MySQL remains unavailable, falls back to SQLite transparently.
    """
    global CURRENT_ENGINE

    # Try MySQL connection (connect_timeout=5 ensures fast fallback on Vercel)
    try:
        if include_db:
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT,
                cursorclass=DictCursor,
                autocommit=True,
                connect_timeout=5
            )
        else:
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT,
                cursorclass=DictCursor,
                autocommit=True,
                connect_timeout=5
            )
        CURRENT_ENGINE = "mysql"
        return conn
    except Exception as err:
        # If connection refused, try launching XAMPP mysqld once
        if allow_auto_start and _try_start_xampp_mysql():
            return get_connection(include_db=include_db, allow_auto_start=False)

        # Fallback to SQLite
        print(f"[DB INFO] MySQL not available ({err}). Operating seamlessly with SQLite fallback.")
        CURRENT_ENGINE = "sqlite"
        return _get_sqlite_connection()


def init_db():
    """
    Initializes the database and table if they do not already exist.
    Also seeds initial sample data if the table is empty.
    This guarantees zero manual setup hurdles for academic presentation.
    """
    global CURRENT_ENGINE

    # Initial probe
    conn = get_connection(include_db=False)

    if CURRENT_ENGINE == "mysql":
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()

            conn = get_connection(include_db=True)
            with conn.cursor() as cursor:
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS emergency_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    request_id VARCHAR(20) NOT NULL UNIQUE,
                    name VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    location VARCHAR(150) NOT NULL,
                    emergency_type VARCHAR(50) NOT NULL,
                    description TEXT,
                    priority INT NOT NULL COMMENT '1: Critical, 2: High, 3: Medium, 4: Low',
                    request_time DATETIME NOT NULL,
                    dispatch_time DATETIME DEFAULT NULL,
                    completion_time DATETIME DEFAULT NULL,
                    response_time INT DEFAULT NULL COMMENT 'Response time in seconds',
                    status ENUM('Pending', 'Dispatched', 'Completed') NOT NULL DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                cursor.execute(create_table_sql)
                _seed_initial_data_if_empty(cursor)
            conn.close()
            print("[DB INIT] MySQL database and table successfully initialized.")
            return True
        except Exception as e:
            print(f"[DB INIT ERROR] MySQL init failed ({e}), switching to SQLite...")
            CURRENT_ENGINE = "sqlite"

    # SQLite initialization
    try:
        conn = _get_sqlite_connection()
        with conn.cursor() as cursor:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS emergency_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id VARCHAR(20) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                location VARCHAR(150) NOT NULL,
                emergency_type VARCHAR(50) NOT NULL,
                description TEXT,
                priority INT NOT NULL,
                request_time DATETIME NOT NULL,
                dispatch_time DATETIME DEFAULT NULL,
                completion_time DATETIME DEFAULT NULL,
                response_time INT DEFAULT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_table_sql)
            _seed_initial_data_if_empty(cursor)
        conn.close()
        print("[DB INIT] SQLite database and table successfully initialized.")
        return True
    except Exception as e:
        print(f"[DB INIT ERROR] Could not initialize database: {e}")
        return False


def _seed_initial_data_if_empty(cursor):
    """Inserts initial emergency records if the table is currently empty."""
    cursor.execute("SELECT COUNT(*) AS count FROM emergency_requests;")
    row = cursor.fetchone()
    if row and row["count"] == 0:
        print("[DB INIT] Seeding initial sample emergency records...")
        sample_records = [
            ("R101", "Arun Kumar", "9876543210", "Anna Nagar, Chennai", "Accident", "Multi-car collision on 2nd Avenue, two passengers injured.", 1, "2026-10-08 08:15:00", "2026-10-08 08:18:00", "2026-10-08 08:45:00", 180, "Completed"),
            ("R102", "Priya Raman", "9876543211", "T Nagar, Chennai", "Medical Emergency", "Elderly patient with acute chest pain and shortness of breath.", 2, "2026-10-08 08:30:00", "2026-10-08 08:36:00", "2026-10-08 09:10:00", 360, "Completed"),
            ("R103", "Karthik Raja", "9876543212", "Guindy, Chennai", "Fire", "Electrical short circuit fire on 3rd floor commercial unit.", 1, "2026-10-08 09:05:00", "2026-10-08 09:08:30", "2026-10-08 09:50:00", 210, "Completed"),
            ("R104", "Divya Sundar", "9876543213", "Velachery, Chennai", "Rescue", "Street flooding, elderly family stranded in ground floor home.", 3, "2026-10-08 09:20:00", "2026-10-08 09:32:00", "2026-10-08 10:25:00", 720, "Completed"),
            ("R105", "Rahul Sharma", "9876543214", "Adyar, Chennai", "Accident", "Motorcycle skid on wet flyover, bleeding head injury.", 1, "2026-10-08 10:10:00", "2026-10-08 10:13:40", "2026-10-08 10:48:00", 220, "Completed"),
            ("R106", "Meena Krishnan", "9876543215", "Mylapore, Chennai", "Other", "Fallen tree blocking ambulance route near Kapaleeshwarar Temple.", 4, "2026-10-08 10:45:00", "2026-10-08 11:05:00", None, 1200, "Dispatched"),
            ("R107", "Suresh Babu", "9876543216", "Tambaram, Chennai", "Medical Emergency", "Severe allergic reaction anaphylaxis in residential colony.", 2, "2026-10-08 11:15:00", "2026-10-08 11:22:00", None, 420, "Dispatched"),
            ("R108", "Lakshmi Narayanan", "9876543217", "Koyambedu, Chennai", "Fire", "Warehouse godown fire spreading near market entrance.", 1, "2026-10-08 11:35:00", None, None, None, "Pending"),
            ("R109", "Anand Kumar", "9876543218", "Nungambakkam, Chennai", "Accident", "Bicycle collided with delivery truck, fractured leg.", 2, "2026-10-08 11:40:00", None, None, None, "Pending"),
            ("R110", "Bhavani Devi", "9876543219", "Porur, Chennai", "Rescue", "Cat stuck on high-tension wire pole, crowd gathering.", 4, "2026-10-08 11:42:00", None, None, None, "Pending"),
            ("R111", "Venkatesh Rao", "9876543220", "Chromepet, Chennai", "Medical Emergency", "Diabetic collapse and unconsciousness at bus terminal.", 1, "2026-10-08 11:45:00", None, None, None, "Pending"),
            ("R112", "Saravanan M", "9876543221", "Thiruvanmiyur, Chennai", "Rescue", "Boat engine failure with 3 fishermen near beach line.", 3, "2026-10-08 11:50:00", None, None, None, "Pending")
        ]
        sql = """
        INSERT INTO emergency_requests 
        (request_id, name, phone, location, emergency_type, description, priority, request_time, dispatch_time, completion_time, response_time, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        for rec in sample_records:
            cursor.execute(sql, rec)


def insert_request(data):
    """
    Inserts a newly submitted emergency request into the database.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO emergency_requests 
            (request_id, name, phone, location, emergency_type, description, priority, request_time, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Pending');
            """
            cursor.execute(sql, (
                data["request_id"],
                data["name"],
                data["phone"],
                data["location"],
                data["emergency_type"],
                data.get("description", ""),
                int(data["priority"]),
                data.get("request_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            ))
            return True
    finally:
        conn.close()


def get_pending_requests():
    """
    Fetches all pending requests ordered by request_time so the Priority Queue can
    load them in original arrival order.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM emergency_requests WHERE status = 'Pending' ORDER BY request_time ASC, id ASC;"
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()


def get_all_requests(priority=None, emergency_type=None, status=None):
    """
    Fetches all emergency requests with optional filters.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM emergency_requests WHERE 1=1"
            params = []

            if priority:
                sql += " AND priority = %s"
                params.append(int(priority))
            if emergency_type:
                sql += " AND emergency_type = %s"
                params.append(emergency_type)
            if status:
                sql += " AND status = %s"
                params.append(status)

            sql += " ORDER BY id DESC;"
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def get_request_by_id(request_id):
    """
    Retrieves complete details for a single request.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM emergency_requests WHERE request_id = %s;"
            cursor.execute(sql, (request_id,))
            return cursor.fetchone()
    finally:
        conn.close()


def update_dispatch_status(request_id, dispatch_time, response_time):
    """
    Updates the request to 'Dispatched', recording dispatch time and response time (in seconds).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            UPDATE emergency_requests 
            SET status = 'Dispatched', dispatch_time = %s, response_time = %s 
            WHERE request_id = %s;
            """
            cursor.execute(sql, (dispatch_time, response_time, request_id))
            return cursor.rowcount > 0
    finally:
        conn.close()


def update_complete_status(request_id, completion_time):
    """
    Marks an emergency as 'Completed'.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            UPDATE emergency_requests 
            SET status = 'Completed', completion_time = %s 
            WHERE request_id = %s;
            """
            cursor.execute(sql, (completion_time, request_id))
            return cursor.rowcount > 0
    finally:
        conn.close()


def get_dashboard_summary():
    """
    Computes high-level KPI card statistics:
    - Total Requests
    - Pending Requests
    - Dispatched (Active) Requests
    - Completed Requests
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'Dispatched' THEN 1 ELSE 0 END) AS dispatched,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed,
                AVG(CASE WHEN response_time IS NOT NULL THEN response_time ELSE NULL END) AS avg_response_time
            FROM emergency_requests;
            """
            cursor.execute(sql)
            row = cursor.fetchone()
            if not row:
                return {"total": 0, "pending": 0, "dispatched": 0, "completed": 0, "avg_response_time": 0.0}
            return {
                "total": int(row["total"] or 0),
                "pending": int(row["pending"] or 0),
                "dispatched": int(row["dispatched"] or 0),
                "completed": int(row["completed"] or 0),
                "avg_response_time": round(float(row["avg_response_time"] or 0), 1)
            }
    finally:
        conn.close()


def get_analytics_data():
    """
    Queries database to compile 4 specific datasets required for Chart.js:
    1. Emergency Requests by Type (Bar chart)
    2. Priority Distribution (Doughnut chart)
    3. Requests by Hour (Line chart)
    4. Average Response Time by Priority (Bar chart)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. By Emergency Type
            cursor.execute("""
                SELECT emergency_type, COUNT(*) as count 
                FROM emergency_requests 
                GROUP BY emergency_type 
                ORDER BY count DESC;
            """)
            by_type = cursor.fetchall()

            # 2. Priority Distribution
            cursor.execute("""
                SELECT priority, COUNT(*) as count 
                FROM emergency_requests 
                GROUP BY priority 
                ORDER BY priority ASC;
            """)
            by_priority_raw = cursor.fetchall()
            priority_labels_map = {1: "Critical (P1)", 2: "High (P2)", 3: "Medium (P3)", 4: "Low (P4)"}
            by_priority = [
                {
                    "priority": r["priority"],
                    "label": priority_labels_map.get(r["priority"], f"Priority {r['priority']}"),
                    "count": r["count"]
                }
                for r in by_priority_raw
            ]

            # 3. Requests by Hour (Grouped by hour of the day)
            cursor.execute("""
                SELECT HOUR(request_time) as hour, COUNT(*) as count 
                FROM emergency_requests 
                GROUP BY HOUR(request_time) 
                ORDER BY hour ASC;
            """)
            by_hour = cursor.fetchall()

            # 4. Average Response Time by Priority (in seconds / minutes)
            cursor.execute("""
                SELECT priority, ROUND(AVG(response_time), 1) as avg_response_sec
                FROM emergency_requests 
                WHERE response_time IS NOT NULL 
                GROUP BY priority 
                ORDER BY priority ASC;
            """)
            resp_by_priority_raw = cursor.fetchall()
            resp_by_priority = [
                {
                    "priority": r["priority"],
                    "label": priority_labels_map.get(r["priority"], f"Priority {r['priority']}"),
                    "avg_response_sec": float(r["avg_response_sec"] or 0)
                }
                for r in resp_by_priority_raw
            ]

            return {
                "by_type": by_type,
                "by_priority": by_priority,
                "by_hour": by_hour,
                "resp_by_priority": resp_by_priority
            }
    finally:
        conn.close()


def generate_next_request_id():
    """
    Generates a deterministic next Request ID like R113, R114, etc.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT request_id FROM emergency_requests ORDER BY id DESC LIMIT 1;")
            row = cursor.fetchone()
            if row and row["request_id"]:
                last_id = row["request_id"]
                if last_id.startswith("R") and last_id[1:].isdigit():
                    num = int(last_id[1:]) + 1
                    return f"R{num}"
            return f"R{int(datetime.now().timestamp()) % 10000}"
    except Exception:
        return f"R{int(datetime.now().timestamp()) % 10000}"
    finally:
        conn.close()
