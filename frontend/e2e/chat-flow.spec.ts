import { expect, test } from '@playwright/test';

import {
  createMessage,
  createSession,
  installChatApiMocks,
} from './support/chatApiMocks';

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

test.describe('Chat Flow', () => {
  test('retries a failed HTTP send and eventually delivers the assistant response', async ({ page }) => {
    await installChatApiMocks(page, { sendFailuresRemaining: 1 });
    await disableRealtimeTransport(page);

    await page.goto('/chat');
    const chat = page.locator('.chat-interface').first();

    await chat.getByRole('combobox', { name: 'Select active agent' }).first().selectOption('designer');
    await chat.getByRole('textbox', { name: 'Message composer' }).first().fill('Retry this request');
    await chat.getByRole('textbox', { name: 'Message composer' }).first().press('Enter');

    await expect(chat.getByText('Failed to send message. You can retry it.').first()).toBeVisible();
    await chat.getByRole('button', { name: 'Retry failed message' }).first().evaluate((element) => {
      (element as HTMLButtonElement).click();
    });

    await expect(chat.getByText('Designer handled: Retry this request').first()).toBeVisible();
    await expect(chat.getByText('Failed to send message. You can retry it.')).toHaveCount(0);
  });

  test('switches sessions and deletes the active session through the canonical API', async ({ page }) => {
    const sessionA = createSession('session-a', 'Architecture Review', 'designer', 1);
    const sessionB = createSession('session-b', 'Bug Triage', 'coder', 2);
    const state = await installChatApiMocks(page, {
      sessions: [sessionB, sessionA],
      messagesBySession: {
        'session-a': [
          createMessage({
            id: 'msg-a1',
            sessionId: 'session-a',
            sequenceNumber: 1,
            sender: 'user',
            content: 'Review the architecture tradeoffs',
            agentId: 'designer',
            agentName: 'Designer',
            minute: 3,
          }),
          createMessage({
            id: 'msg-a2',
            sessionId: 'session-a',
            sequenceNumber: 2,
            sender: 'agent',
            content: 'Designer handled: Review the architecture tradeoffs',
            agentId: 'designer',
            agentName: 'Designer',
            minute: 4,
          }),
        ],
        'session-b': [
          createMessage({
            id: 'msg-b1',
            sessionId: 'session-b',
            sequenceNumber: 1,
            sender: 'user',
            content: 'Fix the failing retry logic',
            agentId: 'coder',
            agentName: 'Coder',
            minute: 5,
          }),
          createMessage({
            id: 'msg-b2',
            sessionId: 'session-b',
            sequenceNumber: 2,
            sender: 'agent',
            content: 'Coder handled: Fix the failing retry logic',
            agentId: 'coder',
            agentName: 'Coder',
            minute: 6,
          }),
        ],
      },
    });
    await disableRealtimeTransport(page);

    await page.goto('/chat');
    const chat = page.locator('.chat-interface').first();

    await page.getByRole('button', { name: 'Open conversation Architecture Review' }).first().click();
    await expect(chat.getByText('Designer handled: Review the architecture tradeoffs').first()).toBeVisible();

    page.once('dialog', (dialog) => dialog.accept());
    await page.getByRole('button', { name: 'Delete conversation Architecture Review' }).first().click();

    await expect(page.getByRole('button', { name: 'Open conversation Architecture Review' })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Open conversation Bug Triage' }).first()).toBeVisible();
    await expect
      .poll(() => state.sessions.some((session) => session.id === 'session-a'))
      .toBe(false);
  });
});
