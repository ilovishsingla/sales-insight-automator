## Sales Insight Automator

Sales Insight Automator is a full-stack prototype that lets a user upload a sales CSV/XLSX file and an email address, automatically analyze the dataset using Google Gemini, and send a professional executive summary via email using Resend.

The system is designed to be **cloud friendly**, **containerized**, and **production-ready** for deployment on **Render** (backend) and **Vercel** (frontend).

---

### Architecture Overview

- **Frontend**: React single page application (Vite)  
  - Handles file upload, email input, and displays status + preview of the AI-generated summary.
- **Backend**: FastAPI  
  - `/analyze` endpoint to parse sales data, call Gemini, and send email via Resend.
- **AI**: Google Gemini API  
  - Generates an executive-ready sales summary from the parsed sales table.
- **Email**: Resend API  
  - Sends the AI summary to the specified email address.
- **Infrastructure**:  
  - **Docker** image for the backend.  
  - **docker-compose** for local orchestration.  
  - **GitHub Actions** CI for linting and Docker build.

High-level flow:

1. User uploads `.csv` or `.xlsx` sales file and provides an email.
2. Backend validates file and email, parses the dataset using `pandas`.
3. Dataframe is converted into a compact markdown-style table string.
4. Google Gemini generates an executive sales report from the table.
5. Resend sends the report via email to the provided address.
6. The same summary is returned in the API response for UI preview.

---

### Folder Structure

```text
sales-insight-automator/
  backend/
    main.py
    requirements.txt
    utils/
      ai_summary.py
      email_service.py
      file_parser.py
  frontend/
    index.html
    vite.config.mts
    package.json
    src/
      App.jsx
      api.js
      main.jsx
  .github/
    workflows/
      ci.yml
  Dockerfile
  docker-compose.yml
  .env.example
  README.md
```

---

### Environment Variables

Copy `.env.example` to `.env` at the project root and set:

- **`GEMINI_API_KEY`**: Google Gemini API key.
- **`RESEND_API_KEY`**: Resend API key.
- **`RESEND_FROM_EMAIL`**: Verified sender address in Resend.
- **`BACKEND_URL`**: Base URL of the backend (e.g. `http://localhost:8000` for local dev, or your Render URL in production).

For Vercel, also expose the backend URL to the frontend as `VITE_BACKEND_URL` in the project settings (or `.env` in `frontend` when running locally). The frontend falls back to `BACKEND_URL` and then to `http://localhost:8000`.

---

### Backend: FastAPI

**Key file**: `backend/main.py`

- Exposes:
  - `POST /analyze` – core endpoint
  - `GET /health` – health check
  - `GET /` – simple root message + docs URL
- Automatic interactive docs are available at **`/docs`** (Swagger UI).

#### `/analyze` Endpoint

- **Method**: `POST`
- **Content type**: `multipart/form-data`
- **Fields**:
  - `file`: required, `.csv` or `.xlsx`, max 5MB
  - `email`: required, valid email format

**Behavior**:

1. **Security & validation**
   - Only `.csv` and `.xlsx` extensions allowed.
   - File size limited to **5MB**.
   - Email is validated with a simple regex.
   - Basic IP-based rate limiting: 20 requests per 60 seconds per IP.
2. **Parsing**
   - Uses `pandas` to parse CSV/Excel into a DataFrame.
   - Empty or unparseable files return a 400 error.
3. **AI Analysis**
   - Converts the DataFrame to a markdown-style table string.
   - Calls **Google Gemini** (`gemini-1.5-pro`) with a business-focused prompt:
     - revenue trends
     - top product category
     - regional performance
     - cancellations/anomalies
     - recommendations
4. **Email Delivery**
   - Uses **Resend** to send:
     - **Subject**: `Q1 Sales Insight Summary`
     - **Body**: formatted HTML including the AI summary.
5. **Response**
   - Returns JSON:

```json
{
  "email": "vp.sales@example.com",
  "summary": "<AI generated summary text>",
  "message": "Sales summary generated and emailed successfully."
}
```

Errors are returned with appropriate HTTP status codes and a `detail` field:

```json
{ "detail": "Invalid email address." }
```

---

### Frontend: React SPA

**Key files**:

- `frontend/src/App.jsx`
- `frontend/src/api.js`

Features:

- Clean, single-page UI.
- Inputs:
  - File upload (`.csv` / `.xlsx`).
  - Recipient email.
- UX:
  - Loading state with spinner while analysis runs.
  - Inline validation messages (missing file, invalid extension, etc.).
  - Success message when the summary is generated and email is sent.
  - Scrollable preview of the AI-generated summary.

The frontend calls:

- `POST {BACKEND_URL}/analyze`

via `axios` with a `FormData` payload.

---

### Local Development Setup

#### Prerequisites

- Python 3.11
- Node.js (LTS) + npm or yarn
- Docker (optional but recommended for parity with production)

#### 1. Clone and configure env

