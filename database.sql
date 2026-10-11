-- =============================================================================
-- RAPIDREQ - Priority-Based Emergency Request & Dispatch System
-- Database Setup Script (MySQL / MariaDB)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS rapidreq;
USE rapidreq;

-- Drop table if exists for clean reset
DROP TABLE IF EXISTS emergency_requests;

-- Create Emergency Requests Table
CREATE TABLE emergency_requests (
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
    response_time INT DEFAULT NULL COMMENT 'Response time in seconds (dispatch_time - request_time)',
    status ENUM('Pending', 'Dispatched', 'Completed') NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Sample Emergency Records (At least 10 realistic entries for academic demonstration)
-- Realistic timestamps across different hours and priorities for Chart.js analytics
-- =============================================================================

INSERT INTO emergency_requests 
(request_id, name, phone, location, emergency_type, description, priority, request_time, dispatch_time, completion_time, response_time, status)
VALUES
-- Completed critical emergencies (Quick response times: 180s - 300s)
('R101', 'Arun Kumar', '9876543210', 'Anna Nagar, Chennai', 'Accident', 'Multi-car collision on 2nd Avenue, two passengers injured.', 1, '2026-10-08 08:15:00', '2026-10-08 08:18:00', '2026-10-08 08:45:00', 180, 'Completed'),
('R102', 'Priya Raman', '9876543211', 'T Nagar, Chennai', 'Medical Emergency', 'Elderly patient with acute chest pain and shortness of breath.', 2, '2026-10-08 08:30:00', '2026-10-08 08:36:00', '2026-10-08 09:10:00', 360, 'Completed'),
('R103', 'Karthik Raja', '9876543212', 'Guindy, Chennai', 'Fire', 'Electrical short circuit fire on 3rd floor commercial unit.', 1, '2026-10-08 09:05:00', '2026-10-08 09:08:30', '2026-10-08 09:50:00', 210, 'Completed'),
('R104', 'Divya Sundar', '9876543213', 'Velachery, Chennai', 'Rescue', 'Street flooding, elderly family stranded in ground floor home.', 3, '2026-10-08 09:20:00', '2026-10-08 09:32:00', '2026-10-08 10:25:00', 720, 'Completed'),
('R105', 'Rahul Sharma', '9876543214', 'Adyar, Chennai', 'Accident', 'Motorcycle skid on wet flyover, bleeding head injury.', 1, '2026-10-08 10:10:00', '2026-10-08 10:13:40', '2026-10-08 10:48:00', 220, 'Completed'),

-- Dispatched (Currently active in transit)
('R106', 'Meena Krishnan', '9876543215', 'Mylapore, Chennai', 'Other', 'Fallen tree blocking ambulance route near Kapaleeshwarar Temple.', 4, '2026-10-08 10:45:00', '2026-10-08 11:05:00', NULL, 1200, 'Dispatched'),
('R107', 'Suresh Babu', '9876543216', 'Tambaram, Chennai', 'Medical Emergency', 'Severe allergic reaction anaphylaxis in residential colony.', 2, '2026-10-08 11:15:00', '2026-10-08 11:22:00', NULL, 420, 'Dispatched'),

-- Pending Requests (Currently waiting in the Priority Queue)
('R108', 'Lakshmi Narayanan', '9876543217', 'Koyambedu, Chennai', 'Fire', 'Warehouse godown fire spreading near market entrance.', 1, '2026-10-08 11:35:00', NULL, NULL, NULL, 'Pending'),
('R109', 'Anand Kumar', '9876543218', 'Nungambakkam, Chennai', 'Accident', 'Bicycle collided with delivery truck, fractured leg.', 2, '2026-10-08 11:40:00', NULL, NULL, NULL, 'Pending'),
('R110', 'Bhavani Devi', '9876543219', 'Porur, Chennai', 'Rescue', 'Cat stuck on high-tension wire pole, crowd gathering.', 4, '2026-10-08 11:42:00', NULL, NULL, NULL, 'Pending'),
('R111', 'Venkatesh Rao', '9876543220', 'Chromepet, Chennai', 'Medical Emergency', 'Diabetic collapse and unconsciousness at bus terminal.', 1, '2026-10-08 11:45:00', NULL, NULL, NULL, 'Pending'),
('R112', 'Saravanan M', '9876543221', 'Thiruvanmiyur, Chennai', 'Rescue', 'Boat engine failure with 3 fishermen near beach line.', 3, '2026-10-08 11:50:00', NULL, NULL, NULL, 'Pending');
