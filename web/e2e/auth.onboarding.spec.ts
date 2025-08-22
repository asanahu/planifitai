import { test, expect } from '@playwright/test';
import './test-setup';

const demoEmail = 'demo@demo.com';
const demoPass = 'password';

test('demo login redirects to onboarding and can skip', async ({ page }) => {
  await page.goto('/login');
  await page.getByPlaceholder('Email').fill(demoEmail);
  await page.getByPlaceholder('Password').fill(demoPass);
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/onboarding/);
  await page.goto('/onboarding?skip=1');
  await expect(page).toHaveURL(/today/);
});