# src/monitoring/scheduler.py
import asyncio
from typing import Optional
import structlog

from src.monitoring.price_monitor import price_monitor

logger = structlog.get_logger()


class MonitorScheduler:
    """Manages background monitoring tasks"""
    
    def __init__(self):
        self.monitor_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start all monitoring tasks"""
        if self.monitor_task is None or self.monitor_task.done():
            self.monitor_task = asyncio.create_task(price_monitor.start())
            logger.info("monitor_scheduler_started")
        else:
            logger.warning("monitor_scheduler_already_running")
    
    async def stop(self):
        """Stop all monitoring tasks"""
        if self.monitor_task and not self.monitor_task.done():
            await price_monitor.stop()
            
            # Wait for task to complete (max 5 seconds)
            try:
                await asyncio.wait_for(self.monitor_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("monitor_task_stop_timeout")
                self.monitor_task.cancel()
            
            logger.info("monitor_scheduler_stopped")


# Global scheduler instance
monitor_scheduler = MonitorScheduler()


# Convenience functions
async def start_scheduler():
    """Start the background monitoring scheduler"""
    await monitor_scheduler.start()


async def stop_scheduler():
    """Stop the background monitoring scheduler"""
    await monitor_scheduler.stop()