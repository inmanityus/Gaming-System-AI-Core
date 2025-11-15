# Guardrails Monitor Service

The Guardrails Monitor provides real-time content moderation and safety enforcement for The Body Broker.

## Overview

This service integrates with:
- **Settings Service**: Receives content policy snapshots via NATS
- **Model Management**: Applies safety filters to AI model outputs
- **Ethelred Content Validator**: Coordinates content validation
- **Red Alert**: Reports critical violations

## Key Components

- **Policy Cache**: Maintains session content policies for fast lookups
- **Safety Filters**: Moderation layers applied to model I/O
- **Integration Points**: NATS subscriptions and event publishing

## Status

🚧 **Under Construction** - Basic integration scaffolding only. Full implementation pending Model Management completion.
