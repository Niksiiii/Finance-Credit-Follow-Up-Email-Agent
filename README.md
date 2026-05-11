# CredFlow AI - Finance Credit Follow-Up Email Agent

## 📖 Description
CredFlow AI is an intelligent, AI-powered system that automatically generates and sends follow-up emails for overdue invoice payments. It features a sophisticated 5-stage tone escalation mechanism based on the number of days an invoice is overdue, ensuring communication remains professional, firm, and legally compliant. The application provides a complete audit trail, payment tracking, team management, and automation scheduling. It leverages LangChain and Google Gemini for context-aware email generation and Streamlit for an interactive, banking-styled dashboard.

## ✨ Features
- **AI Email Generation:** Uses LLM (Google Gemini) to draft highly personalized follow-up and thank-you emails based on dynamic data.
- **5-Stage Tone Escalation:** Automatically escalates email tone: Warm → Polite → Formal → Stern → Escalation Flag (for manual review).
- **Payment Tracking:** Records full and partial payments, automatically calculating balances and sending appropriate thank-you emails.
- **Full Audit Trail:** Logs every email generated, including stage, tone, send status, and timestamp for complete transparency.
- **Automation Scheduler:** Built-in background task scheduler to run follow-up scans automatically at configured intervals.
- **Dry-Run Mode:** Safe testing environment enabled by default to prevent accidental email dispatches during setup.
- **Data Ingestion:** Bulk import invoices effortlessly via CSV or Excel (`.xlsx`, `.xls`) file uploads.
- **Response Tracker:** Log client responses (e.g., Promise to Pay, Dispute) and assign them to specific finance team members.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Google Gemini API Key
- Gmail App Password (for SMTP sending)

### 1. Setup Environment
```bash
# Navigate to the project directory
cd TCI

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
pip install -r frontend/requirements.txt
```

### 2. Configuration
Copy the environment template and add your credentials:
```bash
cp .env.example .env
```
Update the `.env` file with your details:
```env
GOOGLE_API_KEY=your_google_api_key_here
LLM_MODEL=gemini-1.5-flash

# SMTP Configuration (Gmail recommended)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
SENDER_EMAIL=finance@yourcompany.com

# App settings
DRY_RUN_MODE=true
```

### 3. Start the Application

**Start the Backend (FastAPI):**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Start the Frontend (Streamlit):**
Open a new terminal window, activate the venv, and run:
```bash
cd frontend
streamlit run app.py
```

### 4. Access the App
- **Dashboard:** http://localhost:8501
- **API Documentation:** http://localhost:8000/docs
### Dashboard Overview

*Provides a high-level overview of total invoices, overdue amounts, recovery rates, and stage distributions.*

### Follow-Up Queue & Automation
*Review overdue invoices, start the automation scheduler, or manually trigger the AI agent.*

### Audit Logs & Full Email Preview
*Complete transparency into all communications sent by the agent, including tone, status, and full email body.*

### Team & Payment Tracking
*Record payments, track client responses, and manage your finance team roster.*

### Upload Invoices
*Easily drag and drop CSV or Excel files to import your pending credit records.*

## 🔒 Security & Privacy
- **Dry-Run Mode:** Enabled by default. In this mode, emails are generated and logged but NOT actually sent via SMTP.
- **Input Sanitization:** Protects against prompt injection and XSS by stripping HTML tags and filtering common injection phrases from user inputs.
- **PII Masking:** Email addresses and large currency amounts are masked in standard logs to protect sensitive client data.
- **Secrets Management:** API keys and SMTP credentials are read securely from the `.env` file and are never exposed in the source code.

## 🛠️ Tech Stack
- **AI/LLM:** Google Gemini via LangChain
- **Backend Framework:** FastAPI
- **Database:** SQLAlchemy ORM with SQLite
- **Frontend Framework:** Streamlit, Plotly
- **Data Processing:** Pandas, OpenPyXL
