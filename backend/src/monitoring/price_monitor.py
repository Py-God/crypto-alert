# src/monitoring/price_monitor.py
import asyncio
from typing import Dict, Set, List
from datetime import datetime
from collections import defaultdict
import structlog

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import AsyncSessionLocal
from src.alerts.models import Alert, AlertStatus
from src.alerts.constants import AssetType
from src.market_data.client import market_data_client
from src.websocket.manager import manager
from src.monitoring.alert_checker import AlertChecker

logger = structlog.get_logger()


class PriceMonitor:
    """Background service to monitor prices and trigger alerts"""
    
    def __init__(self):
        self.running = False
        self.check_interval = 5  # seconds between price checks
        self.alert_checker = AlertChecker()
        
    async def start(self):
        """Start the price monitoring loop"""
        self.running = True
        logger.info("price_monitor_started", interval=self.check_interval)
        
        while self.running:
            try:
                await self._monitor_cycle()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error("price_monitor_error", error=str(e))
                await asyncio.sleep(10)  # Wait longer on error
    
    async def stop(self):
        """Stop the price monitoring loop"""
        self.running = False
        logger.info("price_monitor_stopped")
    
    async def _monitor_cycle(self):
        """One cycle of price monitoring"""
        async with AsyncSessionLocal() as session:
            # Get all active alerts
            active_alerts = await self._get_active_alerts(session)
            
            if not active_alerts:
                logger.debug("no_active_alerts")
                return
            
            # Group alerts by symbol and asset type
            symbol_groups = self._group_alerts_by_symbol(active_alerts)
            
            logger.info(
                "monitoring_cycle",
                total_alerts=len(active_alerts),
                unique_symbols=len(symbol_groups)
            )
            
            # Check each symbol
            for (symbol, asset_type), alerts in symbol_groups.items():
                try:
                    await self._check_symbol_alerts(session, symbol, asset_type, alerts)
                except Exception as e:
                    logger.error(
                        "symbol_check_error",
                        symbol=symbol,
                        error=str(e)
                    )
            
            await session.commit()
    
    async def _get_active_alerts(self, session: AsyncSession) -> List[Alert]:
        """Get all active alerts from database"""
        query = select(Alert).where(Alert.status == AlertStatus.ACTIVE)
        result = await session.execute(query)
        return result.scalars().all()
    
    def _group_alerts_by_symbol(
        self,
        alerts: List[Alert]
    ) -> Dict[tuple, List[Alert]]:
        """Group alerts by (symbol, asset_type)"""
        groups = defaultdict(list)
        
        for alert in alerts:
            key = (alert.symbol, alert.asset_type)
            groups[key].append(alert)
        
        return dict(groups)
    
    async def _check_symbol_alerts(
        self,
        session: AsyncSession,
        symbol: str,
        asset_type: AssetType,
        alerts: List[Alert]
    ):
        """Check all alerts for a specific symbol"""
        
        # Fetch current price
        try:
            current_price = await market_data_client.get_price(symbol, asset_type)
        except Exception as e:
            logger.error(
                "price_fetch_failed",
                symbol=symbol,
                error=str(e)
            )
            return
        
        logger.debug(
            "checking_symbol",
            symbol=symbol,
            price=current_price,
            alert_count=len(alerts)
        )
        
        # Broadcast price update to WebSocket watchers
        await manager.send_price_update(
            symbol=symbol,
            price=current_price,
            asset_type=asset_type.value
        )
        
        # Check each alert
        for alert in alerts:
            await self._check_alert(session, alert, current_price)
    
    async def _check_alert(
        self,
        session: AsyncSession,
        alert: Alert,
        current_price: float
    ):
        """Check if a single alert should be triggered"""
        
        # Check if alert should trigger
        should_trigger = self.alert_checker.should_trigger_alert(
            alert,
            current_price
        )
        
        if not should_trigger:
            return
        
        # Trigger the alert
        logger.info(
            "alert_triggered",
            alert_id=alert.id,
            symbol=alert.symbol,
            target=alert.target_price,
            current=current_price,
            user_id=alert.user_id
        )
        
        # Update alert status
        alert.status = AlertStatus.TRIGGERED
        alert.triggered_price = current_price
        alert.triggered_at = datetime.utcnow()
        
        # Generate message
        message = self.alert_checker.generate_trigger_message(alert, current_price)
        
        # Send notifications
        await self.alert_checker.notify_user(alert, current_price, message)
        
        # Refresh in session
        await session.flush()


# Global price monitor instance
price_monitor = PriceMonitor()