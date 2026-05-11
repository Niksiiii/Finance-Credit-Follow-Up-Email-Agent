"""
Finance Credit Follow-Up Email Agent — FastAPI Application Entry Point.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .api import invoices, followups, dashboard, team

# ── Logging Setup ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup/shutdown) ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise DB tables. Shutdown: cleanup."""
    logger.info("🚀 Starting Finance Credit Follow-Up Agent...")
    init_db()
    logger.info("✅ Database initialised")
    yield
    logger.info("👋 Shutting down...")


# ── FastAPI App ────────────────────────────────────────────
app = FastAPI(
    title="Finance Credit Follow-Up Email Agent",
    description=(
        "AI-powered agent that automatically generates and sends follow-up emails "
        "for overdue invoice payments. Escalates tone based on days overdue."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow Streamlit frontend) ────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Streamlit origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ──────────────────────────────────────
app.include_router(invoices.router)
app.include_router(followups.router)
app.include_router(dashboard.router)
app.include_router(team.router)


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Finance Credit Follow-Up Email Agent",
        "version": "1.0.0",
    }


@app.get("/api/config", tags=["Config"])
def get_config():
    """Get current agent configuration (safe fields only)."""
    from .config import get_settings
    s = get_settings()
    return {
        "dry_run_mode": s.DRY_RUN_MODE,
        "llm_model": s.LLM_MODEL,
        "payment_link_base": s.PAYMENT_LINK_BASE,
        "sender_email": s.SENDER_EMAIL,
    }
