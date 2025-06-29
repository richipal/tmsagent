#!/usr/bin/env python3
"""
Test runner script for the TMS Agent backend
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        return False
    else:
        print("✅ Command completed successfully")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run tests for TMS Agent backend")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", help="Run specific test file")
    parser.add_argument("--function", help="Run specific test function")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    
    args = parser.parse_args()
    
    # Set up environment
    os.environ["TESTING"] = "true"
    os.environ["GOOGLE_API_KEY"] = "test-api-key"
    os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
    os.environ["BIGQUERY_DATASET_ID"] = "test_dataset"
    
    # Base pytest command
    cmd = ["poetry", "run", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.extend(["-v", "-s"])
    
    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    # Add markers
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    
    # Skip slow tests
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    # Specific file or function
    if args.file:
        if args.function:
            cmd.append(f"{args.file}::{args.function}")
        else:
            cmd.append(args.file)
    elif args.function:
        cmd.extend(["-k", args.function])
    
    # Run tests
    print("🧪 TMS Agent Backend Test Runner")
    print("================================")
    
    success = run_command(cmd, "Running tests")
    
    if success:
        print("\n🎉 All tests passed!")
        
        if args.coverage:
            print("\n📊 Coverage report generated:")
            print("  - HTML: htmlcov/index.html")
            print("  - Terminal output above")
        
        return 0
    else:
        print("\n❌ Tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())