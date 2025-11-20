"""
Check license compliance for dependencies.
Ensures no incompatible licenses are used.
"""
import json
import sys
from typing import List, Dict, Set


# Licenses that are compatible with commercial use
APPROVED_LICENSES = {
    'MIT',
    'MIT License',
    'BSD',
    'BSD License',
    'BSD-2-Clause',
    'BSD-3-Clause',
    'Apache 2.0',
    'Apache License 2.0',
    'Apache Software License',
    'ISC',
    'ISC License',
    'Python Software Foundation License',
    'PSF',
    'Unlicense',
    'CC0',
    'Public Domain',
}

# Licenses that need review
REVIEW_LICENSES = {
    'LGPL',
    'LGPL-2.1',
    'LGPL-3.0',
    'Mozilla Public License',
    'MPL-2.0',
}

# Licenses that are not allowed
FORBIDDEN_LICENSES = {
    'GPL',
    'GPL-2.0',
    'GPL-3.0',
    'AGPL',
    'AGPL-3.0',
    'SSPL',
    'Commons Clause',
}


def normalize_license(license_name: str) -> str:
    """Normalize license name for comparison."""
    if not license_name:
        return 'UNKNOWN'
    
    # Remove version numbers and clean up
    normalized = license_name.strip().upper()
    normalized = normalized.replace('-', ' ')
    normalized = normalized.replace('V', ' ')
    normalized = normalized.replace('VERSION', '')
    normalized = normalized.replace('LICENSE', '')
    normalized = normalized.replace('  ', ' ')
    
    return normalized.strip()


def check_licenses(licenses_file: str) -> Dict[str, List[Dict]]:
    """Check licenses from pip-licenses output."""
    try:
        with open(licenses_file, 'r') as f:
            licenses_data = json.load(f)
    except Exception as e:
        print(f"Error reading licenses file: {e}", file=sys.stderr)
        sys.exit(1)
    
    results = {
        'approved': [],
        'review': [],
        'forbidden': [],
        'unknown': []
    }
    
    for package in licenses_data:
        package_name = package.get('Name', 'Unknown')
        package_version = package.get('Version', 'Unknown')
        license_name = package.get('License', 'Unknown')
        
        normalized = normalize_license(license_name)
        
        package_info = {
            'name': package_name,
            'version': package_version,
            'license': license_name,
            'normalized_license': normalized
        }
        
        # Check against our license lists
        found = False
        
        # Check approved licenses
        for approved in APPROVED_LICENSES:
            if normalize_license(approved) in normalized or normalized in normalize_license(approved):
                results['approved'].append(package_info)
                found = True
                break
        
        if not found:
            # Check review licenses
            for review in REVIEW_LICENSES:
                if normalize_license(review) in normalized or normalized in normalize_license(review):
                    results['review'].append(package_info)
                    found = True
                    break
        
        if not found:
            # Check forbidden licenses
            for forbidden in FORBIDDEN_LICENSES:
                if normalize_license(forbidden) in normalized or normalized in normalize_license(forbidden):
                    results['forbidden'].append(package_info)
                    found = True
                    break
        
        if not found:
            # Unknown license
            results['unknown'].append(package_info)
    
    return results


def generate_report(results: Dict[str, List[Dict]]) -> None:
    """Generate license compliance report."""
    total_packages = sum(len(packages) for packages in results.values())
    
    print("=" * 60)
    print("LICENSE COMPLIANCE REPORT")
    print("=" * 60)
    print(f"\nTotal packages analyzed: {total_packages}")
    print(f"Approved licenses: {len(results['approved'])}")
    print(f"Need review: {len(results['review'])}")
    print(f"Forbidden licenses: {len(results['forbidden'])}")
    print(f"Unknown licenses: {len(results['unknown'])}")
    
    # Show forbidden licenses (critical)
    if results['forbidden']:
        print("\n❌ FORBIDDEN LICENSES (Must be removed or replaced):")
        print("-" * 60)
        for pkg in results['forbidden']:
            print(f"  - {pkg['name']} ({pkg['version']}): {pkg['license']}")
    
    # Show licenses needing review
    if results['review']:
        print("\n⚠️  LICENSES NEEDING REVIEW:")
        print("-" * 60)
        for pkg in results['review']:
            print(f"  - {pkg['name']} ({pkg['version']}): {pkg['license']}")
    
    # Show unknown licenses
    if results['unknown']:
        print("\n❓ UNKNOWN LICENSES (Need manual verification):")
        print("-" * 60)
        for pkg in results['unknown']:
            print(f"  - {pkg['name']} ({pkg['version']}): {pkg['license']}")
    
    # Summary
    print("\n" + "=" * 60)
    if results['forbidden']:
        print("❌ COMPLIANCE CHECK FAILED - Forbidden licenses detected!")
    elif results['unknown'] or results['review']:
        print("⚠️  COMPLIANCE CHECK NEEDS REVIEW - Some licenses need manual verification")
    else:
        print("✅ COMPLIANCE CHECK PASSED - All licenses are approved")
    print("=" * 60)


def create_exceptions_file():
    """Create a template for license exceptions."""
    exceptions_template = {
        "exceptions": [
            {
                "package": "example-package",
                "version": "1.0.0",
                "license": "LGPL-3.0",
                "reason": "Used only in development, not distributed",
                "approved_by": "Legal Team",
                "date": "2024-01-01"
            }
        ]
    }
    
    with open('license-exceptions.json', 'w') as f:
        json.dump(exceptions_template, f, indent=2)
    
    print("Created license-exceptions.json template")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python check_license_compliance.py <licenses.json>", file=sys.stderr)
        print("       python check_license_compliance.py --create-exceptions", file=sys.stderr)
        sys.exit(1)
    
    if sys.argv[1] == '--create-exceptions':
        create_exceptions_file()
        sys.exit(0)
    
    licenses_file = sys.argv[1]
    
    # Check licenses
    results = check_licenses(licenses_file)
    
    # Load exceptions if they exist
    exceptions = {}
    try:
        with open('license-exceptions.json', 'r') as f:
            exceptions_data = json.load(f)
            for exc in exceptions_data.get('exceptions', []):
                key = f"{exc['package']}-{exc['version']}"
                exceptions[key] = exc
    except FileNotFoundError:
        pass
    
    # Apply exceptions
    for category in ['forbidden', 'review', 'unknown']:
        filtered = []
        for pkg in results[category]:
            key = f"{pkg['name']}-{pkg['version']}"
            if key not in exceptions:
                filtered.append(pkg)
            else:
                print(f"ℹ️  Exception applied for {pkg['name']} ({pkg['version']}): {exceptions[key]['reason']}")
        results[category] = filtered
    
    # Generate report
    generate_report(results)
    
    # Exit with appropriate code
    if results['forbidden']:
        sys.exit(1)
    elif results['unknown'] or results['review']:
        sys.exit(2)  # Warning exit code
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
