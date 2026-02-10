/**
 * E2E Test: Dashboard Navigation and Analytics
 * 
 * Tests navigation between dashboard tabs and analytics visualization.
 */

import { test, expect } from '@playwright/test';

test.describe('Dashboard Navigation', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
    });

    test('should display main dashboard', async ({ page }) => {
        // Verify dashboard title/header is visible
        await expect(page).toHaveTitle(/DCIS/);

        // Verify navigation tabs are visible
        await expect(page.locator('text=Overview')).toBeVisible();
        await expect(page.locator('text=Chat')).toBeVisible();
        await expect(page.locator('text=Analytics')).toBeVisible();
    });

    test('should navigate to Overview tab', async ({ page }) => {
        await page.click('text=Overview');

        // Verify overview content loads
        await expect(page.locator('.performance-dashboard, .overview-section')).toBeVisible({ timeout: 5000 });
    });

    test('should navigate to Evolution tab', async ({ page }) => {
        await page.click('text=Evolution');

        // Verify evolution dashboard loads
        await expect(page.locator('text=Evolution').or(page.locator('text=Generation'))).toBeVisible({ timeout: 5000 });
    });

    test('should navigate to Intelligence tab', async ({ page }) => {
        await page.click('text=Intelligence');

        // Wait for intelligence content
        await page.waitForTimeout(1000);

        // Check for intelligence-related content
        const hasIntelligenceContent = await page.locator('text=Metacognition, text=Reasoning, text=Mirror').count() > 0;
        expect(hasIntelligenceContent).toBeTruthy();
    });

    test('should navigate to Operations tab', async ({ page }) => {
        await page.click('text=Operations');

        // Verify operations dashboard loads
        await expect(page.locator('text=Latency, text=Cache, text=Circuit Breaker')).toBeVisible({ timeout: 5000 });
    });

    test('should navigate between multiple tabs', async ({ page }) => {
        // Navigate through several tabs
        await page.click('text=Chat');
        await page.waitForTimeout(500);

        await page.click('text=Analytics');
        await page.waitForTimeout(500);

        await page.click('text=Operations');
        await page.waitForTimeout(500);

        // Verify final tab is active
        await expect(page.locator('text=Operations')).toBeVisible();
    });
});

test.describe('Unified Analytics Dashboard', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard');
        await page.click('text=Analytics');
        await page.waitForTimeout(1000);
    });

    test('should load analytics dashboard', async ({ page }) => {
        // Verify analytics content is present
        await expect(page.locator('text=System Analytics, text=Analytics, text=Health')).toBeVisible({ timeout: 5000 });
    });

    test('should display KPI cards', async ({ page }) => {
        // Look for metric cards/KPIs
        const kpis = page.locator('.text-2xl, .text-xl').filter({ hasText: /\d+/ });

        // Should have multiple KPI cards
        const count = await kpis.count();
        expect(count).toBeGreaterThan(0);
    });

    test('should switch between overview and detailed views', async ({ page }) => {
        // Look for view toggle buttons
        const overviewButton = page.locator('button:has-text("Overview")');
        const detailedButton = page.locator('button:has-text("Detailed")');

        if (await overviewButton.isVisible()) {
            // Click overview
            await overviewButton.click();
            await page.waitForTimeout(500);

            // Click detailed
            await detailedButton.click();
            await page.waitForTimeout(500);

            // Verify detailed view loaded
            expect(await page.locator('text=RLHF, text=Evolution, text=Performance').count()).toBeGreaterThan(0);
        }
    });

    test('should display charts and visualizations', async ({ page }) => {
        // Wait for charts to render
        await page.waitForTimeout(2000);

        // Look for SVG charts (Recharts renders as SVG)
        const charts = page.locator('svg');
        const chartCount = await charts.count();

        // Should have at least one chart
        expect(chartCount).toBeGreaterThan(0);
    });
});

test.describe('Feedback Analytics', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
    });

    test('should display feedback metrics after submission', async ({ page }) => {
        // Submit feedback via chat
        await page.click('text=Chat');
        await page.selectOption('.agent-dropdown', { index: 1 });
        await page.fill('.message-input', 'Test for analytics');
        await page.click('.send-button');

        await page.waitForSelector('.message-wrapper.agent', { timeout: 15000 });

        const agentMessage = page.locator('.message-wrapper.agent').first();
        await agentMessage.hover();
        await page.waitForTimeout(300);

        // Submit thumbs up
        await agentMessage.locator('.feedback-btn').first().click();

        // Navigate to analytics
        await page.click('text=Analytics');
        await page.waitForTimeout(2000);

        // Verify feedback count increased
        const feedbackMetric = page.locator('text=/Total Feedback|Feedback Score/i');
        await expect(feedbackMetric).toBeVisible({ timeout: 5000 });
    });
});

test.describe('Responsive Design', () => {
    test('should work on mobile viewport', async ({ page }) => {
        // Set mobile viewport
        await page.setViewportSize({ width: 375, height: 667 });

        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');

        // Verify main content is visible
        await expect(page.locator('text=Overview, text=Chat')).toBeVisible();
    });

    test('should work on tablet viewport', async ({ page }) => {
        // Set tablet viewport
        await page.setViewportSize({ width: 768, height: 1024 });

        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');

        // Navigate to chat
        await page.click('text=Chat');

        // Verify chat interface renders properly
        await expect(page.locator('.chat-interface')).toBeVisible();
    });
});
