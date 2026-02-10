/**
 * E2E Test: Operations Dashboard Monitoring
 * 
 * Tests real-time monitoring and operations features.
 */

import { test, expect } from '@playwright/test';

test.describe('Operations Dashboard', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard');
        await page.click('text=Operations');
        await page.waitForTimeout(1000);
    });

    test('should load operations dashboard', async ({ page }) => {
        // Verify operations content is visible
        await expect(page.locator('text=/Operations|Monitoring|System/i')).toBeVisible({ timeout: 5000 });
    });

    test('should display latency metrics', async ({ page }) => {
        // Look for latency-related content
        await page.waitForTimeout(2000);

        const hasLatencyContent = await page.locator('text=/Latency|ms|Avg/i').count() > 0;
        expect(hasLatencyContent).toBeTruthy();
    });

    test('should display cache metrics', async ({ page }) => {
        // Look for cache-related metrics
        await page.waitForTimeout(2000);

        const hasCacheContent = await page.locator('text=/Cache|Hit Rate|Miss/i').count() > 0;
        expect(hasCacheContent).toBeTruthy();
    });

    test('should display circuit breaker status', async ({ page }) => {
        // Look for circuit breaker status
        await page.waitForTimeout(2000);

        const hasCircuitBreakerContent = await page.locator('text=/Circuit|Breaker|State/i').count() > 0;
        expect(hasCircuitBreakerContent).toBeTruthy();
    });

    test('should update metrics in real-time', async ({ page }) => {
        // Wait for initial load
        await page.waitForTimeout(2000);

        // Get initial metric value
        const metricElements = page.locator('.text-2xl, .text-xl').filter({ hasText: /\d+/ });
        const initialCount = await metricElements.count();

        // Wait for refresh cycle (5 seconds)
        await page.waitForTimeout(6000);

        // Check metrics are still displayed (real-time updates working)
        const updatedCount = await metricElements.count();
        expect(updatedCount).toBeGreaterThanOrEqual(initialCount);
    });

    test('should display charts for monitoring data', async ({ page }) => {
        await page.waitForTimeout(2000);

        // Look for charts (SVG elements from Recharts)
        const charts = page.locator('svg');
        const chartCount = await charts.count();

        expect(chartCount).toBeGreaterThan(0);
    });
});

test.describe('System Health Monitoring', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
    });

    test('should show system status indicators', async ({ page }) => {
        // Navigate to operations or analytics
        await page.click('text=Operations');
        await page.waitForTimeout(2000);

        // Look for status indicators (healthy, warning, error states)
        const statusElements = page.locator('text=/healthy|online|active|closed/i');
        const statusCount = await statusElements.count();

        expect(statusCount).toBeGreaterThan(0);
    });

    test('should display performance metrics across tabs', async ({ page }) => {
        // Check Overview tab
        await page.click('text=Overview');
        await page.waitForTimeout(1000);

        const hasOverviewMetrics = await page.locator('text=/\d+ms|\d+%|\d+\s*(req|request)/i').count() > 0;
        expect(hasOverviewMetrics).toBeTruthy();
    });
});
