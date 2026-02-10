/**
 * E2E Test: Chat Interface and Feedback Flow
 * 
 * Tests the complete user flow:
 * 1. Navigate to dashboard
 * 2. Open chat interface
 * 3. Send message to agent
 * 4. Receive response
 * 5. Submit feedback (thumbs up/down)
 * 6. Verify feedback recorded
 */

import { test, expect } from '@playwright/test';

test.describe('Chat Interface', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to dashboard
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
    });

    test('should load chat interface', async ({ page }) => {
        // Click on Chat tab
        await page.click('text=Chat');

        // Verify chat interface is visible
        await expect(page.locator('.chat-interface')).toBeVisible();

        // Verify agent selector is present
        await expect(page.locator('.agent-dropdown')).toBeVisible();
    });

    test('should send message and receive response', async ({ page }) => {
        // Navigate to chat
        await page.click('text=Chat');

        // Select an agent
        await page.selectOption('.agent-dropdown', { index: 1 });

        // Wait a bit for selection
        await page.waitForTimeout(500);

        // Type message
        const messageInput = page.locator('.message-input');
        await messageInput.fill('What is machine learning?');

        // Send message
        await page.click('.send-button');

        // Wait for agent response (with timeout)
        await expect(page.locator('.message-wrapper.agent')).toBeVisible({ timeout: 15000 });

        // Verify message appears in chat
        await expect(page.locator('text=What is machine learning?')).toBeVisible();
    });

    test('should submit thumbs up feedback', async ({ page }) => {
        // Navigate to chat
        await page.click('text=Chat');

        // Select agent and send message
        await page.selectOption('.agent-dropdown', { index: 1 });
        await page.fill('.message-input', 'Test message');
        await page.click('.send-button');

        // Wait for response
        await page.waitForSelector('.message-wrapper.agent', { timeout: 15000 });

        // Hover over agent message to reveal feedback buttons
        const agentMessage = page.locator('.message-wrapper.agent').first();
        await agentMessage.hover();

        // Wait for feedback buttons to appear
        await page.waitForTimeout(300);

        // Click thumbs up
        const thumbsUpButton = agentMessage.locator('.feedback-btn').first();
        await thumbsUpButton.click();

        // Verify button is active
        await expect(thumbsUpButton).toHaveClass(/active/);
    });

    test('should submit thumbs down feedback', async ({ page }) => {
        // Navigate to chat
        await page.click('text=Chat');

        // Select agent and send message
        await page.selectOption('.agent-dropdown', { index: 1 });
        await page.fill('.message-input', 'Test message for negative feedback');
        await page.click('.send-button');

        // Wait for response
        await page.waitForSelector('.message-wrapper.agent', { timeout: 15000 });

        // Hover and click thumbs down
        const agentMessage = page.locator('.message-wrapper.agent').first();
        await agentMessage.hover();
        await page.waitForTimeout(300);

        const thumbsDownButton = agentMessage.locator('.feedback-btn').nth(1);
        await thumbsDownButton.click();

        // Verify button is active
        await expect(thumbsDownButton).toHaveClass(/active/);
    });

    test('should toggle feedback selection', async ({ page }) => {
        // Navigate to chat and send message
        await page.click('text=Chat');
        await page.selectOption('.agent-dropdown', { index: 1 });
        await page.fill('.message-input', 'Toggle test');
        await page.click('.send-button');

        await page.waitForSelector('.message-wrapper.agent', { timeout: 15000 });

        const agentMessage = page.locator('.message-wrapper.agent').first();
        await agentMessage.hover();
        await page.waitForTimeout(300);

        const thumbsUpButton = agentMessage.locator('.feedback-btn').first();

        // Click thumbs up
        await thumbsUpButton.click();
        await expect(thumbsUpButton).toHaveClass(/active/);

        // Click again to toggle off
        await thumbsUpButton.click();
        await expect(thumbsUpButton).not.toHaveClass(/active/);
    });
});

test.describe('Chat Interface - Edge Cases', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/dashboard');
        await page.click('text=Chat');
    });

    test('should disable send button when no agent selected', async ({ page }) => {
        // Verify send button is disabled
        const sendButton = page.locator('.send-button');
        await expect(sendButton).toBeDisabled();
    });

    test('should disable send button with empty message', async ({ page }) => {
        // Select agent
        await page.selectOption('.agent-dropdown', { index: 1 });

        // Verify send button is disabled when input is empty
        const sendButton = page.locator('.send-button');
        await expect(sendButton).toBeDisabled();
    });

    test('should handle multiple messages in conversation', async ({ page }) => {
        await page.selectOption('.agent-dropdown', { index: 1 });

        // Send first message
        await page.fill('.message-input', 'First question');
        await page.click('.send-button');
        await page.waitForSelector('.message-wrapper.agent', { timeout: 15000 });

        // Send second message
        await page.fill('.message-input', 'Second question');
        await page.click('.send-button');

        // Verify both messages appear
        await expect(page.locator('text=First question')).toBeVisible();
        await expect(page.locator('text=Second question')).toBeVisible();
    });
});
