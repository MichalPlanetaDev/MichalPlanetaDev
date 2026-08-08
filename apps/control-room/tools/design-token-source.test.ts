// @vitest-environment node

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, test } from "vitest";

const packageRoot = process.cwd();
const sourceModulePath = resolve(packageRoot, "tools/design-token-source.ts");
const repositoryTokenPath = resolve(
  packageRoot,
  "../../profile/design-tokens.json",
);

type MutableRecord = Record<string, unknown>;
type TokenModule = typeof import("./design-token-source.ts");

async function tokenModule(): Promise<TokenModule> {
  expect(
    existsSync(sourceModulePath),
    "design-token-source.ts must exist",
  ).toBe(true);

  if (!existsSync(sourceModulePath)) {
    throw new Error("design-token-source.ts must exist");
  }

  return import("./design-token-source.ts");
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

function arrayAt(source: MutableRecord, ...path: string[]): unknown[] {
  let current: unknown = source;

  for (const segment of path) {
    current = (current as MutableRecord)[segment];
  }

  return current as unknown[];
}

async function resolveDocument(document: MutableRecord) {
  const { parseDesignTokenSource, resolveSemanticDesignTokens } =
    await tokenModule();
  return resolveSemanticDesignTokens(parseDesignTokenSource(document));
}

async function expectSourceFailure(
  mutate: (document: MutableRecord) => void,
  message: string | RegExp,
): Promise<void> {
  const { parseDesignTokenSource, resolveSemanticDesignTokens } =
    await tokenModule();
  const document = repositoryDocument();
  mutate(document);

  expect(() =>
    resolveSemanticDesignTokens(parseDesignTokenSource(document)),
  ).toThrow(message);
}

describe("authored design tokens", () => {
  test("loads the repository contract with verified contrast and semantic roles", async () => {
    const { loadDesignTokenSource, resolveSemanticDesignTokens } =
      await tokenModule();
    const source = loadDesignTokenSource(repositoryTokenPath);
    const contract = resolveSemanticDesignTokens(source);
    const colorCount = Object.values(source.palette).reduce(
      (count, group) => count + Object.keys(group).length,
      0,
    );

    expect(source.schemaVersion).toBe(2);
    expect(source.themeId).toBe("planetary-observatory");
    expect(colorCount).toBe(14);
    expect(source.typography.sizes).toHaveProperty("display", 58);
    expect(source.spacing.steps).toHaveLength(8);
    expect(source.rules.contrastPairs).toHaveLength(3);
    expect(
      source.rules.contrastPairs.every(
        (pair) => pair.actual >= pair.minimum,
      ),
    ).toBe(true);
    expect(contract.semantic.get("surface")?.get("canvas")).toMatchObject({
      reference: "background.void",
      resolvedTokenId: "background.void",
      kind: "color",
    });
    expect(contract.semantic.get("font")?.get("content")).toMatchObject({
      reference: "typography.fontStack",
      resolvedTokenId: "typography.fontStack",
      kind: "font-stack",
    });
  });

  test("resolves semantic reference chains to raw tokens", async () => {
    const document = repositoryDocument();
    objectAt(document, "semantic", "surface").canvas =
      "semantic.surface.depth";

    const contract = await resolveDocument(document);

    expect(contract.semantic.get("surface")?.get("canvas")).toMatchObject({
      reference: "semantic.surface.depth",
      resolvedTokenId: "background.deep",
      kind: "color",
    });
  });

  test("identifies the immediate owner of nested unknown references", async () => {
    await expectSourceFailure(
      (document) => {
        const surface = objectAt(document, "semantic", "surface");
        surface.canvas = "semantic.surface.depth";
        surface.depth = "background.missing";
      },
      "semantic.surface.depth references unknown token background.missing",
    );
  });

  test("rejects direct unknown semantic references", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "semantic", "surface").canvas =
          "background.missing";
      },
      "semantic.surface.canvas references unknown token background.missing",
    );
  });

  test("rejects semantic cycles with their path", async () => {
    await expectSourceFailure(
      (document) => {
        const surface = objectAt(document, "semantic", "surface");
        surface.canvas = "semantic.surface.elevated";
        surface.elevated = "semantic.surface.canvas";
      },
      "Semantic reference cycle: semantic.surface.canvas -> semantic.surface.elevated -> semantic.surface.canvas",
    );
  });

  test("rejects semantic kind mismatches", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "semantic", "spacing").section =
          "accent.signal";
      },
      "semantic.spacing.section requires a length token; accent.signal resolves to color",
    );
  });

  test("rejects unsupported top-level and nested fields", async () => {
    await expectSourceFailure(
      (document) => {
        document.unexpected = true;
      },
      "Design token source contains unsupported fields: unexpected",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "typography").unexpected = true;
      },
      "Design token source.typography contains unsupported fields: unexpected",
    );
  });

  test("rejects unsupported schema versions and theme identifiers", async () => {
    await expectSourceFailure(
      (document) => {
        document.schemaVersion = 3;
      },
      "Unsupported design token schemaVersion: 3",
    );
    await expectSourceFailure(
      (document) => {
        document.themeId = "Planetary Observatory";
      },
      "Design token source.themeId must use lowercase kebab-case",
    );
  });

  test("requires lowercase six-digit palette colors", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "palette", "background").void = "black";
      },
      "palette.background.void must use lowercase six-digit hex",
    );
  });

  test("requires unique non-empty font stacks", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "typography").fontStack = ["Inter", "Inter"];
      },
      "Design token source.typography.fontStack must contain unique values",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "typography").monoStack = [];
      },
      "Design token source.typography.monoStack must contain unique values",
    );
  });

  test("requires descending type sizes and increasing type weights", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "typography", "sizes").title = 64;
      },
      "Typography sizes must be strictly descending",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "typography", "weights").medium = 300;
      },
      "Typography weights must be strictly increasing",
    );
  });

  test("requires finite numeric token values", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "typography", "tracking").heading = Number.NaN;
      },
      "Design token source.typography.tracking.heading must contain a finite number",
    );
  });

  test("requires positive aligned strictly increasing spacing steps", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "spacing").steps = [4, 8, 12, 16, 24, 32, 48, 48];
      },
      "Spacing steps must be strictly increasing",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "spacing").unit = 0;
      },
      "Spacing unit must be positive",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "spacing").steps = [4, 8, 12, 16, 24, 32, 48, 62];
      },
      "Spacing steps must start at and align to the unit",
    );
  });

  test("requires positive radii and strokes", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "radii").small = 0;
      },
      "Radii and strokes must be positive",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "strokes").hairline = 0;
      },
      "Radii and strokes must be positive",
    );
  });

  test("requires ordered bounded opacity values", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "opacity").muted = 0.1;
      },
      "Opacity values must be strictly increasing",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "opacity").strong = 1.2;
      },
      "Opacity values must be greater than zero and at most one",
    );
  });

  test("enforces the authored layout contract", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "layout").canvasWidth = 900;
      },
      "Layout canvasWidth must be between 960 and 1600",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "layout").columns = 10;
      },
      "Layout columns must equal 12",
    );
    await expectSourceFailure(
      (document) => {
        const layout = objectAt(document, "layout");
        layout.canvasWidth = 960;
        layout.safeInset = 480;
      },
      "Layout safeInset leaves no usable canvas width",
    );
  });

  test("enforces effect bounds", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "effects").glowBlur = 33;
      },
      "effects.glowBlur must be between zero and 32",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "effects").glowOpacity = 1.1;
      },
      "effects.glowOpacity must be between zero and one",
    );
  });

  test("requires ordered positive motion durations within one second", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "motion", "duration").standard = 100;
      },
      "Motion durations must be strictly increasing",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "motion", "duration").standard = 1200;
      },
      "Motion durations must be greater than zero and at most 1000 milliseconds",
    );
  });

  test("enforces motion density and corner-language policies", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "rules").motion = "ambient-loop";
      },
      "Unsupported motion policy: ambient-loop",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "rules").density = "dashboard";
      },
      "Unsupported density policy: dashboard",
    );
    await expectSourceFailure(
      (document) => {
        objectAt(document, "rules").cornerLanguage = "rounded";
      },
      "Unsupported corner language: rounded",
    );
  });

  test("rejects unresolved and duplicate contrast references", async () => {
    await expectSourceFailure(
      (document) => {
        const pairs = arrayAt(document, "rules", "contrastPairs") as MutableRecord[];
        pairs[0]!.foreground = "text.missing";
      },
      "Unknown contrast color: text.missing",
    );
    await expectSourceFailure(
      (document) => {
        const pairs = arrayAt(document, "rules", "contrastPairs") as MutableRecord[];
        pairs.push(structuredClone(pairs[0]!));
      },
      "Duplicate contrast pair: text.primary on background.void",
    );
  });

  test("requires finite bounded contrast minima and sufficient actual contrast", async () => {
    await expectSourceFailure(
      (document) => {
        const pairs = arrayAt(document, "rules", "contrastPairs") as MutableRecord[];
        pairs[0]!.minimum = Number.POSITIVE_INFINITY;
      },
      "Design token source.rules.contrastPairs[0].minimum must contain a finite number",
    );
    await expectSourceFailure(
      (document) => {
        const pairs = arrayAt(document, "rules", "contrastPairs") as MutableRecord[];
        pairs[0]!.minimum = 1;
      },
      "Design token source.rules.contrastPairs[0].minimum must be between one and 21",
    );
    await expectSourceFailure(
      (document) => {
        const palette = objectAt(document, "palette");
        objectAt(palette, "text").primary =
          objectAt(palette, "background").void;
      },
      /Contrast text\.primary on background\.void does not meet minimum 7\.0; actual 1\.000/,
    );
  });

  test("requires at least one contrast pair", async () => {
    await expectSourceFailure(
      (document) => {
        objectAt(document, "rules").contrastPairs = [];
      },
      "At least one contrast pair is required",
    );
  });
});
