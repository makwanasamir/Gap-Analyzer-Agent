// Playwright config for E2E bot testing
// See https://playwright.dev/docs/test-configuration

module.exports = {
  testDir: './e2e',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: 'http://127.0.0.1:3978',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
};
