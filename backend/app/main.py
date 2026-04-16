from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, close_mongo_connection
from app.routes import auth, upload, admin, verify, workspace, report
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Traceable Media Verification System")

# CORS Configuration – set FRONTEND_ORIGIN env var on Render
_origin_env = os.getenv("FRONTEND_ORIGIN", "")
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
if _origin_env:
    for _o in _origin_env.split(","):
        _o = _o.strip()
        if _o and _o not in origins:
            origins.append(_o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Connection Events
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Include Routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(verify.router, prefix="/api", tags=["Verification"])
app.include_router(workspace.router, prefix="/api/workspace", tags=["Workspace"])
app.include_router(report.router,    prefix="/api/report",    tags=["Report"])

@app.get("/")
async def root():
    return {"message": "Welcome to Traceable Media Verification System API"}


# cd backend 
# venv\Scripts\activate
# uvicorn app.main:app --reload