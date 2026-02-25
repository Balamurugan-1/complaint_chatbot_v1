# Complaint Chatbot v1 (FastAPI + MySQL + Twilio WhatsApp)

This project is a FastAPI backend that receives WhatsApp messages from Twilio, extracts machine details, and registers complaints in MySQL.

## 1. Tech Stack

- Python 3.10+
- FastAPI
- Uvicorn
- SQLAlchemy
- MySQL (with PyMySQL driver)
- Twilio WhatsApp webhook

## 2. Project Structure

```text
complaint_chatbot_v1/
+- app/
¦  +- main.py            # FastAPI routes (Twilio webhook)
¦  +- models.py          # SQLAlchemy models
¦  +- database.py        # DB engine + session
¦  +- extractor.py       # message -> machine matching
¦  +- crud.py
¦  +- schemas.py
¦  +- state_manager.py
+- create_tables.py      # Creates DB tables from models
+- requirements.txt
```

## 3. Prerequisites

1. Install MySQL Server and make sure it is running.
2. Install Python 3.10 or newer.
3. (Optional but recommended) Install Git and use a virtual environment.

## 4. Database Setup (MySQL)

Open MySQL and run:

```sql
CREATE DATABASE internship_db;
```

If you want to use a separate DB user (recommended):

```sql
CREATE USER 'chatbot_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON internship_db.* TO 'chatbot_user'@'localhost';
FLUSH PRIVILEGES;
```

## 5. Python Environment Setup

From project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
```

Install dependencies (if `requirements.txt` is empty, install manually):

```powershell
pip install fastapi uvicorn sqlalchemy pymysql python-multipart
```

Optional: save installed versions:

```powershell
pip freeze > requirements.txt
```

## 6. Configure Database URL

`app/database.py` reads `DATABASE_URL` from environment.

PowerShell (current terminal only):

```powershell
$env:DATABASE_URL = "mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1/internship_db"
```

If you use the dedicated DB user:

```powershell
$env:DATABASE_URL = "mysql+pymysql://chatbot_user:your_password@127.0.0.1/internship_db"
```

## 7. Create Tables

Run:

```powershell
python create_tables.py
```

This creates tables defined in `app/models.py`:

- `complaint`
- `conversation_state`
- `resources`
- `lab_incharge`

## 8. Seed Initial Resource Data

The webhook needs machine records in `resources` to match user messages.

Example SQL:

```sql
USE internship_db;

INSERT INTO resources (name, location, activation_status)
VALUES
('CNC Machine', 101, 'active'),
('Lathe Machine', 102, 'active'),
('Drill Press', 103, 'active');
```

## 9. Run the FastAPI Server

From project root:

```powershell
uvicorn app.main:app --reload
```

Server will start at:

- `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

## 10. Test API Locally

Check seeded machines:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/test-machines" -Method Get
```

## 11. Connect Twilio WhatsApp Webhook

1. Start your API locally.
2. Expose local server publicly using ngrok:

```powershell
ngrok http 8000
```

3. Copy HTTPS forwarding URL from ngrok.
4. In Twilio Console, set WhatsApp incoming webhook to:

```text
https://<your-ngrok-domain>/webhook/twilio
```

5. Send a WhatsApp message to your Twilio sandbox number.

## 12. Expected Conversation Flow

1. User sends message containing machine name.
2. Bot matches machine from `resources` table.
3. Bot asks for issue type (`hardware` / `process` / `electrical`).
4. User sends type.
5. Complaint is inserted into `complaint` table.
6. User receives success reply.

## 13. Troubleshooting

- `ModuleNotFoundError` or import issues:
  - Run command from project root (`complaint_chatbot_v1`) and use `uvicorn app.main:app --reload`.

- DB connection error:
  - Verify MySQL is running.
  - Verify `DATABASE_URL` username/password/db name.

- `Please provide the correct machine name.` always appears:
  - Ensure `resources` table has data.
  - Use a message containing machine keywords.

- Twilio webhook not hitting local API:
  - Ensure ngrok is running.
  - Ensure Twilio webhook URL is HTTPS and ends with `/webhook/twilio`.

## 14. Next Improvements (Recommended)

- Move secrets to a `.env` file and load via `python-dotenv`.
- Add Alembic migrations instead of only `create_tables.py`.
- Add request/response schemas and validation in `schemas.py`.
- Add tests for webhook flow and extractor logic.
