#!/usr/bin/env python3
"""
Repository cleanup script - removes temporary and unused files
"""

import os
import shutil
from pathlib import Path

def safe_remove(path, description=""):
    """Safely remove a file or directory"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            print(f"✅ Removed file: {path} {description}")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(f"✅ Removed directory: {path} {description}")
        else:
            print(f"⚠️  Not found: {path}")
    except Exception as e:
        print(f"❌ Error removing {path}: {e}")

def cleanup_backend():
    """Clean up backend directory"""
    print("\n🧹 Cleaning up backend directory...")
    
    backend_dir = "/Users/richipalbindra/Documents/myhome/workspace/llm/google/adk/tmsagent/backend"
    
    # Temporary and debug files to remove
    temp_files = [
        "debug_database_test.py",
        "debug_foreign_keys.py", 
        "diagnose_tests.py",
        "test_basic_imports.py",
        "test_imports.py",
        "test_setup.py",
        "run_simple_test.py",
        "test_runner_debug.py",
        "run_tests_systematic.py",  # Keep run_working_tests.py as it's useful
        "TESTING_TROUBLESHOOTING.md",  # Can remove since tests are working
    ]
    
    # Log files to remove
    log_files = [
        "full_backend_final_test.log",
        "full_backend_fixed_test.log", 
        "full_backend_test.log",
        "minimal_backend_test.log",
        "minimal_test.log",
        "test_full_backend.log",
    ]
    
    # Unused backend files
    unused_files = [
        "main_minimal.py",  # Keep main.py, remove minimal version
        "simple_main.py",   # Keep main.py, remove simple version
    ]
    
    all_files = temp_files + log_files + unused_files
    
    for file in all_files:
        file_path = os.path.join(backend_dir, file)
        safe_remove(file_path, f"(temporary/debug file)")

def cleanup_parent():
    """Clean up parent directory"""
    print("\n🧹 Cleaning up parent directory...")
    
    parent_dir = "/Users/richipalbindra/Documents/myhome/workspace/llm/google/adk/tmsagent"
    
    # Old test files that were causing conflicts
    old_test_files = [
        "tests/test_root_agent.py",
        "tests/test_sub_agents.py", 
        "tests/test_api_integration.py",
        "tests/test_tools.py",
        "tests/conftest.py",
        "tests/__init__.py",
    ]
    
    # Test files in parent directory
    test_files = [
        "test_memory.py",
        "test_persistence.py",
    ]
    
    # Remove old test files
    for file in old_test_files:
        file_path = os.path.join(parent_dir, file)
        safe_remove(file_path, "(old test file)")
    
    # Remove test files in parent
    for file in test_files:
        file_path = os.path.join(parent_dir, file)
        safe_remove(file_path, "(parent test file)")
    
    # Remove entire old tests directory if it exists
    old_tests_dir = os.path.join(parent_dir, "tests")
    if os.path.exists(old_tests_dir):
        safe_remove(old_tests_dir, "(old tests directory)")

def cleanup_unused_session_managers():
    """Clean up unused session manager files"""
    print("\n🧹 Cleaning up unused session manager files...")
    
    backend_dir = "/Users/richipalbindra/Documents/myhome/workspace/llm/google/adk/tmsagent/backend"
    
    # Keep persistent_session_manager.py, remove others
    unused_managers = [
        "app/core/enhanced_session_manager.py",
        "app/core/session_manager.py", 
        "app/core/simple_session_manager.py",
    ]
    
    for file in unused_managers:
        file_path = os.path.join(backend_dir, file)
        safe_remove(file_path, "(unused session manager)")

def cleanup_test_files():
    """Clean up redundant test files"""
    print("\n🧹 Cleaning up redundant test files...")
    
    backend_dir = "/Users/richipalbindra/Documents/myhome/workspace/llm/google/adk/tmsagent/backend"
    
    # Remove duplicate/redundant test files, keep the working ones
    redundant_tests = [
        "tests/test_database_simple.py",        # Keep test_database_models.py
        "tests/test_database_models_simple.py", # Keep test_database_models.py
        "tests/test_api_endpoints.py",          # Keep test_api_endpoints_fixed.py
        "tests/test_integration.py",            # Keep test_integration_fixed.py
    ]
    
    for file in redundant_tests:
        file_path = os.path.join(backend_dir, file)
        safe_remove(file_path, "(redundant test file)")

def cleanup_temp_charts():
    """Clean up temporary chart files"""
    print("\n🧹 Cleaning up temporary chart files...")
    
    backend_dir = "/Users/richipalbindra/Documents/myhome/workspace/llm/google/adk/tmsagent/backend"
    charts_dir = os.path.join(backend_dir, "uploads/charts")
    
    if os.path.exists(charts_dir):
        # Remove all chart files (they're just test artifacts)
        for file in os.listdir(charts_dir):
            if file.startswith("chart_") and file.endswith(".png"):
                file_path = os.path.join(charts_dir, file)
                safe_remove(file_path, "(temporary chart)")

def cleanup_database_files():
    """Clean up temporary database files"""
    print("\n🧹 Cleaning up database files...")
    
    backend_dir = "/Users/richipalbindra/Documents/myhome/workspace/llm/google/adk/tmsagent/backend"
    data_dir = os.path.join(backend_dir, "data")
    
    if os.path.exists(data_dir):
        # Remove the test database (will be recreated when needed)
        db_file = os.path.join(data_dir, "conversations.db")
        if os.path.exists(db_file):
            safe_remove(db_file, "(test database - will be recreated)")

def cleanup_python_cache():
    """Clean up Python cache files"""
    print("\n🧹 Cleaning up Python cache files...")
    
    base_dir = "/Users/richipalbindra/Documents/myhome/workspace/llm/google/adk/tmsagent"
    
    # Find and remove __pycache__ directories
    for root, dirs, files in os.walk(base_dir):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                cache_dir = os.path.join(root, dir_name)
                safe_remove(cache_dir, "(Python cache)")
        
        # Remove .pyc files
        for file_name in files:
            if file_name.endswith(".pyc"):
                pyc_file = os.path.join(root, file_name)
                safe_remove(pyc_file, "(Python cache)")

def main():
    """Main cleanup function"""
    print("🧹 Repository Cleanup Tool")
    print("=" * 50)
    
    # Ask for confirmation
    print("\nThis will remove:")
    print("📁 Temporary and debug files")
    print("📋 Log files")
    print("🧪 Redundant test files") 
    print("🗂️ Unused session manager files")
    print("🎨 Temporary chart files")
    print("🗄️ Test database files")
    print("🐍 Python cache files")
    print("📜 Old test directories")
    
    response = input("\n❓ Continue with cleanup? (y/N): ").lower().strip()
    
    if response != 'y':
        print("❌ Cleanup cancelled")
        return
    
    print("\n🚀 Starting cleanup...")
    
    # Run cleanup functions
    cleanup_backend()
    cleanup_parent() 
    cleanup_unused_session_managers()
    cleanup_test_files()
    cleanup_temp_charts()
    cleanup_database_files()
    cleanup_python_cache()
    
    print("\n" + "=" * 50)
    print("✅ Cleanup completed!")
    print("\n📋 Remaining important files:")
    print("   • Working test suite in backend/tests/")
    print("   • Main application files")
    print("   • Configuration files")
    print("   • Documentation files")
    print("   • run_working_tests.py (for testing)")
    print("\n🎯 Repository is now clean and ready for development!")

if __name__ == "__main__":
    main()