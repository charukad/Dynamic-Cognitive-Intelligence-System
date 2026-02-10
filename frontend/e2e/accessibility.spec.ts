import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Tests', () => {
    test('homepage should not have accessibility violations', async ({ page }) => {
        await page.goto('/');

        const accessibilityScanResults = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .analyze();

        expect(accessibilityScanResults.violations).toEqual([]);
    });

    test('neural link chat should be accessible', async ({ page }) => {
        await page.goto('/');

        // Wait for page to load
        await page.waitForLoadState('networkidle');

        // Navigate to chat
        await page.getByRole('link', { name: /neural.*link/i }).click();
        await page.waitForLoadState('networkidle');

        const accessibilityScanResults = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa'])
            .analyze();

        expect(accessibilityScanResults.violations).toEqual([]);
    });

    test('keyboard navigation should work', async ({ page }) => {
        await page.goto('/');

        // Tab through interactive elements
        await page.keyboard.press('Tab');
        const firstFocusable = await page.evaluate(() => document.activeElement?.tagName);
        expect(firstFocusable).toBeTruthy();

        // Should be able to navigate to links
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        const currentElement = await page.evaluate(() => document.activeElement?.tagName);
        expect(['A', 'BUTTON']).toContain(currentElement);
    });

    test('all images should have alt text', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        const imagesWithoutAlt = await page.evaluate(() => {
            const images = Array.from(document.querySelectorAll('img'));
            return images.filter(img => !img.alt).length;
        });

        expect(imagesWithoutAlt).toBe(0);
    });

    test('proper heading hierarchy', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        const headings = await page.evaluate(() => {
            const h1s = document.querySelectorAll('h1').length;
            const headingLevels = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))
                .map(h => parseInt(h.tagName[1]));

            return { h1Count: h1s, levels: headingLevels };
        });

        // Should have exactly one h1
        expect(headings.h1Count).toBe(1);

        // Headings should not skip levels
        for (let i = 1; i < headings.levels.length; i++) {
            const diff = headings.levels[i] - headings.levels[i - 1];
            expect(diff).toBeLessThanOrEqual(1);
        }
    });

    test('color contrast meets WCAG AA standards', async ({ page }) => {
        await page.goto('/');

        const accessibilityScanResults = await new AxeBuilder({ page })
            .withTags(['wcag2aa'])
            .include(['button', 'a', 'p', 'h1', 'h2', 'h3'])
            .analyze();

        const colorContrastViolations = accessibilityScanResults.violations
            .filter(v => v.id === 'color-contrast');

        expect(colorContrastViolations).toEqual([]);
    });

    test('form inputs should have labels', async ({ page }) => {
        await page.goto('/');

        // Navigate to a page with forms (chat interface)
        await page.getByRole('link', { name: /neural.*link/i }).click();
        await page.waitForLoadState('networkidle');

        const accessibilityScanResults = await new AxeBuilder({ page })
            .withTags(['wcag2a'])
            .analyze();

        const labelViolations = accessibilityScanResults.violations
            .filter(v => v.id === 'label');

        expect(labelViolations).toEqual([]);
    });

    test('landmarks should be properly defined', async ({ page }) => {
        await page.goto('/');

        const landmarks = await page.evaluate(() => {
            return {
                main: document.querySelectorAll('main').length,
                nav: document.querySelectorAll('nav').length,
                header: document.querySelectorAll('header').length,
            };
        });

        // Should have at least one main landmark
        expect(landmarks.main).toBeGreaterThanOrEqual(1);
    });
});
