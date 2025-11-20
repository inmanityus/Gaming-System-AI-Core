#!/usr/bin/env python3
"""
Validate Python imports and syntax for all services.
This script helps catch import errors before deployment.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import ast
import importlib.util
import py_compile
import tempfile


class ImportValidator:
    """Validates Python imports and syntax for services."""
    
    def __init__(self, services_json: str = ".github/services.json"):
        self.services_json = services_json
        self.services = self._load_services()
        self.errors: List[Dict[str, any]] = []
        
    def _load_services(self) -> List[Dict[str, any]]:
        """Load services configuration from JSON file."""
        with open(self.services_json, 'r') as f:
            data = json.load(f)
        return [s for s in data['services'] if s['type'] == 'python']
    
    def validate_all(self) -> bool:
        """Validate all Python services."""
        print(f"Validating {len(self.services)} Python services...")
        
        all_valid = True
        for service in self.services:
            print(f"\n{'='*60}")
            print(f"Validating: {service['name']}")
            print(f"Path: {service['path']}")
            
            if not self.validate_service(service):
                all_valid = False
                
        return all_valid
    
    def validate_service(self, service: Dict[str, any]) -> bool:
        """Validate a single service."""
        service_path = Path(service['path'])
        
        if not service_path.exists():
            self.errors.append({
                'service': service['name'],
                'error': f"Service path does not exist: {service_path}"
            })
            return False
        
        # Find all Python files
        py_files = list(service_path.rglob('*.py'))
        if not py_files:
            print(f"  No Python files found in {service_path}")
            return True
        
        print(f"  Found {len(py_files)} Python files")
        
        # Validate each file
        service_valid = True
        for py_file in py_files:
            if not self._validate_file(py_file, service['name']):
                service_valid = False
                
        if service_valid:
            print(f"  ✓ All files validated successfully")
        else:
            print(f"  ✗ Validation failed")
            
        return service_valid
    
    def _validate_file(self, file_path: Path, service_name: str) -> bool:
        """Validate a single Python file."""
        relative_path = file_path.relative_to(Path.cwd())
        
        # 1. Check syntax by parsing AST
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            self.errors.append({
                'service': service_name,
                'file': str(relative_path),
                'error': f"Syntax error: {e.msg} at line {e.lineno}",
                'line': e.lineno
            })
            print(f"    ✗ {relative_path}: Syntax error at line {e.lineno}")
            return False
        except Exception as e:
            self.errors.append({
                'service': service_name,
                'file': str(relative_path),
                'error': f"Parse error: {str(e)}"
            })
            print(f"    ✗ {relative_path}: Parse error")
            return False
        
        # 2. Compile the file
        try:
            py_compile.compile(str(file_path), doraise=True)
        except py_compile.PyCompileError as e:
            self.errors.append({
                'service': service_name,
                'file': str(relative_path),
                'error': f"Compile error: {str(e)}"
            })
            print(f"    ✗ {relative_path}: Compile error")
            return False
        
        # 3. Extract and validate imports
        imports = self._extract_imports(content)
        if imports:
            invalid_imports = self._check_imports(imports, file_path, service_name)
            if invalid_imports:
                for imp in invalid_imports:
                    print(f"    ⚠ {relative_path}: Potential import issue: {imp}")
                # Don't fail on import warnings, just flag them
        
        return True
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract all import statements from Python code."""
        imports = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except:
            pass
        return imports
    
    def _check_imports(self, imports: List[str], file_path: Path, service_name: str) -> List[str]:
        """Check if imports are likely to work."""
        invalid_imports = []
        
        # Common modules that should be available
        stdlib_modules = {
            'os', 'sys', 'json', 'typing', 'datetime', 'time', 'logging',
            'pathlib', 'collections', 'itertools', 'functools', 'asyncio',
            'uuid', 'random', 'math', 're', 'abc', 'enum', 'dataclasses'
        }
        
        # Check each import
        for imp in imports:
            # Skip standard library modules
            base_module = imp.split('.')[0]
            if base_module in stdlib_modules:
                continue
                
            # Skip relative imports
            if imp.startswith('.'):
                continue
                
            # Skip service-local imports
            service_base = Path(service_name).name
            if imp.startswith(service_base):
                continue
                
            # Check if it's a known problematic import
            if base_module in ['services', 'shared']:
                # These are cross-service imports that might fail in containers
                invalid_imports.append(imp)
        
        return invalid_imports
    
    def print_summary(self):
        """Print validation summary."""
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")
        
        if not self.errors:
            print("✓ All services validated successfully!")
        else:
            print(f"✗ Found {len(self.errors)} errors:\n")
            
            # Group errors by service
            by_service = {}
            for error in self.errors:
                service = error['service']
                if service not in by_service:
                    by_service[service] = []
                by_service[service].append(error)
            
            # Print errors by service
            for service, errors in by_service.items():
                print(f"\n{service}:")
                for error in errors:
                    if 'file' in error:
                        print(f"  - {error['file']}: {error['error']}")
                    else:
                        print(f"  - {error['error']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Validate Python imports for microservices')
    parser.add_argument('--services-json', default='.github/services.json',
                        help='Path to services.json file')
    parser.add_argument('--service', help='Validate specific service only')
    parser.add_argument('--fix', action='store_true',
                        help='Attempt to fix common issues')
    
    args = parser.parse_args()
    
    validator = ImportValidator(args.services_json)
    
    if args.service:
        # Validate single service
        service = next((s for s in validator.services if s['name'] == args.service), None)
        if not service:
            print(f"Service not found: {args.service}")
            sys.exit(1)
        
        valid = validator.validate_service(service)
    else:
        # Validate all services
        valid = validator.validate_all()
    
    validator.print_summary()
    
    sys.exit(0 if valid else 1)


if __name__ == '__main__':
    main()
