// Playwright E2E test for Gap Analysis Bot
const { test, expect } = require('@playwright/test');

test('Bot responds to start and analyze', async ({ page }) => {
  await page.goto('http://127.0.0.1:3978/api/messages');
  // Health check
  const health = await page.textContent('body');
  expect(health).toContain('Bot is running');

  // Simulate POST message (requires API mocking or Teams emulator)
  // This is a placeholder for real bot E2E
});
