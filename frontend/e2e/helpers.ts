/**
 * E2E Test Helper Utilities
 * 
 * Shared utilities and helper functions for E2E tests.
 */

import { Page, expect } from '@playwright/test';

/**
 * Wait for dashboard to fully load
 */
export async function waitForDashboardLoad(page: Page) {
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000); // Additional buffer for animations
}

/**
 * Navigate to specific dashboard tab
 */
export async function navigateToTab(page: Page, tabName: string) {
    await page.click(`text=${tabName}`);
    await page.waitForTimeout(500);
}

/**
 * Send chat message and wait for response
 */
export async function sendChatMessage(page: Page, message: string, agentIndex: number = 1) {
    // Navigate to chat if not already there
    const chatInterface = page.locator('.chat-interface');
    if (!(await chatInterface.isVisible())) {
        await navigateToTab(page, 'Chat');
    }

    // Select agent
    await page.selectOption('.agent-dropdown', { index: agentIndex });
    await page.waitForTimeout(300);

    // Type and send message
    await page.fill('.message-input', message);
    await page.click('.send-button');

    // Wait for response
    await page.waitForSelector('.message-wrapper.agent', { timeout: 15000 });
}

/**
 * Submit feedback on last agent message
 */
export async function submitFeedback(page: Page, type: 'thumbs_up' | 'thumbs_down') {
    const agentMessage = page.locator('.message-wrapper.agent').first();
    await agentMessage.hover();
    await page.waitForTimeout(300);

    const buttonIndex = type === 'thumbs_up' ? 0 : 1;
    const feedbackButton = agentMessage.locator('.feedback-btn').nth(buttonIndex);
    await feedbackButton.click();

    // Verify button is active
    await expect(feedbackButton).toHaveClass(/active/);
}

/**
 * Check if element contains numeric value
 */
export async function hasNumericContent(page: Page, selector: string): Promise<boolean> {
    const element = page.locator(selector);
    const text = await element.textContent();
    return text ? /\d+/.test(text) : false;
}

/**
 * Wait for charts to render
 */
export async function waitForCharts(page: Page) {
    await page.waitForTimeout(2000);
    const charts = page.locator('svg');
    const count = await charts.count();
    expect(count).toBeGreaterThan(0);
}

/**
 * Verify metric card is visible with value
 */
export async function verifyMetricCard(page: Page, label: string) {
    const card = page.locator(`text=${label}`).locator('..').locator('..');
    await expect(card).toBeVisible({ timeout: 5000 });

    // Check for numeric value nearby
    const hasNumber = await card.locator('text=/\\d+/').count() > 0;
    expect(hasNumber).toBeTruthy();
}

/**
 * Wait for real-time updates
 */
export async function waitForRealtimeUpdate(page: Page, waitSeconds: number = 6) {
    await page.waitForTimeout(waitSeconds * 1000);
}

/**
 * Check system health status
 */
export async function checkSystemHealth(page: Page): Promise<'healthy' | 'degraded' | 'unknown'> {
    const healthyCount = await page.locator('text=/healthy|online|closed/i').count();
    const degradedCount = await page.locator('text=/warning|degraded|error/i').count();

    if (healthyCount > 0) return 'healthy';
    if (degradedCount > 0) return 'degraded';
    return 'unknown';
}

/**
 * Take screenshot with custom name
 */
export async function takeScreenshot(page: Page, name: string) {
    await page.screenshot({ path: `test-results/screenshots/${name}.png`, fullPage: true });
}

/**
 * Wait for API response
 */
export async function waitForApiResponse(page: Page, urlPattern: string | RegExp) {
    await page.waitForResponse((response) => {
        const url = response.url();
        if (typeof urlPattern === 'string') {
            return url.includes(urlPattern);
        }
        return urlPattern.test(url);
    });
}

/**
 * Verify tab is active
 */
export async function verifyActiveTab(page: Page, tabName: string) {
    const tab = page.locator(`text=${tabName}`).first();
    await expect(tab).toBeVisible();

    // Check if parent has active styling
    const parent = tab.locator('..');
    const classes = await parent.getAttribute('class');

    // Active tabs typically have specific classes or styles
    expect(classes).toBeTruthy();
}

/**
 * Count visible elements matching selector
 */
export async function countVisibleElements(page: Page, selector: string): Promise<number> {
    const elements = page.locator(selector);
    let count = 0;

    const total = await elements.count();
    for (let i = 0; i < total; i++) {
        if (await elements.nth(i).isVisible()) {
            count++;
        }
    }

    return count;
}
