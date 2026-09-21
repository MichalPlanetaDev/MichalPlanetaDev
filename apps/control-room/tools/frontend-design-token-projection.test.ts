// @vitest-environment node

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, test } from "vitest";

import {
  loadDesignTokenSource,
  parseDesignTokenSource,
  resolveSemanticDesignTokens,
} from "./design-token-source.ts";

const packageRoot = process.cwd();
const projectionModulePath = resolve(
  packageRoot,
  "tools/frontend-design-token-projection.ts",
);
const repositoryTokenPath = resolve(
  packageRoot,
  "../../profile/design-tokens.json",
);
const committedCssPath = resolve(
  packageRoot,
  "src/generated/design-tokens.css",
);
const committedTypescriptPath = resolve(
  packageRoot,
  "src/generated/design-tokens.ts",
);
const acceptedFingerprint =
  "7a644c039fe18880d03cd25100584136c87e52f7ffffcf512b2e9a24441edd3b";

type MutableRecord = Record<string, unknown>;

async function projectionModule() {
  expect(
    existsSync(projectionModulePath),
    "frontend-design-token-projection.ts must exist",
  ).toBe(true);

  if (!existsSync(projectionModulePath)) {
    throw new Error("frontend-design-token-projection.ts must exist");
  }

  return import("./frontend-design-token-projection.ts");
}

function repositoryDocument(): MutableRecord {
  return JSON.parse(
    readFileSync(repositoryTokenPath, "utf8"),
  ) as MutableRecord;
}

function objectAt(source: MutableRecord, ...path: string[]): MutableRecord {
  let current: unknown = source;

  for (const segment of path) {
    current = (current as MutableRecord)[segment];
  }

  return current as MutableRecord;
}

async function repositoryTokens() {
  const { projectFrontendDesignTokens } = await projectionModule();
  return projectFrontendDesignTokens(
    resolveSemanticDesignTokens(loadDesignTokenSource(repositoryTokenPath)),
  );
}

describe("frontend design-token projection", () => {
  test("resolves semantic roles once with raw source identity", async () => {
    const tokens = await repositoryTokens();

    expect(tokens.semantic.surface?.canvas).toMatchObject({
      kind: "color",
      sourceTokenId: "background.void",
      value: "#05080d",
    });
    expect(tokens.semantic.spacing?.section).toMatchObject({
      kind: "length",
      sourceTokenId: "layout.sectionGap",
      value: 56,
    });
  });

  test("preserves the accepted stable SHA-256 fingerprint", async () => {
    const first = await repositoryTokens();
    const second = await repositoryTokens();

    expect(first.fingerprint).toMatch(/^[0-9a-f]{64}$/);
    expect(first.fingerprint).toBe(acceptedFingerprint);
    expect(second.fingerprint).toBe(first.fingerprint);
  });

  test("fingerprint changes when resolved token content changes", async () => {
    const { projectFrontendDesignTokens } = await projectionModule();
    const document = repositoryDocument();
    objectAt(document, "palette", "accent").critical = "#e36d73";
    const changed = projectFrontendDesignTokens(
      resolveSemanticDesignTokens(parseDesignTokenSource(document)),
    );

    expect(changed.fingerprint).not.toBe(acceptedFingerprint);
  });

  test("CSS uses explicit units and resolved semantic names", async () => {
    const { renderDesignTokenCss } = await projectionModule();
    const css = renderDesignTokenCss(await repositoryTokens());

    expect(css).toContain("--cr-surface-canvas: #05080d;");
    expect(css).toContain("--cr-spacing-section: 3.5rem;");
    expect(css).toContain("--cr-motion-fast: 120ms;");
    expect(css).toContain("--cr-stroke-hairline: 1px;");
    expect(css).toContain(
      '--cr-font-technical: "SFMono-Regular", Consolas, "Liberation Mono", monospace;',
    );
    expect(css).not.toContain("semantic.surface.canvas");
  });

  test("CSS metadata is deterministic and contains no timestamp", async () => {
    const { renderDesignTokenCss } = await projectionModule();
    const css = renderDesignTokenCss(await repositoryTokens());

    expect(css).toContain("/* schema-version: 2 */");
    expect(css).toContain("/* theme-id: planetary-observatory */");
    expect(css).toContain(`/* fingerprint: ${acceptedFingerprint} */`);
    expect(css).not.toMatch(/20\d{2}-\d{2}-\d{2}/);
  });

  test("TypeScript rendering is readonly resolved literal data", async () => {
    const { renderDesignTokenTypescript } = await projectionModule();
    const document = renderDesignTokenTypescript(await repositoryTokens());

    expect(document).toContain("export const designTokens =");
    expect(document).toContain(`fingerprint: "${acceptedFingerprint}"`);
    expect(document).toContain('"canvas": "#05080d"');
    expect(document).toContain('"section": "3.5rem"');
    expect(document).toContain("} as const;");
    expect(document).toContain("export type SemanticDesignTokens");
    expect(document).not.toContain("resolve");
  });

  test("CSS custom-property names are unique", async () => {
    const { renderDesignTokenCss } = await projectionModule();
    const css = renderDesignTokenCss(await repositoryTokens());
    const names = [
      ...css.matchAll(/^\s*(--cr-[a-z0-9-]+):/gm),
    ].map((match) => match[1]);

    expect(names.length).toBeGreaterThan(0);
    expect(new Set(names).size).toBe(names.length);
  });

  test("rendering is byte-stable and equals both committed artifacts", async () => {
    const {
      renderDesignTokenCss,
      renderDesignTokenTypescript,
    } = await projectionModule();
    const tokens = await repositoryTokens();
    const firstCss = renderDesignTokenCss(tokens);
    const secondCss = renderDesignTokenCss(tokens);
    const firstTypescript = renderDesignTokenTypescript(tokens);
    const secondTypescript = renderDesignTokenTypescript(tokens);

    expect(firstCss).toBe(secondCss);
    expect(firstTypescript).toBe(secondTypescript);
    expect(firstCss).toBe(readFileSync(committedCssPath, "utf8"));
    expect(firstTypescript).toBe(
      readFileSync(committedTypescriptPath, "utf8"),
    );
  });
});