```bash
cd sales-insight-automator
cp .env.example .env
# Edit .env to add your real GEMINI_API_KEY, RESEND_API_KEY, RESEND_FROM_EMAIL
```

#### 2. Run backend locally (no Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/docs` to inspect and test the API.

#### 3. Run frontend locally

```bash
cd ../frontend
npm install
npm run dev
```

Vite will start the SPA (default `http://localhost:5173`).  
Ensure `BACKEND_URL` (and optionally `VITE_BACKEND_URL`) point to `http://localhost:8000`.

---

### Docker Setup

**Backend container only** (frontend is expected to be deployed via Vercel):

- **`Dockerfile`** (root)
  - Uses `python:3.11-slim`.
  - Installs backend dependencies from `backend/requirements.txt`.
  - Runs FastAPI via `uvicorn main:app --host 0.0.0.0 --port 8000`.

Build and run manually:

```bash
docker build -t sales-insight-automator-backend .
docker run --env-file .env -p 8000:8000 sales-insight-automator-backend
```

Or use **docker-compose**:

```bash
docker-compose up --build
```

The backend will be reachable at `http://localhost:8000`.

---

### CI/CD: GitHub Actions

Workflow file: `.github/workflows/ci.yml`

Runs on **pull requests to `main`**:

1. Checks out the repository.
2. Sets up Python 3.11.
3. Installs backend dependencies + `ruff`.
4. Runs `ruff check backend` for linting.
5. Builds the backend Docker image:

```bash
docker build -t sales-insight-automator-backend .
```

You can extend this pipeline with tests, security scans, or push the image to a registry.

---

### Security Measures

- **File validation**
  - Only `.csv` and `.xlsx` extensions allowed.
  - Maximum upload size: **5MB** (enforced server-side).
  - Basic parsing validation (empty or invalid files rejected).
- **Input validation**
  - Email is validated with a regex before processing.
- **Rate limiting**
  - Simple in-memory IP-based limiter: **20 requests / 60 seconds** per IP.
- **Error handling**
  - Centralized HTTP exception handler with structured JSON responses.
- **CORS**
  - Permissive CORS configured for SPA use; can be locked down for specific domains in production.

For true production, you’d typically place this behind HTTPS with API gateway / WAF and move rate limiting and auth to infrastructure or middleware level.

---

### Deployment Instructions

#### Backend → Render

1. Create a new **Web Service** in Render.
2. Connect your GitHub repository.
3. Set:
   - **Runtime**: Python 3.11 (or Docker if using the Dockerfile directly).
   - If using Python build:
     - **Build Command**: `pip install -r backend/requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 8000`
     - **Root Directory**: `backend`
   - If using Docker:
     - Point Render to the root `Dockerfile`.
4. Configure environment variables in Render dashboard:
   - `GEMINI_API_KEY`
   - `RESEND_API_KEY`
   - `RESEND_FROM_EMAIL`
5. Once deployed, note the public URL, e.g. `https://sales-insight-backend.onrender.com`.
6. Confirm Swagger docs are at: `https://...onrender.com/docs`.

#### Frontend → Vercel

1. From Vercel dashboard, **Import Project** from your GitHub repo.
2. Set **Framework Preset** to `Vite`.
3. Set:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Configure environment variables:
   - `VITE_BACKEND_URL` = your Render backend URL (e.g. `https://sales-insight-backend.onrender.com`)
5. Deploy. After deployment, hitting the Vercel URL should load the SPA and call your Render backend at `/analyze`.

---

### Testing with Sample Data

You can use the provided CSV for quick validation:

```csv
Date,Product_Category,Region,Units_Sold,Unit_Price,Revenue,Status
2026-01-05,Electronics,North,150,1200,180000,Shipped
2026-01-12,Home Appliances,South,45,450,20250,Shipped
2026-01-20,Electronics,East,80,1100,88000,Delivered
2026-02-15,Electronics,North,210,1250,262500,Delivered
2026-02-28,Home Appliances,North,60,400,24000,Cancelled
2026-03-10,Electronics,West,95,1150,109250,Shipped
```

Steps:

1. Save this as `sample_sales.csv`.
2. Run backend and frontend locally (or deploy).
3. Upload `sample_sales.csv` in the UI.
4. Enter a valid email address you control.
5. Submit and verify:
   - A success message in the UI.
   - An email arriving with subject **“Q1 Sales Insight Summary”**.
   - A meaningful, executive-style summary preview in the app.

---

### Next Steps / Extensions

This prototype is intentionally compact but can be extended with:

- Authentication and per-user history of analyses.
- More advanced anomaly detection or metrics in the Gemini prompt.
- Support for multiple time periods and automatic comparison.
- Integration with cloud storage (S3/GCS) for archived uploads.
- Observability (structured logging, metrics, tracing).

For now, Sales Insight Automator gives you a complete, deployable foundation: upload → analyze with LLM → email a polished sales summary. 

