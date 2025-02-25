"""
API route definitions for the Reading List Tracker.
"""
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from reading_list.database import models

router = APIRouter(prefix="/api/v1")

@router.get("/books", response_model=List[Dict])
async def get_books():
    """Get all books in the database."""
    return []  # TODO: Implement actual database query

@router.get("/readings", response_model=List[Dict])
async def get_readings():
    """Get all reading sessions."""
    return []  # TODO: Implement actual database query

@router.get("/inventory", response_model=List[Dict])
async def get_inventory():
    """Get complete inventory."""
    return []  # TODO: Implement actual database query