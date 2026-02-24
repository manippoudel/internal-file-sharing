# Testing Guide
## Internal File Sharing System

This document provides comprehensive instructions for running and maintaining the test suite.

---

## Overview

The testing suite provides comprehensive coverage of both backend and frontend functionality:

- **Backend**: 10 test files with pytest, testing services, models, and API endpoints
- **Frontend**: Vitest tests for stores and components
- **Integration**: End-to-end workflow testing
- **Coverage**: Targets 70%+ coverage on critical paths

---

## Backend Testing (Python/pytest)

### Setup

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start test database**:
   ```bash
   # From project root
   docker-compose --profile test up -d test-db
   ```

   This starts a PostgreSQL test database on port 5433.

3. **Verify test database**:
   ```bash
   docker ps | grep filedb_test
   ```

### Running Tests

**Run all tests**:
```bash
cd backend
pytest
```

**Run with coverage**:
```bash
pytest --cov=app --cov-report=html
```

Coverage report will be generated in `backend/htmlcov/index.html`.

**Run specific test file**:
```bash
pytest tests/test_auth_service.py -v
```

**Run specific test**:
```bash
pytest tests/test_auth_service.py::TestAuthService::test_successful_login -v
```

**Run tests by marker**:
```bash
pytest -m auth      # Authentication tests only
pytest -m files     # File operation tests only
pytest -m admin     # Admin tests only
```

**Run with detailed output**:
```bash
pytest -v -s
```

### Test Files

| File | Tests | Description |
|------|-------|-------------|
| `test_auth_service.py` | 15+ tests | Authentication, login, logout, password changes, account lockout |
| `test_file_service.py` | 25+ tests | File upload, download, delete, restore, chunked uploads, cleanup |
| `test_admin_service.py` | 10+ tests | Admin API endpoints, user management, system health |
| `test_audit_service.py` | 8+ tests | Audit logging, filtering, pagination |
| `test_models.py` | 10+ tests | Database model validations, relationships, constraints |
| `test_integration.py` | 6+ tests | End-to-end workflows |

### Test Coverage

Current coverage targets:
- Authentication: 90%+
- File operations: 85%+
- Admin functions: 80%+
- Models: 90%+
- Overall: 70%+

---

## Frontend Testing (JavaScript/Vitest)

### Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Verify Vitest is installed**:
   ```bash
   npm run test -- --version
   ```

### Running Tests

**Run all tests**:
```bash
cd frontend
npm run test
```

**Run in watch mode** (re-runs on file changes):
```bash
npm run test:watch
```

**Run with coverage**:
```bash
npm run test:coverage
```

**Run with UI** (interactive mode):
```bash
npm run test:ui
```

Then open http://localhost:51204 in your browser.

**Run specific test file**:
```bash
npm run test tests/stores/auth.test.js
```

### Test Files

| File | Tests | Description |
|------|-------|-------------|
| `stores/auth.test.js` | 10+ tests | Auth store: login, logout, isAuthenticated, isAdmin |
| `stores/files.test.js` | 12+ tests | Files store: fetch, delete, restore, selection, pagination |
| `components/example.test.js` | Examples | Component testing patterns and examples |

### Frontend Test Coverage

Coverage report will be generated in `frontend/coverage/index.html`.

---

## Test Database Management

### Starting Test Database

```bash
# Start only test database
docker-compose --profile test up -d test-db

# Stop test database
docker-compose --profile test down

# View logs
docker-compose --profile test logs test-db
```

### Connecting to Test Database

```bash
# Via docker exec
docker exec -it filedb_test psql -U testuser -d filedb_test

# Via psql (if installed locally)
psql -h localhost -p 5433 -U testuser -d filedb_test
```

Password: `testpassword`

### Resetting Test Database

```bash
docker-compose --profile test down -v
docker-compose --profile test up -d test-db
```

---

## CI/CD Integration

### Running Tests in CI

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: filedb_test
        ports:
          - 5433:5432

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm install

      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
```

---

## Writing New Tests

### Backend Test Template

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

class TestNewFeature:
    """Test new feature"""

    async def test_feature_works(self, db_session: AsyncSession, test_user: User):
        """Test that the feature works as expected"""
        # Arrange
        # ... setup test data

        # Act
        result = await some_function(db_session, test_user.id)

        # Assert
        assert result is not None
        assert result.property == expected_value
```

### Frontend Test Template

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

describe('New Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render correctly', () => {
    const wrapper = mount(NewComponent)
    expect(wrapper.exists()).toBe(true)
  })

  it('should handle user interaction', async () => {
    const wrapper = mount(NewComponent)
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted()).toHaveProperty('customEvent')
  })
})
```

---

## Troubleshooting

### Backend Tests

**Issue**: Database connection refused
```
Solution: Ensure test database is running
$ docker-compose --profile test up -d test-db
$ docker ps | grep filedb_test
```

**Issue**: Import errors
```
Solution: Install dependencies
$ cd backend && pip install -r requirements.txt
```

**Issue**: Tests fail with "asyncio" errors
```
Solution: Ensure pytest-asyncio is installed
$ pip install pytest-asyncio==0.21.1
```

### Frontend Tests

**Issue**: Module not found errors
```
Solution: Install dependencies
$ cd frontend && npm install
```

**Issue**: Tests fail with "localStorage is not defined"
```
Solution: Verify setup.js is configured correctly in vitest.config.js
The setup file mocks localStorage automatically
```

**Issue**: Component import errors
```
Solution: Check alias configuration in vitest.config.js
Ensure '@' alias points to './src'
```

---

## Best Practices

### General
1. **Run tests before committing** - Catch issues early
2. **Write tests for new features** - Maintain coverage
3. **Keep tests isolated** - Each test should be independent
4. **Use descriptive names** - Test names should explain what they test
5. **Mock external dependencies** - Tests should not call real APIs

### Backend
1. **Use fixtures** - Reuse test data setup via conftest.py
2. **Test async code** - Use pytest-asyncio for async functions
3. **Clean database state** - Fixtures handle cleanup automatically
4. **Test edge cases** - Not just happy paths

### Frontend
1. **Mock API calls** - Don't make real HTTP requests
2. **Test user interactions** - Trigger events, test outputs
3. **Test store integration** - Verify components use stores correctly
4. **Keep tests fast** - Mock heavy operations

---

## Metrics & Reporting

### View Coverage Reports

**Backend**:
```bash
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html  # or xdg-open on Linux
```

**Frontend**:
```bash
cd frontend
npm run test:coverage
open coverage/index.html
```

### Coverage Goals

- **Critical paths** (auth, file operations): 90%+
- **Admin functions**: 80%+
- **Overall**: 70%+

### Test Execution Time

- Backend tests: ~30-60 seconds
- Frontend tests: ~5-10 seconds
- Total: Under 2 minutes

---

## Continuous Improvement

### Adding More Tests

1. Identify untested code paths in coverage report
2. Write tests for new features before implementing (TDD)
3. Add integration tests for complex workflows
4. Consider E2E tests with Playwright for critical user flows

### Maintaining Tests

1. Update tests when features change
2. Remove obsolete tests
3. Refactor duplicate test code into fixtures/helpers
4. Keep test data realistic but minimal

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Vue Test Utils](https://test-utils.vuejs.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

## Support

If you encounter issues with the test suite:

1. Check this documentation first
2. Review the test output carefully
3. Verify dependencies are installed
4. Ensure test database is running
5. Check for recent code changes that might affect tests

For questions or issues, consult the main README.md or project documentation.
