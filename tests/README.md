# Test Suite for Telegram Crossposter SaaS

This directory contains automated tests that emulate the full SaaS application flow.

## Files

- `mocks.py` - Mock implementations for external services (Telegram API, Max API, SMTP, Cloudflare Turnstile)
- `test_result.py` - Test result and suite data structures
- `test_emulator.py` - Main test emulator that coordinates all mocks
- `integration_tests.py` - Integration tests that verify the full user flow
- `run_tests.py` - Main test runner script

## Running Tests

### Quick Start

```bash
# Make sure the backend is running
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, run tests
cd ..
python tests/run_tests.py
```

### Environment Setup

The tests use `http://localhost:8000` as the default API URL. If your backend runs elsewhere, set the `API_URL` environment variable:

```bash
API_URL=http://localhost:8001 python tests/run_tests.py
```

### Test Categories

1. **Mock Components** - Verifies that all mock services work correctly
2. **User Registration** - Tests user registration with email verification
3. **Email Verification** - Tests email verification token flow
4. **Update User Settings** - Tests updating Max credentials
5. **Create Telegram Connection** - Tests creating a Telegram bot connection with webhook
6. **Create Connection** - Tests creating Telegram->Max mapping
7. **Forward Text Post (Webhook)** - Tests end-to-end post forwarding via webhook

## Mock Services

### Mock Telegram API
- Simulates `getMe`, `setWebhook`, `deleteWebhook`, `getWebhookInfo`
- Provides a default test bot (`@test_bot`)
- Provides a default test channel (`@testchannel`)
- Can create channel posts for webhook testing

### Mock Max API
- Simulates sending text messages to Max
- Provides message tracking for verification
- Returns mock message IDs

### Mock SMTP
- Simulates email sending
- Tracks sent emails for verification
- Can extract verification/reset tokens from sent emails

### Mock Cloudflare Turnstile
- Simulates captcha validation
- Generates valid tokens for testing
- Always validates successfully

## Test Output

```
======================================================================
  TEST SUITE: Telegram Crossposter SaaS Integration Tests
======================================================================

1. User Registration
   Status: ✓ PASS
   Message: Registered user test_1234567890@example.com, email sent
   Duration: 45.23ms

...

----------------------------------------------------------------------
  SUMMARY: 6/6 tests passed
  Passed: 6
  Failed: 0
======================================================================
```

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed
- `130` - Test run interrupted by user

## Notes

- Tests require a running backend server
- External API calls are mocked, no real tokens or services needed
- Test data uses randomized email addresses to avoid conflicts
- The emulator cleans up between tests where appropriate
