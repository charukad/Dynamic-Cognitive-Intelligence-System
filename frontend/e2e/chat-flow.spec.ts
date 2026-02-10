import { test, expect } from '@playwright/test';

test.describe('Chat Flow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should navigate to Neural Link chat', async ({ page }) => {
        // Find and click the Neural Link navigation item
        await page.getByRole('link', { name: /neural.*link/i }).click();

        // Wait for navigation
        await page.waitForLoadState('networkidle');

        // Verify we're on the chat page
        await expect(page.getByText(/neural.*link/i)).toBeVisible();
        await expect(page.getByPlaceholder(/transmit.*command/i)).toBeVisible();
    });

    test('should send a message and display it', async ({ page }) => {
        // Navigate to chat
        await page.getByRole('link', { name: /neural.*link/i }).click();
        await page.waitForLoadState('networkidle');

        // Type a message
        const messageInput = page.getByPlaceholder(/transmit.*command/i);
        await messageInput.fill('Hello, agents!');

        // Submit the message
        await page.getByRole('button', { name: /send/i }).click();

        // Verify message appears in chat
        await expect(page.getByText('Hello, agents!')).toBeVisible();

        // Verify input is cleared
        await expect(messageInput).toHaveValue('');
    });

    test('should display agent response after user message', async ({ page }) => {
        // Navigate to chat
        await page.getByRole('link', { name: /neural.*link/i }).click();
        await page.waitForLoadState('networkidle');

        // Send a message
        await page.getByPlaceholder(/transmit.*command/i).fill('Test message');
        await page.getByRole('button', { name: /send/i }).click();

        // Wait for simulated agent response (1 second delay)
        await page.waitForTimeout(1500);

        // Verify agent response appears
        await expect(page.getByText(/logician/i)).toBeVisible();
        await expect(page.getByText(/analyzing.*input/i)).toBeVisible();
    });

    test('should show online status indicator', async ({ page }) => {
        await page.getByRole('link', { name: /neural.*link/i }).click();
        await page.waitForLoadState('networkidle');

        // Verify online status
        await expect(page.getByText(/online/i)).toBeVisible();
    });

    test('should display messages with timestamps', async ({ page }) => {
        await page.getByRole('link', { name: /neural.*link/i }).click();
        await page.waitForLoadState('networkidle');

        // Send a message
        await page.getByPlaceholder(/transmit.*command/i).fill('Check timestamp');
        await page.getByRole('button', { name: /send/i }).click();

        // Verify timestamp format (HH:MM)
        const timeRegex = /\d{1,2}:\d{2}/;
        await expect(page.getByText(timeRegex)).toBeVisible();
    });
});
