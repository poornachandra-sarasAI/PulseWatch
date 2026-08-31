"""PulseWatch HTTP API application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.monitors import router as monitors_router
from app.api.routes.results import router as results_router


app = FastAPI(
    title="PulseWatch API",
    version="0.1.0",
    description="Create and inspect HTTP uptime monitors.",
)

# Allow the local Next.js dev server and the Docker-composed frontend to call
# the API from the browser.  Wildcard origins are intentionally avoided.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Confirm that the API process is reachable."""

    return {"status": "ok"}


app.include_router(monitors_router)
app.include_router(results_router)
