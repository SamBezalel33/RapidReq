# RAPIDREQ

Priority-based emergency request and dispatch system.

<div align="center">

[![Live Demo](https://img.shields.io/badge/Live-Demo-0ea5e9?style=for-the-badge)](https://rapidreq-three.vercel.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github)](https://github.com/SamBezalel33/RapidReq)

</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/MySQL-Database-4479A1?logo=mysql&logoColor=white" alt="MySQL" />
  <img src="https://img.shields.io/badge/Charts-Chart.js-FF6384?logo=chartdotjs&logoColor=white" alt="Chart.js" />
</p>

## Overview

RAPIDREQ is a smart emergency dispatch platform built around a custom priority queue. It ensures that critical incidents are handled first instead of waiting behind lower-priority requests just because they arrived earlier.

This project simulates a real dispatch control system where emergency requests are assigned urgency levels, stored in a database, visualized in a dashboard, and processed using priority-based logic.

## Live Demo

- Vercel App: https://rapidreq-three.vercel.app/
- GitHub Repository: https://github.com/SamBezalel33/RapidReq

## Why this project matters

In real emergency response, not all incidents are equal:

- Critical injuries must be prioritized over minor issues
- Standard FIFO queues delay life-saving decisions
- Priority-based dispatch improves safety and response efficiency

RAPIDREQ solves this by using a custom priority queue where:

- P1 = Critical
- P2 = High
- P3 = Medium
- P4 = Low

Higher urgency requests are dispatched first, while equal-priority requests still respect FIFO order.

## Key Features

- Custom emergency priority queue implementation
- Dispatcher dashboard for emergency management
- Request submission form for new incidents
- MySQL-backed data persistence
- Real-time analytics and charts
- Priority-based dispatch logic with tie-breaking
- Clean responsive admin UI

## Tech Stack

- Python
- Flask
- MySQL
- HTML/CSS/JavaScript
- Chart.js

## Project Structure

```text
Rapidreq/
├── app.py
├── database.py
├── database.sql
├── priority_queue.py
├── requirements.txt
├── README.md
├── templates/
│   ├── analytics.html
│   ├── base.html
│   ├── dashboard.html
│   ├── index.html
│   ├── request_details.html
│   ├── requests.html
│   └── submit.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── dashboard.js
```

## How it works

1. Emergency requests are submitted through the web app.
2. Each request is assigned a priority level.
3. Requests are inserted into a priority queue.
4. The dispatcher views the queue and selects the next case.
5. Highest-priority incidents are processed first.
6. Dispatch data is saved and charted for analytics.

## Run locally

```bash
git clone https://github.com/SamBezalel33/RapidReq.git
cd RapidReq
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Demo workflow

- Submit a new emergency request
- Assign a priority level
- Check the dispatch dashboard
- Observe the queue order
- Dispatch the next highest-priority case
- Review analytics and response trends

## Screenshots

The live app is available here:

https://rapidreq-three.vercel.app/

## Project goal

The goal of RAPIDREQ is to demonstrate how a priority queue can improve emergency dispatch decisions, reduce risk, and support faster, smarter response handling.

## License

This project is intended for academic and demonstration purposes.

---

Built for efficient emergency response and smarter dispatch decisions.
