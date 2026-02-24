"""
Test suite for Internal File Sharing System

This package contains all tests for the application:
- test_auth_service.py: Authentication and authorization tests
- test_file_service.py: File upload, download, and management tests
- test_admin_service.py: Admin functionality tests
- test_audit_service.py: Audit logging tests
- test_models.py: Database model tests
- test_integration.py: End-to-end integration tests

Run tests with:
    pytest                          # Run all tests
    pytest -v                       # Verbose output
    pytest --cov=app                # With coverage
    pytest tests/test_auth_service.py  # Specific test file
    pytest -k test_login            # Specific test pattern
"""
