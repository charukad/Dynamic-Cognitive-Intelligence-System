# E2E Testing Guide

## Setup

Install Playwright and browsers:

```bash
npm install -D @playwright/test
npx playwright install
```

## Running Tests

### Run all tests
```bash
npx playwright test
```

### Run specific test file
```bash
npx playwright test e2e/chat-interface.spec.ts
```

### Run tests in headed mode (see browser)
```bash
npx playwright test --headed
```

### Run tests with UI mode (interactive)
```bash
npx playwright test --ui
```

### Run tests in debug mode
```bash
npx playwright test --debug
```

### Run tests for specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

## Test Files

### `chat-interface.spec.ts` (9 tests)
Tests chat functionality:
- Loading chat interface
- Sending messages and receiving responses
- Submitting thumbs up/down feedback
- Toggling feedback
- Edge cases (disabled states, empty inputs)
- Multiple messages in conversation

### `dashboard-navigation.spec.ts` (12 tests)
Tests dashboard navigation:
- Main dashboard display
- Navigation between tabs (Overview, Evolution, Intelligence, Operations, Chat, Analytics)
- Unified Analytics dashboard views
- KPI card displays
- Chart visualizations
- Responsive design (mobile, tablet)

### `operations-monitoring.spec.ts` (8 tests)
Tests operations monitoring:
- Loading operations dashboard
- Displaying latency metrics
- Showing cache metrics
- Circuit breaker status
- Real-time metric updates
- System health indicators

## Test Coverage

**Total Tests:** 29 E2E tests
- Chat Interface: 9 tests
- Dashboard Navigation: 12 tests
- Operations Monitoring: 8 tests

## Viewing Test Reports

After running tests, view the HTML report:

```bash
npx playwright show-report
```

## Test Results

Test results are saved in:
- `test-results/` - Test artifacts (screenshots, videos, traces)
- `playwright-report/` - HTML report

## Screenshots and Videos

- **Screenshots**: Captured on test failure
- **Videos**: Recorded on test failure
- **Traces**: Captured on first retry

## CI/CD Integration

For CI environments, tests run with:
- Retries: 2 attempts
- Workers: 1 (sequential execution)
- Headless mode only

## Best Practices

1. **Wait for elements**: Use `waitForSelector` instead of `waitForTimeout` when possible
2. **Stable selectors**: Use data-testid attributes for critical elements
3. **Independent tests**: Each test should be self-contained
4. **Cleanup**: Tests automatically reset state via fixtures
5. **Timeouts**: Adjust timeouts for slower operations (API calls, animations)

## Debugging Failed Tests

1. Run in debug mode: `npx playwright test --debug`
2. Use UI mode: `npx playwright test --ui`
3. Check screenshots in `test-results/`
4. View trace files with: `npx playwright show-trace trace.zip`

## Common Issues

### Test timeout
Increase timeout in individual test:
```typescript
test('my test', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  // ... test code
});
```

### Element not found
Add explicit wait:
```typescript
await page.waitForSelector('.my-element', { timeout: 10000 });
```

### Network requests failing
Ensure backend server is running on `localhost:8000` before tests.

## Helper Functions

Located in `e2e/helpers.ts`:
- `waitForDashboardLoad()` - Wait for dashboard to fully load
- `navigateToTab()` - Navigate to specific tab
- `sendChatMessage()` - Send message and wait for response
- `submitFeedback()` - Submit thumbs up/down feedback
- `waitForCharts()` - Wait for chart rendering
- `verifyMetricCard()` - Verify metric card display
- `checkSystemHealth()` - Check system health status
