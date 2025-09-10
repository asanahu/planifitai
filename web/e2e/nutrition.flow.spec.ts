import { test, expect, Page } from '@playwright/test';
import './test-setup';

const login = async (page: Page) => {
  await page.goto('/login');
  await page.getByPlaceholder('Email').fill('demo@demo.com');
  await page.getByPlaceholder('Password').fill('password');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/today|onboarding/);
};

test('nutrition page shows empty state', async ({ page }) => {
  await login(page);
  await page.goto('/nutrition/today');
  await expect(page.getByText('No hay comidas registradas')).toBeVisible();
  await expect(page.getByRole('button', { name: /Plan semanal|Ir al plan semanal/i })).toBeVisible();
});
