import { expect, test } from "@playwright/test";
import type { Locator, Page } from "@playwright/test";

interface RgbColor {
  blue: number;
  green: number;
  red: number;
}

async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));

  expect(dimensions.scrollWidth).toBeLessThanOrEqual(
    dimensions.clientWidth,
  );
}

async function readOutline(
  locator: Locator,
): Promise<{
  color: string;
  style: string;
  width: number;
}> {
  return locator.evaluate((element) => {
    const style = getComputedStyle(element);

    return {
      color: style.outlineColor,
      style: style.outlineStyle,
      width: Number.parseFloat(style.outlineWidth),
    };
  });
}

function parseRgbColor(value: string): RgbColor {
  const channels = value.match(/\d+(?:\.\d+)?/g);

  if (!channels || channels.length < 3) {
    throw new Error(`Unsupported computed color: ${value}`);
  }

  return {
    red: Number(channels[0]) / 255,
    green: Number(channels[1]) / 255,
    blue: Number(channels[2]) / 255,
  };
}

function linearize(channel: number): number {
  if (channel <= 0.04045) {
    return channel / 12.92;
  }

  return ((channel + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(color: string): number {
  const { blue, green, red } = parseRgbColor(color);

  return (
    0.2126 * linearize(red) +
    0.7152 * linearize(green) +
    0.0722 * linearize(blue)
  );
}

function contrastRatio(
  foreground: string,
  background: string,
): number {
  const foregroundLuminance = relativeLuminance(foreground);
  const backgroundLuminance = relativeLuminance(background);
  const lighter = Math.max(
    foregroundLuminance,
    backgroundLuminance,
  );
  const darker = Math.min(
    foregroundLuminance,
    backgroundLuminance,
  );

  return (lighter + 0.05) / (darker + 0.05);
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

test("focus and runtime diagnostics remain visible and clean", async ({
  page,
}) => {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];

  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });
  page.on("pageerror", (error) => {
    pageErrors.push(error.message);
  });

  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.keyboard.press("Tab");

  const skipLink = page.getByRole("link", {
    name: "Skip to main content",
  });

  await expect(skipLink).toBeFocused();
  await expect
    .poll(async () => {
      const bounds = await skipLink.boundingBox();

      return bounds?.y ?? -1;
    })
    .toBeGreaterThanOrEqual(0);

  const skipOutline = await readOutline(skipLink);

  expect(skipOutline.style).not.toBe("none");
  expect(skipOutline.width).toBeGreaterThanOrEqual(2);

  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");

  const profileLink = page.getByRole("link", {
    name: "Profile",
    exact: true,
  });

  await expect(profileLink).toBeFocused();

  const profileOutline = await readOutline(profileLink);

  expect(profileOutline.style).not.toBe("none");
  expect(profileOutline.width).toBeGreaterThanOrEqual(2);
  expect(profileOutline.color).toBe(skipOutline.color);
  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("visitor-facing metadata maintains readable contrast", async ({
  page,
}) => {
  await page.goto("/");

  const pairs = await page.evaluate(() => {
    const heading = document.querySelector("h1");
    const heroSummary = document.querySelector(".hero-summary");
    const identityMetadata = document.querySelector(
      ".site-identity small",
    );
    const footer = document.querySelector("footer");

    if (
      !heading ||
      !heroSummary ||
      !identityMetadata ||
      !footer
    ) {
      throw new Error("Required contrast probe element is missing.");
    }

    const rootStyle = getComputedStyle(
      document.documentElement,
    );
    const colorProbe = document.createElement("span");

    colorProbe.style.color = rootStyle
      .getPropertyValue("--cr-surface-panel")
      .trim();
    document.body.append(colorProbe);

    const panelColor = getComputedStyle(colorProbe).color;

    colorProbe.remove();

    return {
      canvas: rootStyle.backgroundColor,
      footer: getComputedStyle(footer).color,
      identityMetadata: getComputedStyle(identityMetadata).color,
      panel: panelColor,
      primaryContent: getComputedStyle(heading).color,
      secondaryContent: getComputedStyle(heroSummary).color,
    };
  });

  expect(
    contrastRatio(pairs.primaryContent, pairs.canvas),
    "primary content on canvas",
  ).toBeGreaterThanOrEqual(7);

  expect(
    contrastRatio(pairs.secondaryContent, pairs.panel),
    "secondary content on panel",
  ).toBeGreaterThanOrEqual(4.5);

  expect(
    contrastRatio(pairs.identityMetadata, pairs.canvas),
    "header metadata on canvas",
  ).toBeGreaterThanOrEqual(4.5);

  expect(
    contrastRatio(pairs.footer, pairs.canvas),
    "footer metadata on canvas",
  ).toBeGreaterThanOrEqual(4.5);
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

  const scrollBehavior = await page.locator("html").evaluate(
    (element) => getComputedStyle(element).scrollBehavior,
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
        links.map((link) => link.getBoundingClientRect().height),
      );

    expect(targetHeights).toHaveLength(5);

    for (const height of targetHeights) {
      expect(height).toBeGreaterThanOrEqual(44);
    }
  },
);
