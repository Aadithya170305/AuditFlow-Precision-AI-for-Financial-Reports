# AuditFlow – Precision AI for Financial Reports

AuditFlow is a project I built to make financial reports easier to understand.
Instead of going through hundreds of pages of PDFs, the idea is simple: upload a document and ask questions about it like you would ask a person.

---

## What this project does

Financial reports are usually long, dense, and time-consuming to read.
With AuditFlow, you can:

* Upload a financial PDF
* Extract useful information from it
* Ask questions in plain English
* Get quick, relevant answers

The goal is to turn static financial documents into something interactive and actually useful.

---

## Features

* Upload and process financial PDFs
* Extract and structure important data
* Ask questions and get AI-based responses
* Fast backend built using FastAPI

---

## Project Structure

```
Backend/
│── app/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   ├── models/
│
│── data/          # ignored (stores uploaded PDFs)
│── .env           # ignored (API keys, secrets)
│── requirements.txt
│── .gitignore
│── README.md
```

---

## Tech Stack

* FastAPI (Backend framework)
* Python
* AI / LLM-based processing
* PDF parsing tools

---

## How to run the project

### 1. Clone the repo

```
git clone https://github.com/Aadithya170305/AuditFlow-Precision-AI-for-Financial-Reports.git
cd Backend
```

---

### 2. Create a virtual environment

```
python -m venv .venv
.venv\Scripts\activate
```

---

### 3. Install dependencies

```
pip install -r requirements.txt
```

---

### 4. Add environment variables

Create a `.env` file:

```
OPENAI_API_KEY=your_api_key
DB_URL=your_database_url
```

---

### 5. Run the server

```
uvicorn app.main:app --reload
```

---

## A few things I kept in mind

* Sensitive data (like API keys) is not pushed to GitHub
* Uploaded files are ignored using `.gitignore`
* The structure is kept simple so it’s easy to extend later

---

## Future improvements

Some things I’d like to add next:

* Better financial insights and visualizations
* User authentication
* Cloud deployment
* More accurate and context-aware AI responses

---
