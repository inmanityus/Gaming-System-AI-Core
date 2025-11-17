#!/usr/bin/env python3
"""
Compile engagement protobuf definitions
"""
import subprocess
import sys
from pathlib import Path


def compile_proto():
    """Compile the engagement proto file to Python."""
    # Get paths
    repo_root = Path(__file__).parent.parent.parent
    proto_dir = repo_root / "proto"
    proto_file = proto_dir / "ethelred_engagement.proto"
    output_dir = Path(__file__).parent / "generated"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Add __init__.py
    (output_dir / "__init__.py").write_text("")
    
    # Compile proto
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"--proto_path={proto_dir}",
        f"--python_out={output_dir}",
        f"--pyi_out={output_dir}",
        str(proto_file)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error compiling proto: {result.stderr}")
        sys.exit(1)
    
    print(f"Successfully compiled {proto_file} to {output_dir}")
    

if __name__ == "__main__":
    compile_proto()

