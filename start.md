cd /Users/dasuncharuka/Documents/projects/llm/dcis/frontend
npm run dev




cd /Users/dasuncharuka/Documents/projects/llm/dcis
source backend/.venv/bin/activate
cd backend
uvicorn src.main:app --port 8008 --reload


cd /Users/dasuncharuka/Documents/projects/llm/dcis/backend
pkill -f "uvicorn src.main" 2>/dev/null
.venv314/bin/uvicorn src.main:app --port 8008 --reload
