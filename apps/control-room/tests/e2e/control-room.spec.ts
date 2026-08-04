import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));

  expect(dimensions.scrollWidth).toBeLessThanOrEqual(
    dimensions.clientWidth,
  );
}

test("semantic shell exposes identity and primary routes", async ({
  page,
}) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "Michał Planeta",
    }),
  ).toBeVisible();

  await expect(page.locator("h1")).toHaveCount(1);
  await expect(page.locator("canvas")).toHaveCount(0);

  for (const label of [
    "Profile",
    "Projects",
    "Systems",
    "Evidence",
    "Contact",
  ]) {
    await expect(
      page.getByRole("link", {
        name: label,
        exact: true,
      }),
    ).toBeVisible();
  }

  await page.keyboard.press("Tab");
  const skipLink = page.getByRole("link", {
    name: "Skip to main content",
  });
  await expect(skipLink).toBeFocused();

  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();
});

test("content remains complete when WebGL is unavailable", async ({
  page,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "WebGLRenderingContext", {
      configurable: true,
      value: undefined,
    });
    Object.defineProperty(window, "WebGL2RenderingContext", {
      configurable: true,
      value: undefined,
    });
  });

  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "Projects as engineering systems",
    }),
  ).toBeVisible();

  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "Evidence before claims",
    }),
  ).toBeVisible();

  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "Inspect the work directly",
    }),
  ).toBeVisible();
});

for (const viewport of [
  { name: "tablet", width: 820, height: 1180 },
  { name: "mobile", width: 390, height: 844 },
]) {
  test(`${viewport.name} composition has no horizontal overflow`, async ({
    page,
  }) => {
    await page.setViewportSize({
      width: viewport.width,
      height: viewport.height,
    });
    await page.goto("/");

    await expectNoHorizontalOverflow(page);

    await expect(
      page.getByRole("heading", {
        level: 1,
        name: "Michał Planeta",
      }),
    ).toBeVisible();
  });
}

test("reduced motion preserves content and disables smooth scrolling", async ({
  page,
}) => {
  await page.emulateMedia({
    reducedMotion: "reduce",
  });
  await page.goto("/");

  const reducedMotionMatches = await page.evaluate(() =>
    window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  expect(reducedMotionMatches).toBe(true);

  const scrollBehavior = await page.locator("html").evaluate((element) =>
    getComputedStyle(element).scrollBehavior,
  );
  expect(scrollBehavior).toBe("auto");

  await expect(page.locator("#profile")).toBeVisible();
  await expect(page.locator("#projects")).toBeVisible();
  await expect(page.locator("#systems")).toBeVisible();
  await expect(page.locator("#evidence")).toBeVisible();
  await expect(page.locator("#contact")).toBeVisible();
});

test(
  "mobile navigation provides explicit touch targets",
  async ({ page }) => {
    await page.setViewportSize({
      width: 390,
      height: 844,
    });
    await page.goto("/");

    const targetHeights = await page
      .locator(".site-header nav a")
      .evaluateAll((links) =>
        links.map((link) =>
          link.getBoundingClientRect().height
        ),
      );

    expect(targetHeights).toHaveLength(5);

    for (const height of targetHeights) {
      expect(height).toBeGreaterThanOrEqual(44);
    }
  },
);
