# Cost Optimization Recommendations
Generated: 2025-11-08 19:47:11

## Analysis Period: 7 days
Start: 2025-11-01
End: 2025-11-08

## Services Analyzed: 22

## Over-Provisioned Services: 22
- state-manager: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- ai-router: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- world-state: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- time-manager: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- language-system: CPU 0% avg (allocated: 512), Memory 0% avg (allocated: 1024)
- settings: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- model-management: CPU 0% avg (allocated: 512), Memory 0% avg (allocated: 1024)
- capability-registry: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- story-teller: CPU 0% avg (allocated: 512), Memory 0% avg (allocated: 1024)
- npc-behavior: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- weather-manager: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- quest-system: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- knowledge-base: CPU 0% avg (allocated: 1024), Memory 0% avg (allocated: 2048)
- payment: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- performance-mode: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- ai-integration: CPU 0% avg (allocated: 512), Memory 0% avg (allocated: 1024)
- ue-version-monitor: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- router: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- orchestration: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- event-bus: CPU 0% avg (allocated: 512), Memory 0% avg (allocated: 1024)
- environmental-narrative: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)
- storyteller: CPU 0% avg (allocated: 256), Memory 0% avg (allocated: 512)


## Under-Provisioned Services: 0
None found

## Estimated Savings:
- Right-sizing services: ~(                     .Count * 2)/mo
- Additional optimization opportunities to investigate:
  - Database right-sizing
  - VPC endpoints (eliminate data transfer costs)
  - Reserved capacity for baseline
  - Service consolidation for low-traffic services

## Action Items:
1. Review over-provisioned services
2. Test with reduced CPU/memory allocations in dev
3. Monitor for 48 hours after changes
4. Roll out to production if stable
