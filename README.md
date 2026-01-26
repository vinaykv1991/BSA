# AI Financial Planner & Expense Tracker

An automated financial memory and planning engine built with FastAPI. This application automatically extracts expenses from various sources (SMS, PDFs, CSVs), categorizes them using a hybrid AI approach, and provides real-time budgeting and "safe-to-spend" insights.

## 🚀 Key Features

- **Multi-Source Data Ingestion**:
    - **SMS Parsing**: Robust regex-based extraction from bank notification messages (e.g., HDFC, generic formats).
    - **PDF Statement Analysis**: Automated table extraction from bank PDF statements using `pdfplumber`.
    - **CSV Import**: Support for standard bank CSV exports.
- **Hybrid AI Categorization**:
    - Rule-based engine for high-speed, predictable categorization.
    - Modular design with placeholders for LLM-based fallback for unknown merchants.
    - Automatic distinction between **Earnings** and **Spendings**.
- **Dynamic Budgeting Engine**:
    - Real-time "Safe-to-Spend" calculations based on monthly income and spending velocity.
    - Category-wise budget tracking.
- **Privacy & Security**:
    - **Strict Data Isolation**: Every request is scoped to a specific `user_id`.
    - **Timezone Awareness**: All financial data is standardized to UTC.
- **Scalable Architecture**: Layered design (API, Services, Models, Schemas) for easy maintainability.

## 🛠 Tech Stack

- **Backend**: Python 3.12+, FastAPI
- **Database**: SQLAlchemy ORM (SQLite for dev, compatible with PostgreSQL)
- **PDF Processing**: `pdfplumber`
- **Validation**: Pydantic v2
- **Testing**: Pytest, ReportLab (for mock statement generation)
- **Deployment**: Uvicorn, Gunicorn, Docker

## 📂 Project Structure

```
.
├── app/
│   ├── api/            # FastAPI routes and dependency injection
│   ├── models/         # SQLAlchemy database models
│   ├── schemas/        # Pydantic models for validation
│   ├── services/       # Business logic (Normalization, Categorization, Budgeting)
│   ├── tests/          # Unit and integration tests
│   ├── main.py         # Application entry point
│   └── database.py     # DB connection and session management
├── requirements.txt    # Project dependencies
├── .gitignore          # Repository hygiene
└── README.md           # Documentation
```

## 💻 Local Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd ai-financial-planner
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`. You can access the interactive Swagger docs at `http://localhost:8000/docs`.

5. **Run Tests**:
   ```bash
   python -m pytest
   ```

## 📡 API Endpoints (Quick Reference)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/users` | Create a new user with monthly income. |
| `POST` | `/accounts` | Link a bank/credit card account to a user. |
| `POST` | `/ingest` | Ingest raw data (SMS text, CSV rows, or base64 PDF). |
| `GET` | `/users/{id}/transactions` | Retrieve user-specific categorized transactions. |
| `GET` | `/users/{id}/summary` | Get monthly spending breakdown by category. |
| `GET` | `/users/{id}/safe_to_spend` | Get real-time remaining budget for the month. |

## 🚢 Deployment Guide

### Option 1: Docker (Recommended)

1. **Create a `Dockerfile`**:
   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /code
   COPY ./requirements.txt /code/requirements.txt
   RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
   COPY ./app /code/app
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
   ```

2. **Build and Run**:
   ```bash
   docker build -t finance-app .
   docker run -d -p 80:80 finance-app
   ```

### Option 2: Production Server (Gunicorn)

For production, it's recommended to use Gunicorn with Uvicorn workers:
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### Database Persistence
In production, swap the `SQLALCHEMY_DATABASE_URL` in `app/database.py` to point to a managed PostgreSQL instance:
```python
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
```

## 🛣 Future Roadmap

- [ ] **Account Aggregator (AA) Integration**: Connect directly to bank APIs via Finvu/CAMS for real-time sync.
- [ ] **LLM Merchant Interpretation**: Integrate OpenAI/Anthropic for smart classification of obscure merchants.
- [ ] **Mobile App**: Flutter-based mobile dashboard.
- [ ] **Forecasting**: Predictive burn-rate analysis based on historical trends.
