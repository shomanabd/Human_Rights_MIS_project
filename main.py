from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers.cases import case_router
from routers.reports import report_router
from routers.analytics import analytics_router


app = FastAPI(
    title="Human Rights MIS",
    description="Document, manage, and analyze human rights violations.",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(case_router, prefix="/cases", tags=["Case Management"])
app.include_router(report_router, prefix="/reports", tags=["Incident Reporting"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])

app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get("/")
def read_root():
    return {"message": "Human Rights MIS API is active"}
