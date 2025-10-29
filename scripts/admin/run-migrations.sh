#!/bin/bash
# Admin Database Migration Runner
# Applies all admin migrations in order

set -e

echo "🔄 Running Admin Site Migrations..."

# Database connection
DB_HOST="${DB_HOST:-localhost}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-befreefitness}"

# Migration files
MIGRATIONS=(
  "database-migrations/admin-001-security-hardening.sql"
  "database-migrations/admin-002-core-admin-tables.sql"
  "database-migrations/admin-003-all-admin-features.sql"
)

# Apply each migration
for migration in "${MIGRATIONS[@]}"; do
  echo "Applying: $migration"
  psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f "$migration"
  
  if [ $? -eq 0 ]; then
    echo "✅ Success: $migration"
  else
    echo "❌ Failed: $migration"
    exit 1
  fi
done

echo "✅ All migrations applied successfully!"

# Verify tables created
echo ""
echo "Verifying tables..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
  SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columns
  FROM information_schema.tables t
  WHERE table_schema = 'public' 
    AND (table_name LIKE '%admin%' OR table_name IN ('broadcasts', 'content_flags', 'ai_sessions'))
  ORDER BY table_name;
"

echo ""
echo "🎉 Admin database setup complete!"






