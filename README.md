# 🏫 SchoolHub – Complete School Management System

A full‑stack, security‑focused school management platform built with Flask. SchoolHub centralizes student, staff, class, and results management for educational institutions, with role‑based access for admins, teachers, and students.

---

## 📖 About SchoolHub

SchoolHub is a complete, production‑ready school management system. It provides a clean web interface for administrators, teachers, and students to manage all school operations efficiently.

### Key Functionalities

- **User Management** – Role‑based accounts for Admin, DOS, Teacher, Class Teacher, and Student.
- **Student Management** – Register, update, and manage student profiles with class, combination, subject selection, and candidate status.
- **Staff Management** – Add and manage teachers and class teachers with assigned subjects and classes.
- **Results & Reports** – Record and store student results and reports.
- **Announcements** – Create and broadcast announcements to all users or targeted groups.
- **Alerts** – Send targeted alerts to individual students.
- **Authentication** – Secure JWT‑based login with Argon2id password hashing.
- **Rate Limiting** – Protection against brute‑force and abuse (100 requests per hour).
- **SQLite** – Lightweight database for development (easy to switch to PostgreSQL).
- **Responsive Design** – Optimized for desktop, tablet, and mobile.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Flask (Python 3.8+) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Database** | SQLite (development) / PostgreSQL (production) |
| **Authentication** | JWT (PyJWT) |
| **Password Hashing** | Argon2id (argon2-cffi) |
| **Rate Limiting** | Flask‑Limiter |
| **Hosting** | Render / PythonAnywhere |

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/Ravenj-png/raven-tech-system.git
cd raven-tech-system
