"""
Regional Dashboard Router
API endpoints for regional manager dashboard.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sqlite3

from aos.api.app import get_db
from aos.api.security import get_current_operator
from aos.core.aggregation import RegionalAggregator

router = APIRouter(prefix="/regional", tags=["regional"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/dashboard", response_class=HTMLResponse)
async def regional_dashboard(
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
    operator = Depends(get_current_operator)
):
    """Regional manager dashboard."""
    aggregator = RegionalAggregator(db)
    
    # Get summary stats
    summary = aggregator.get_village_summary()
    
    # Get aggregated data
    harvests = aggregator.aggregate_harvests(days=30)
    transport = aggregator.aggregate_transport(days=7)
    
    return templates.TemplateResponse("regional.html", {
        "request": request,
        "operator": operator,
        "summary": summary,
        "harvests": harvests,
        "transport": transport
    })

@router.get("/api/summary")
async def get_summary(
    db: sqlite3.Connection = Depends(get_db),
    operator = Depends(get_current_operator)
):
    """Get regional summary statistics."""
    aggregator = RegionalAggregator(db)
    return aggregator.get_village_summary()

@router.get("/api/harvests")
async def get_harvests(
    days: int = 30,
    db: sqlite3.Connection = Depends(get_db),
    operator = Depends(get_current_operator)
):
    """Get aggregated harvest data."""
    aggregator = RegionalAggregator(db)
    return aggregator.aggregate_harvests(days=days)

@router.get("/api/transport")
async def get_transport(
    days: int = 7,
    db: sqlite3.Connection = Depends(get_db),
    operator = Depends(get_current_operator)
):
    """Get aggregated transport data."""
    aggregator = RegionalAggregator(db)
    return aggregator.aggregate_transport(days=days)
