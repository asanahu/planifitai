import { test, expect, Page } from '@playwright/test';
import './test-setup';

const login = async (page: Page) => {
  await page.goto('/login');
  await page.getByPlaceholder('Email').fill('demo@demo.com');
  await page.getByPlaceholder('Password').fill('password');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/today|onboarding/);
};

test('today page renders KPI cards', async ({ page }) => {
  await login(page);
  await page.goto('/today');
  await expect(page.getByText('Sesiones semana')).toBeVisible();
  await expect(page.getByText('Adherencia')).toBeVisible();
  await expect(page.getByText('Meta kcal hoy')).toBeVisible();
});