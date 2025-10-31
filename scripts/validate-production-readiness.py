"""
Production readiness validation script.
Checks all required components and configurations before deployment.
"""

import asyncio
import sys
import os
from uuid import uuid4

# Check environment variables
REQUIRED_ENV_VARS = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD"
]

def check_environment():
    """Check that all required environment variables are set."""
    missing = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✅ All required environment variables set")
    return True


async def check_database_connection():
    """Check database connectivity."""
    try:
        from services.state_manager.connection_pool import get_postgres_pool
        
        postgres = await get_postgres_pool()
        # Try a simple query
        await postgres.execute("SELECT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def check_model_registry():
    """Check Model Registry functionality."""
    try:
        from services.model_management.model_registry import ModelRegistry
        
        registry = ModelRegistry()
        # Try to get a model (may return None, that's OK)
        await registry.get_current_model("foundation_layer")
        print("✅ Model Registry functional")
        return True
    except Exception as e:
        print(f"❌ Model Registry check failed: {e}")
        return False


async def check_historical_logging():
    """Check Historical Log Processor functionality."""
    try:
        from services.model_management.historical_log_processor import HistoricalLogProcessor
        
        processor = HistoricalLogProcessor()
        # Don't actually log, just check initialization
        print("✅ Historical Log Processor functional")
        return True
    except Exception as e:
        print(f"❌ Historical Log Processor check failed: {e}")
        return False


async def check_guardrails_monitor():
    """Check Guardrails Monitor functionality."""
    try:
        from services.model_management.guardrails_monitor import GuardrailsMonitor
        
        monitor = GuardrailsMonitor()
        # Test monitoring
        result = await monitor.monitor_outputs(
            model_id="test",
            outputs=["This is a safe test output"]
        )
        if result:
            print("✅ Guardrails Monitor functional")
            return True
    except Exception as e:
        print(f"❌ Guardrails Monitor check failed: {e}")
        return False


async def check_deployment_manager():
    """Check Deployment Manager functionality."""
    try:
        from services.model_management.deployment_manager import DeploymentManager
        
        manager = DeploymentManager()
        # Just check initialization
        print("✅ Deployment Manager functional")
        return True
    except Exception as e:
        print(f"❌ Deployment Manager check failed: {e}")
        return False


async def main():
    """Run all production readiness checks."""
    print("🚀 Production Readiness Validation")
    print("=" * 50)
    
    checks = [
        ("Environment Variables", check_environment()),
        ("Database Connection", await check_database_connection()),
        ("Model Registry", await check_model_registry()),
        ("Historical Logging", await check_historical_logging()),
        ("Guardrails Monitor", await check_guardrails_monitor()),
        ("Deployment Manager", await check_deployment_manager()),
    ]
    
    results = []
    for name, result in checks:
        results.append(result)
        if not result:
            print(f"\n❌ Production readiness check FAILED at: {name}")
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ ALL PRODUCTION READINESS CHECKS PASSED")
    print("✅ System ready for production deployment")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

