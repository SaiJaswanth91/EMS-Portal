# 🏢 Enterprise Employee & Leave Management System (EELMS)

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-success.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-45%2F45%20Passing-brightgreen.svg)]()

**EELMS** is a production-grade, secure, role-based Enterprise Employee & Leave Management System built with **Django 5.2**, **Django REST Framework**, **Bootstrap 5**, **Chart.js**, and **PostgreSQL/SQLite**. It delivers end-to-end corporate workflow automation for attendance tracking, leave applications, manager approvals, dynamic analytics, and employee master records.

---

## 🌟 Core Features & Capability Matrix

### 1. 📊 Dynamic Dashboard & Real-Time Analytics
- **Live Metric Cards**: Dynamically calculated counts for Total Active Employees, Active Departments, Present Today, and Pending Leaves.
- **Role-Aware Views**:
  - **Admin & HR**: Organization-wide metrics, overall attendance breakdown, and department distribution.
  - **Manager**: Team-level scoping displaying direct subordinates, team clock-in counts, and team pending approvals.
  - **Employee**: Personal clock-in status, today's working hours, leave balance matrix, and personal pending applications.
- **Interactive Visualizations (Chart.js)**:
  - *Chart 1*: Today's Attendance Breakdown (Doughnut Chart).
  - *Chart 2*: Active Employees per Department (Bar Chart).
  - *Chart 3*: 7-Day Attendance / Working Hours Trend (Line Chart).
  - *Empty State Protection*: Clean fallback messages and zero-count safeguards when no records exist.

### 2. 🔐 Role-Based Access Control (RBAC) & Security
- **4 System Roles**: `ADMIN`, `HR`, `MANAGER`, `EMPLOYEE`.
- **IDOR Protection**: Object-level permissions preventing unauthorized cross-tenant profile or leave data access.
- **Security Protections**: CSRF token validation, password complexity rules, session management, and `json_script` DOM serialization preventing XSS attacks.

### 3. 👥 Employee Management Module
- **Concurrency-Safe ID Generation**: Automatic generation of `EMP-{DEPT_CODE}-{SEQ:04d}` employee IDs using `select_for_update()` database row locking.
- **Corporate Details**: Department assignment, designation, reporting manager linking, employment status (`ACTIVE`, `ON_LEAVE`, `SUSPENDED`, `RESIGNED`, `TERMINATED`), profile photo validation, and emergency contact details.

### 4. ⏱️ Attendance Tracking System
- **Server-Validated Clock-In/Out**: Real-time timestamp recording preventing double clock-ins or clock-outs without clocking in first.
- **Automated Hours & Status Calculation**:
  - Grace period cutoff (shift start + 15 mins) for `LATE` status.
  - Working hours calculation (< 4.0 hrs automatically marked `HALF_DAY`).

### 5. 📅 Leave Application & Approval Engine
- **Atomic Approval Workflow**: Database row locking (`select_for_update()`) during approvals preventing race conditions in balance deductions.
- **Smart Validation**: Date range validation, overlapping request detection, active employment status checks, and insufficient leave balance protection.
- **Leave Balances & Policies**: Yearly leave quotas per leave type (Casual, Sick, Earned, Unpaid).

### 6. 🌐 OpenAPI & REST APIs
- Integrated **DRF Spectacular** OpenAPI 3.0 schema generation with interactive Swagger UI (`/api/docs/`) and Redoc UI (`/api/redoc/`).

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Language** | Python 3.10 |
| **Backend Framework** | Django 5.2 |
| **API Framework** | Django REST Framework (DRF) + drf-spectacular |
| **Frontend & UI** | HTML5, Vanilla CSS, Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4 |
| **Database** | PostgreSQL 16 (Production) / SQLite 3 (Development Fallback) |
| **Async Task Queue** | Celery 5.3 + Redis 7 |
| **Testing** | Pytest + pytest-django |
| **Containerization** | Docker & Docker Compose |

---

## 🔑 Demo Login Credentials

The login page at [`/accounts/login/`](http://127.0.0.1:8000/accounts/login/) features interactive single-click autofill buttons for testing:

| Role | Email | Password | Scope / Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@eelms.com` | `Admin@123` | Full System Administration & Global Overrides |
| **HR** | `hr@eelms.com` | `Hr@123` | Employee Management, Department Setup & Leave Policies |
| **Manager** | `manager1@eelms.com` | `Manager@123` | Team Attendance Monitoring & Direct Leave Approvals |
| **Employee** | `employee1@eelms.com` | `Employee@123` | Daily Clock-In/Out, Leave Applications & Profile |

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Git

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/SaiJaswanth91/EMS-Portal.git
cd EMS-Portal

# Create & activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements/development.txt
```

### 3. Run Database Migrations
```bash
python backend/manage.py migrate
```

### 4. Launch Development Server
```bash
python backend/manage.py runserver
```

Open your browser and navigate to:
- **Application Portal**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Dashboard**: [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
- **Swagger API Docs**: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🐳 Docker Deployment

To run the complete production stack (PostgreSQL, Redis, Django Web, Celery Worker, Celery Beat) via Docker Compose:

```bash
docker-compose up --build
```

---

## 🧪 Running Unit Tests

The repository contains a test suite covering accounts, attendance, departments, employees, leave approvals, RBAC, and dynamic dashboard metrics:

```bash
cd backend
python -m pytest
```

**Output:**
```text
============================= 45 passed in 35.71s =============================
```

---

## 📁 Project Directory Structure

```text
EMS-Portal/
├── .env.example              # Environment variables template
├── docker-compose.yml        # Docker compose configuration
├── pytest.ini                # Pytest configuration
├── README.md                 # Project Documentation
└── backend/
    ├── manage.py             # Django management entrypoint
    ├── config/               # Project configuration & settings
    │   ├── settings/         # Base, Development & Production settings
    │   ├── urls.py           # Main URL routing & Dashboard View
    │   ├── wsgi.py           # WSGI application entry point
    │   └── celery.py         # Celery task queue configuration
    ├── apps/                 # Modular Domain Applications
    │   ├── accounts/         # User model, Authentication, Roles & Mixins
    │   ├── employees/        # Employee profiles & ID generator
    │   ├── departments/      # Departments & Designations
    │   ├── attendance/       # Clock-in/out logic & status calculations
    │   ├── leaves/           # Leave requests, balances & atomic approvals
    │   ├── notifications/    # System notifications & email background tasks
    │   ├── documents/        # Employee document storage module
    │   ├── reports/          # Corporate reporting & analytics module
    │   └── audit/            # Security & audit logging module
    ├── templates/            # HTML5 Templates (Bootstrap 5)
    │   ├── base.html         # Base layout template
    │   ├── components/       # Reusable UI components (Navbar, Sidebar, Alerts)
    │   ├── dashboard/        # Dynamic Dashboard template (index.html)
    │   ├── accounts/         # User profile views
    │   ├── employees/        # Employee list, detail & form views
    │   ├── departments/      # Department management views
    │   ├── attendance/       # Attendance log & team status views
    │   ├── leaves/           # Leave application, list & approval views
    │   └── registration/     # Login & password reset forms
    ├── static/               # Static assets
    │   ├── css/              # Custom design system & styles
    │   └── js/               # Main JS & Chart.js dashboard integration
    └── tests/                # Pytest test suite (45 unit tests)
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
