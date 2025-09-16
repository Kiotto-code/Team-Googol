import threading
import time
from database import release_expired_claims
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaimCleanupScheduler:
    def __init__(self, interval_seconds=300):  # Default: 5 minutes
        self.interval_seconds = interval_seconds
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the background cleanup task."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.thread.start()
        logger.info("Started claim cleanup scheduler")
    
    def stop(self):
        """Stop the background cleanup task."""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Stopped claim cleanup scheduler")
    
    def _cleanup_loop(self):
        """Main loop for cleaning up expired claims."""
        while self.running:
            try:
                released_count = release_expired_claims()
                if released_count > 0:
                    logger.info(f"Released {released_count} expired claims")
            except Exception as e:
                logger.error(f"Error during claim cleanup: {e}")
            
            # Sleep for the specified interval
            time.sleep(self.interval_seconds)

# Global scheduler instance
scheduler = ClaimCleanupScheduler()

def start_cleanup_scheduler():
    """Start the cleanup scheduler."""
    scheduler.start()

def stop_cleanup_scheduler():
    """Stop the cleanup scheduler."""
    scheduler.stop()
