"""
Validate database migration files for conflicts and issues.
Used in CI/CD pipeline before applying migrations.
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple


def find_migration_files(migrations_dir: str = "infrastructure/database/migrations") -> List[Path]:
    """Find all migration files."""
    migrations_path = Path(migrations_dir)
    if not migrations_path.exists():
        print(f"Migrations directory not found: {migrations_dir}")
        return []
    
    # Alembic migration pattern
    alembic_pattern = re.compile(r'^\d+_[a-f0-9]+_.*\.py$')
    
    migration_files = []
    for file in migrations_path.iterdir():
        if file.is_file() and alembic_pattern.match(file.name):
            migration_files.append(file)
    
    return sorted(migration_files)


def check_revision_conflicts(migration_files: List[Path]) -> List[str]:
    """Check for revision ID conflicts."""
    errors = []
    revisions = {}
    
    for file in migration_files:
        content = file.read_text()
        
        # Extract revision ID
        revision_match = re.search(r"revision = ['\"]([a-f0-9]+)['\"]", content)
        if not revision_match:
            errors.append(f"{file.name}: Missing revision ID")
            continue
        
        revision = revision_match.group(1)
        
        if revision in revisions:
            errors.append(
                f"Duplicate revision ID {revision} in files: "
                f"{revisions[revision]} and {file.name}"
            )
        else:
            revisions[revision] = file.name
    
    return errors


def check_down_revision_chain(migration_files: List[Path]) -> List[str]:
    """Check that down_revision chain is valid."""
    errors = []
    revisions = set()
    down_revisions = set()
    revision_to_file = {}
    
    for file in migration_files:
        content = file.read_text()
        
        # Extract revision and down_revision
        revision_match = re.search(r"revision = ['\"]([a-f0-9]+)['\"]", content)
        down_revision_match = re.search(r"down_revision = ['\"]([a-f0-9]+|None)['\"]", content)
        
        if revision_match:
            revision = revision_match.group(1)
            revisions.add(revision)
            revision_to_file[revision] = file.name
        
        if down_revision_match and down_revision_match.group(1) != "None":
            down_revision = down_revision_match.group(1)
            down_revisions.add(down_revision)
    
    # Check for orphaned migrations
    orphaned = down_revisions - revisions
    if orphaned:
        for orphan in orphaned:
            errors.append(f"Reference to non-existent revision: {orphan}")
    
    # Check for multiple heads
    heads = revisions - down_revisions
    if len(heads) > 1:
        head_files = [revision_to_file.get(h, h) for h in heads]
        errors.append(f"Multiple migration heads detected: {', '.join(head_files)}")
    
    return errors


def check_sql_safety(migration_files: List[Path]) -> List[str]:
    """Check for potentially dangerous SQL operations."""
    errors = []
    warnings = []
    
    dangerous_patterns = [
        (r'DROP\s+TABLE\s+(?!IF\s+EXISTS)', "DROP TABLE without IF EXISTS"),
        (r'TRUNCATE\s+TABLE', "TRUNCATE TABLE is dangerous in migrations"),
        (r'DELETE\s+FROM\s+\w+\s*;', "DELETE without WHERE clause"),
        (r'UPDATE\s+\w+\s+SET.*\s*;', "UPDATE without WHERE clause"),
    ]
    
    warning_patterns = [
        (r'ALTER\s+TABLE.*DROP\s+COLUMN', "Dropping column - ensure data is backed up"),
        (r'CREATE\s+INDEX(?!\s+CONCURRENTLY)', "CREATE INDEX without CONCURRENTLY blocks table"),
        (r'ALTER\s+TABLE.*ALTER\s+COLUMN.*TYPE', "Changing column type can be dangerous"),
    ]
    
    for file in migration_files:
        content = file.read_text()
        
        # Check dangerous patterns
        for pattern, message in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                errors.append(f"{file.name}: {message}")
        
        # Check warning patterns
        for pattern, message in warning_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                warnings.append(f"{file.name}: WARNING - {message}")
    
    # Print warnings but don't fail
    for warning in warnings:
        print(f"⚠️  {warning}")
    
    return errors


def check_migration_dependencies(migration_files: List[Path]) -> List[str]:
    """Check that migrations don't have circular dependencies."""
    errors = []
    
    # Build dependency graph
    graph = {}
    for file in migration_files:
        content = file.read_text()
        
        revision_match = re.search(r"revision = ['\"]([a-f0-9]+)['\"]", content)
        down_revision_match = re.search(r"down_revision = ['\"]([a-f0-9]+|None)['\"]", content)
        
        if revision_match and down_revision_match:
            revision = revision_match.group(1)
            down_revision = down_revision_match.group(1) if down_revision_match.group(1) != "None" else None
            graph[revision] = down_revision
    
    # Check for cycles using DFS
    def has_cycle(node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
        visited.add(node)
        rec_stack.add(node)
        
        if node in graph and graph[node]:
            neighbor = graph[node]
            if neighbor not in visited:
                if has_cycle(neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node)
        return False
    
    visited = set()
    for node in graph:
        if node not in visited:
            if has_cycle(node, visited, set()):
                errors.append(f"Circular dependency detected involving revision {node}")
    
    return errors


def check_upgrade_downgrade_symmetry(migration_files: List[Path]) -> List[str]:
    """Check that upgrade and downgrade functions are properly defined."""
    errors = []
    
    for file in migration_files:
        content = file.read_text()
        
        # Check for upgrade function
        if not re.search(r'def\s+upgrade\s*\(\s*\)\s*:', content):
            errors.append(f"{file.name}: Missing upgrade() function")
        
        # Check for downgrade function
        if not re.search(r'def\s+downgrade\s*\(\s*\)\s*:', content):
            errors.append(f"{file.name}: Missing downgrade() function")
        
        # Check that downgrade is not empty (unless it's the initial migration)
        downgrade_match = re.search(
            r'def\s+downgrade\s*\(\s*\)\s*:.*?(?=def|\Z)',
            content,
            re.DOTALL
        )
        if downgrade_match:
            downgrade_body = downgrade_match.group(0)
            if 'pass' in downgrade_body and 'initial' not in file.name.lower():
                errors.append(f"{file.name}: Downgrade function is empty (contains only 'pass')")
    
    return errors


def main():
    """Main validation function."""
    print("🔍 Validating database migrations...")
    
    # Find migration files
    migration_files = find_migration_files()
    
    if not migration_files:
        print("No migration files found.")
        return 0
    
    print(f"Found {len(migration_files)} migration files")
    
    all_errors = []
    
    # Run validation checks
    checks = [
        ("Checking revision conflicts", check_revision_conflicts),
        ("Checking down_revision chain", check_down_revision_chain),
        ("Checking SQL safety", check_sql_safety),
        ("Checking migration dependencies", check_migration_dependencies),
        ("Checking upgrade/downgrade symmetry", check_upgrade_downgrade_symmetry),
    ]
    
    for check_name, check_func in checks:
        print(f"\n{check_name}...")
        errors = check_func(migration_files)
        if errors:
            all_errors.extend(errors)
            for error in errors:
                print(f"  ❌ {error}")
        else:
            print(f"  ✅ Passed")
    
    # Summary
    print(f"\n{'='*60}")
    if all_errors:
        print(f"❌ Validation failed with {len(all_errors)} errors")
        return 1
    else:
        print("✅ All migration validations passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
