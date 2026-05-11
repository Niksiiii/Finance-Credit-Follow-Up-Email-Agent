"""
Automation Scheduler — Background thread that auto-runs the follow-up agent
at configurable intervals. Start/stop via API.
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional

from ..database import SessionLocal
from .agent import run_follow_up_agent

logger = logging.getLogger(__name__)


class FollowUpScheduler:
    """Thread-based scheduler for automated follow-up email dispatch."""

    def __init__(self):
        self._timer: Optional[threading.Timer] = None
        self._is_running: bool = False
        self._interval_hours: float = 24.0  # default: run daily
        self._dry_run: bool = True
        self._next_run: Optional[datetime] = None
        self._last_run: Optional[datetime] = None
        self._total_runs: int = 0
        self._lock = threading.Lock()
        self._last_result: Optional[dict] = None

    @property
    def status(self) -> dict:
        """Current scheduler status."""
        with self._lock:
            return {
                "is_running": self._is_running,
                "interval_hours": self._interval_hours,
                "dry_run": self._dry_run,
                "next_run": self._next_run.isoformat() if self._next_run else None,
                "last_run": self._last_run.isoformat() if self._last_run else None,
                "total_runs": self._total_runs,
                "last_result": self._last_result,
            }

    def start(self, interval_hours: float = 24.0, dry_run: bool = True):
        """Start the automation scheduler."""
        with self._lock:
            if self._is_running:
                logger.warning("Scheduler is already running")
                return

            self._interval_hours = interval_hours
            self._dry_run = dry_run
            self._is_running = True

        logger.info(f"🤖 Automation STARTED | Interval: {interval_hours}h | Dry-Run: {dry_run}")

        # Run immediately on first start, then schedule next
        self._execute_and_schedule()

    def stop(self):
        """Stop the automation scheduler."""
        with self._lock:
            self._is_running = False
            if self._timer:
                self._timer.cancel()
                self._timer = None
            self._next_run = None

        logger.info("🛑 Automation STOPPED")

    def _execute_and_schedule(self):
        """Execute one follow-up cycle, then schedule the next."""
        with self._lock:
            if not self._is_running:
                return

        # Run the agent
        try:
            db = SessionLocal()
            try:
                logger.info(f"⏰ Scheduled run #{self._total_runs + 1} starting...")
                result = run_follow_up_agent(db, dry_run=self._dry_run)

                with self._lock:
                    self._last_run = datetime.utcnow()
                    self._total_runs += 1
                    self._last_result = {
                        "run_number": self._total_runs,
                        "timestamp": self._last_run.isoformat(),
                        "total_processed": result["total_processed"],
                        "emails_sent": result["emails_sent"],
                        "emails_dry_run": result["emails_dry_run"],
                        "escalated": result["escalated_to_legal"],
                    }

                logger.info(f"⏰ Scheduled run #{self._total_runs} complete: "
                            f"{result['total_processed']} processed")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Scheduler execution error: {e}")

        # Schedule next run
        with self._lock:
            if self._is_running:
                interval_seconds = self._interval_hours * 3600
                self._next_run = datetime.utcnow() + timedelta(seconds=interval_seconds)
                self._timer = threading.Timer(interval_seconds, self._execute_and_schedule)
                self._timer.daemon = True
                self._timer.start()
                logger.info(f"📅 Next run scheduled at: {self._next_run.isoformat()}")


# Singleton instance
scheduler = FollowUpScheduler()
