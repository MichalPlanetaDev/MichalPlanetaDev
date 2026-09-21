import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, test } from "vitest";

import { designTokens } from "@/generated/design-tokens";

const packageRoot = process.cwd();
const cssPath = resolve(
  packageRoot,
  "src/generated/design-tokens.css",
);
const layoutPath = resolve(packageRoot, "src/app/layout.tsx");

const css = readFileSync(cssPath, "utf8");
const layoutSource = readFileSync(layoutPath, "utf8");

function cssVariable(name: `--cr-${string}`): string {
  const match = css.match(
    new RegExp(`^\\s*${name}:\\s*([^;]+);$`, "m"),
  );

  expect(match, `${name} must exist`).not.toBeNull();

  return match?.[1]?.trim() ?? "";
}

describe("generated design-token contract", () => {
  test("CSS and TypeScript expose one resolved design contract", () => {
    expect(cssVariable("--cr-surface-canvas")).toBe(
      designTokens.semantic.surface.canvas,
    );
    expect(cssVariable("--cr-signal-primary")).toBe(
      designTokens.semantic.signal.primary,
    );
    expect(cssVariable("--cr-spacing-section")).toBe(
      designTokens.semantic.spacing.section,
    );
    expect(cssVariable("--cr-font-technical")).toBe(
      designTokens.semantic.font.technical,
    );
    expect(cssVariable("--cr-motion-fast")).toBe(
      designTokens.semantic.motion.fast,
    );
    expect(css).toContain(
      `/* schema-version: ${designTokens.meta.schemaVersion} */`,
    );
    expect(css).toContain(
      `/* theme-id: ${designTokens.meta.themeId} */`,
    );
    expect(css).toContain(
      `/* fingerprint: ${designTokens.meta.fingerprint} */`,
    );
  });

  test("application root imports generated CSS before authored CSS", () => {
    const generatedImport =
      'import "@/generated/design-tokens.css";';
    const authoredImport = 'import "./globals.css";';

    expect(layoutSource).toContain(generatedImport);
    expect(layoutSource.indexOf(generatedImport)).toBeLessThan(
      layoutSource.indexOf(authoredImport),
    );
  });
});
