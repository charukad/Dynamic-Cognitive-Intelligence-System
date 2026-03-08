import { expect, test } from '@playwright/test';

import { installChatApiMocks } from './support/chatApiMocks';

async function disableRealtimeTransport(page: import('@playwright/test').Page) {
  await page.addInitScript(() => {
    class DisabledWebSocket {
      static CONNECTING = 0;
      static OPEN = 1;
      static CLOSING = 2;
      static CLOSED = 3;

      readyState = DisabledWebSocket.CLOSED;
      onopen: ((event: Event) => void) | null = null;
      onclose: ((event: CloseEvent) => void) | null = null;
      onerror: ((event: Event) => void) | null = null;
      onmessage: ((event: MessageEvent<string>) => void) | null = null;

      constructor() {
        queueMicrotask(() => {
          this.onerror?.(new Event('error'));
          this.onclose?.(new CloseEvent('close'));
        });
      }

      send() { }

      close() {
        this.readyState = DisabledWebSocket.CLOSED;
      }
    }

    Object.defineProperty(window, 'WebSocket', {
      configurable: true,
      writable: true,
      value: DisabledWebSocket,
    });
  });
}

test.describe('Chat Interface', () => {
  test('sends messages, records feedback, and preserves conversation continuity', async ({ page }) => {
    const state = await installChatApiMocks(page);
    await disableRealtimeTransport(page);

    await page.goto('/chat');
    const chat = page.locator('.chat-interface').first();
    await expect(chat).toBeVisible();
    await expect(chat.getByRole('heading', { name: 'Living AI Organization Interface' }).first()).toBeVisible();
    await expect(chat.getByRole('combobox', { name: 'Select active agent' }).first()).toBeVisible();

    await chat.getByRole('combobox', { name: 'Select active agent' }).first().selectOption('designer');
    await chat.getByRole('textbox', { name: 'Message composer' }).first().fill('Design a cleaner navigation system');
    await chat.getByRole('textbox', { name: 'Message composer' }).first().press('Enter');

    await expect(chat.getByText('Design a cleaner navigation system').first()).toBeVisible();
    await expect(chat.getByText('Designer handled: Design a cleaner navigation system').first()).toBeVisible();

    await chat.getByRole('button', { name: 'Mark assistant response as helpful' }).first().evaluate((element) => {
      (element as HTMLButtonElement).click();
    });
    await expect
      .poll(() => state.feedbackRequests.length)
      .toBe(1);
    expect(state.feedbackRequests[0]?.feedback_type).toBe('thumbs_up');

    await chat.getByRole('textbox', { name: 'Message composer' }).first().fill('Add a stronger dashboard hierarchy');
    await chat.getByRole('textbox', { name: 'Message composer' }).first().press('Enter');

    await expect(chat.getByText('Designer handled: Add a stronger dashboard hierarchy').first()).toBeVisible();
    await expect
      .poll(() => state.messagesBySession['session-1']?.length || 0)
      .toBe(4);
  });

  test('loads the canonical room, dag, and replay views', async ({ page }) => {
    await installChatApiMocks(page);
    await disableRealtimeTransport(page);

    await page.goto('/chat');
    const chat = page.locator('.chat-interface').first();

    const strategyButton = chat.getByRole('button', { name: /strategy center/i }).first();
    await strategyButton.scrollIntoViewIfNeeded();
    await strategyButton.evaluate((element) => {
      (element as HTMLButtonElement).click();
    });
    await expect(chat.getByRole('dialog', { name: /strategy center detail panel/i }).first()).toBeVisible();
    await expect(chat.getByText('Strategy Center is preparing the latest route plan.').first()).toBeVisible();

    await chat.getByRole('tab', { name: 'Task DAG Viewer' }).first().evaluate((element) => {
      (element as HTMLButtonElement).click();
    });
    await expect(chat.getByText('Designer completed the latest delivery path.').first()).toBeVisible();
    await chat.getByRole('button', { name: /delivery and validation/i }).first().evaluate((element) => {
      (element as HTMLButtonElement).click();
    });
    await expect(chat.getByText('demo-model').first()).toBeVisible();

    await chat.getByRole('tab', { name: 'Replay' }).first().evaluate((element) => {
      (element as HTMLButtonElement).click();
    });
    await expect(chat.getByLabel('Replay frame scrubber').first()).toBeVisible();
    await chat.getByRole('button', { name: 'Step forward in replay' }).first().evaluate((element) => {
      (element as HTMLButtonElement).click();
    });
    await expect(chat.getByText(/front desk/i).first()).toBeVisible();
  });
});
