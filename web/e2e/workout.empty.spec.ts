import { test, expect, Page } from '@playwright/test';
import './test-setup';

const login = async (page: Page) => {
  await page.goto('/login');
  await page.getByPlaceholder('Email').fill('demo@demo.com');
  await page.getByPlaceholder('Password').fill('password');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/today|onboarding/);
};

test('workout page shows empty state CTA', async ({ page }) => {
  await login(page);
  await page.goto('/workout');
  await expect(page.getByText('No tienes rutina aún')).toBeVisible();
  await expect(page.getByRole('button', { name: /Usar plantilla por defecto/i })).toBeVisible();
});