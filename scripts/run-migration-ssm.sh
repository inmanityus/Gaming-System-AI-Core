#!/bin/bash
# Run migration via SSM

cd /home/ubuntu/gaming-system
source .env
PGPASSWORD=$DB_PASSWORD psql -h database.gaming-system.internal -U postgres -d gaming_system -f database/migrations/012_story_memory.sql

