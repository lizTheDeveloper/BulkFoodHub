#!/usr/bin/env python3
"""
Test script to verify database and Redis connections.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.database import test_db_connection, test_redis_connection, db_manager
from app.core.logging import get_logger

logger = get_logger(__name__)

def main():
    """Test database and Redis connections."""
    print("Testing BulkFoodHub Phase 1 Setup...")
    print("=" * 50)
    
    # Test database connection
    print("Testing PostgreSQL connection...")
    db_status = test_db_connection()
    if db_status:
        print("✅ PostgreSQL connection successful")
    else:
        print("❌ PostgreSQL connection failed")
        return False
    
    # Test Redis connection
    print("Testing Redis connection...")
    redis_status = test_redis_connection()
    if redis_status:
        print("✅ Redis connection successful")
    else:
        print("❌ Redis connection failed")
        return False
    
    # Test database manager health check
    print("Testing database manager health check...")
    health = db_manager.health_check()
    print(f"Health status: {health}")
    
    if health["overall"] == "healthy":
        print("✅ All systems healthy")
        return True
    else:
        print("❌ Some systems unhealthy")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Phase 1 setup completed successfully!")
        print("Database schema created, Redis running, logging configured.")
    else:
        print("\n❌ Phase 1 setup has issues that need to be resolved.")
        sys.exit(1)
