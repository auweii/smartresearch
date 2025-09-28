# SmartResearch – Helps in finding relevant research papers, summarizes, and clusters accordingly

Quick Workflow 



Setup
1. Clone Repo
git clone https://github.com/maudit-4047/smartresearch.git
cd smartresearch

2. Backend (FastAPI)
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
uvicorn main:app --reload


API → http://127.0.0.1:8000

Docs → http://127.0.0.1:8000/docs

NLTK setup (run once):

import nltk
nltk.download('punkt')
nltk.download('stopwords')

3. Frontend (Next.js)
cd ../frontend/smartresearch-frontend
npm install
npm run dev


UI → http://localhost:3000

📂 Structure
smartresearch/
├── backend/
│   ├── main.py
│   ├── smartresearch_backend/   # api/, services/, libs/
│   ├── data/uploads/            # uploaded PDFs
│   └── requirements.txt
│
└── frontend/
    └── smartresearch-frontend/  # Next.js app

🔧 Quick Test (backend only)

Start a job with curl:

curl -X POST "http://127.0.0.1:8000/jobs/start" \
     -H "Content-Type: application/json" \
     -d '{"file_ids": ["demo1"], "use_abstractive": true}'


Check status:

curl http://127.0.0.1:8000/jobs/<job_id>/status


That’s all a dev needs to run both backend + frontend locally.
