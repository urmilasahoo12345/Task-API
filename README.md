# Task Management API (FastAPI)

A lightweight CRUD REST API built with Python, FastAPI, and SQLite for FlyRank BE-02.

---
## 💾 Database Architecture

* **Database Engine:** SQLite (Chosen because it requires zero server setup and stores data locally in a single lightweight file).
* **Storage Path:** `./tasks.db` (auto-generated in the project root on server startup).
  
---
## 🚀 How to Install & Run

### Prerequisites
* Python 3.10+
* Virtual environment (`.venv`) initialized

### Quickstart Command
Run the server locally with a single command:

```bash
uvicorn main:app --reload

```
Screenshots
<img width="1332" height="544" alt="curl -i" src="https://github.com/user-attachments/assets/a51e9755-135f-4d49-9145-0d234d79edb3" />
<img width="2812" height="1402" alt="swagger ui" src="https://github.com/user-attachments/assets/df2131de-c0b9-4674-a675-7d453ebdf389" />
<img width="2176" height="992" alt="tasks db ss" src="https://github.com/user-attachments/assets/82509497-dac8-4a00-b27a-20d1131a2c95" />
