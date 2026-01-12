# src/alerts/router.py
from fastapi import APIRouter, Depends
from src.auth.dependencies import get_current_user
from src.auth.models import User

router = APIRouter()

@router.get("/alerts")
async def get_my_alerts(
    current_user: User = Depends(get_current_user),  # ← This validates the token!
    db: AsyncSession = Depends(get_db)
):
    """
    Only authenticated users can access this.
    current_user is automatically populated from the JWT token.
    """
    # Get alerts for this specific user
    alerts = await alert_service.get_user_alerts(db, current_user.id)
    return alerts