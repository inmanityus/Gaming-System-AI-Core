# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""Health check system for Body Broker services"""
import asyncio
from typing import Dict, Any


async def check_all_systems() -> Dict[str, Any]:
    """Check health of all Body Broker systems."""
    results = {}
    
    # Check harvesting
    try:
        from services.harvesting.body_part_extraction import HarvestingSystem
        h = HarvestingSystem()
        results['harvesting'] = {'status': 'healthy', 'systems': 1}
    except Exception as e:
        results['harvesting'] = {'status': 'error', 'error': str(e)}
    
    # Check negotiation
    try:
        from services.negotiation.haggling_system import HagglingSystem
        n = HagglingSystem()
        results['negotiation'] = {'status': 'healthy', 'systems': 1}
    except Exception as e:
        results['negotiation'] = {'status': 'error', 'error': str(e)}
    
    # Check drug economy
    try:
        from services.drug_economy.dark_drugs_system import DarkDrugsSystem
        d = DarkDrugsSystem()
        results['drugs'] = {'status': 'healthy', 'drug_types': 8}
    except Exception as e:
        results['drugs'] = {'status': 'error', 'error': str(e)}
    
    # Check clients
    try:
        from services.clients.dark_families_system import DarkFamiliesSystem
        c = DarkFamiliesSystem()
        results['clients'] = {'status': 'healthy', 'families': 8}
    except Exception as e:
        results['clients'] = {'status': 'error', 'error': str(e)}
    
    # Check morality
    try:
        from services.morality.surgeon_butcher_system import SurgeonButcherSystem
        m = SurgeonButcherSystem()
        results['morality'] = {'status': 'healthy', 'paths': 3}
    except Exception as e:
        results['morality'] = {'status': 'error', 'error': str(e)}
    
    # Overall health
    all_healthy = all(r.get('status') == 'healthy' for r in results.values())
    
    return {
        'overall_status': 'healthy' if all_healthy else 'degraded',
        'systems': results,
        'total_systems': len(results)
    }

