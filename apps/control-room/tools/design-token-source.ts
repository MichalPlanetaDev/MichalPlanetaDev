import { readFileSync } from "node:fs";

export type DesignTokenKind =
  | "color"
  | "font-stack"
  | "length"
  | "font-weight"
  | "tracking"
  | "opacity"
  | "number"
  | "duration";

export type DesignTokenValue = string | number | readonly string[];

export interface RawDesignToken {
  tokenId: string;
  kind: DesignTokenKind;
  value: DesignTokenValue;
}

export interface ResolvedSemanticToken {
  reference: string;
  resolvedTokenId: string;
  kind: DesignTokenKind;
}

export interface ContrastPair {
  foreground: string;
  background: string;
  minimum: number;
  actual: number;
}

export interface DesignTokenSource {
  schemaVersion: 2;
  themeId: string;
  palette: {
    background: Record<string, string>;
    text: Record<string, string>;
    accent: Record<string, string>;
    border: Record<string, string>;
  };
  typography: {
    fontStack: string[];
    monoStack: string[];
    sizes: Record<string, number>;
    weights: Record<string, number>;
    tracking: Record<string, number>;
  };
  spacing: {
    unit: number;
    steps: number[];
  };
  radii: Record<string, number>;
  strokes: Record<string, number>;
  opacity: Record<string, number>;
  layout: Record<string, number>;
  effects: Record<string, number>;
  motion: {
    duration: Record<string, number>;
  };
  semantic: Record<string, Record<string, string>>;
  rules: {
    motion: string;
    density: string;
    cornerLanguage: string;
    contrastPairs: ContrastPair[];
  };
}

export interface ResolvedDesignTokenContract {
  schemaVersion: 2;
  themeId: string;
  raw: ReadonlyMap<string, RawDesignToken>;
  semantic: ReadonlyMap<
    string,
    ReadonlyMap<string, ResolvedSemanticToken>
  >;
}

export class DesignTokenSourceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DesignTokenSourceError";
  }
}

type SourceObject = Record<string, unknown>;

const supportedSchemaVersion = 2 as const;
const identifierPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const colorPattern = /^#[0-9a-f]{6}$/;

const paletteGroups = {
  background: ["void", "deep", "panel", "panel-raised"],
  text: ["primary", "secondary", "muted"],
  accent: ["signal", "orbit", "warning", "critical", "success"],
  border: ["subtle", "strong"],
} as const;

const typeSizeIds = [
  "display",
  "title",
  "heading",
  "body",
  "label",
  "micro",
] as const;
const typeWeightIds = ["regular", "medium", "semibold", "bold"] as const;
const trackingIds = ["display", "heading", "label"] as const;
const radiusIds = ["small", "medium", "large", "pill"] as const;
const strokeIds = ["hairline", "emphasis"] as const;
const opacityIds = ["subtle", "muted", "secondary", "strong"] as const;
const layoutIds = [
  "canvasWidth",
  "safeInset",
  "columns",
  "gutter",
  "sectionGap",
] as const;
const effectIds = ["glowBlur", "glowOpacity"] as const;
const motionDurationIds = ["fast", "standard"] as const;

const semanticRoleKinds: Record<
  string,
  Readonly<Record<string, DesignTokenKind>>
> = {
  surface: {
    canvas: "color",
    depth: "color",
    panel: "color",
    elevated: "color",
  },
  content: {
    primary: "color",
    secondary: "color",
    muted: "color",
    inverse: "color",
  },
  signal: {
    primary: "color",
    secondary: "color",
    warning: "color",
    critical: "color",
    success: "color",
  },
  structure: {
    subtle: "color",
    strong: "color",
    focus: "color",
  },
  font: {
    content: "font-stack",
    technical: "font-stack",
  },
  typeSize: {
    display: "length",
    title: "length",
    heading: "length",
    body: "length",
    label: "length",
    micro: "length",
  },
  typeWeight: {
    regular: "font-weight",
    medium: "font-weight",
    semibold: "font-weight",
    bold: "font-weight",
  },
  tracking: {
    display: "tracking",
    heading: "tracking",
    label: "tracking",
  },
  spacing: {
    xs: "length",
    sm: "length",
    md: "length",
    lg: "length",
    xl: "length",
    "2xl": "length",
    "3xl": "length",
    "4xl": "length",
    section: "length",
    safeInset: "length",
    gutter: "length",
  },
  radius: {
    small: "length",
    medium: "length",
    large: "length",
    pill: "length",
  },
  stroke: {
    hairline: "length",
    emphasis: "length",
  },
  opacity: {
    subtle: "opacity",
    muted: "opacity",
    secondary: "opacity",
    strong: "opacity",
  },
  effect: {
    glowBlur: "length",
    glowOpacity: "opacity",
  },
  layout: {
    contentWidth: "length",
    columns: "number",
  },
  motion: {
    fast: "duration",
    standard: "duration",
  },
};

function requireObject(value: unknown, context: string): SourceObject {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new DesignTokenSourceError(
      `${context} must contain a JSON object`,
    );
  }

  return value as SourceObject;
}

function requireArray(value: unknown, context: string): unknown[] {
  if (!Array.isArray(value)) {
    throw new DesignTokenSourceError(
      `${context} must contain a JSON array`,
    );
  }

  return value;
}

function requireExactFields(
  source: SourceObject,
  expectedFields: readonly string[],
  context: string,
): void {
  const expected = new Set(expectedFields);
  const missing = expectedFields
    .filter((field) => !(field in source))
    .sort();
  const unsupported = Object.keys(source)
    .filter((field) => !expected.has(field))
    .sort();

  if (missing.length > 0) {
    throw new DesignTokenSourceError(
      `${context} is missing fields: ${missing.join(", ")}`,
    );
  }

  if (unsupported.length > 0) {
    throw new DesignTokenSourceError(
      `${context} contains unsupported fields: ${unsupported.join(", ")}`,
    );
  }
}

function requireText(
  source: SourceObject,
  field: string,
  context: string,
): string {
  const value = source[field];

  if (typeof value !== "string" || value.trim().length === 0) {
    throw new DesignTokenSourceError(
      `${context}.${field} must contain a non-empty string`,
    );
  }

  return value.trim();
}

function requireInteger(
  source: SourceObject,
  field: string,
  context: string,
): number {
  const value = source[field];

  if (typeof value !== "number" || !Number.isInteger(value)) {
    throw new DesignTokenSourceError(
      `${context}.${field} must contain an integer`,
    );
  }

  return value;
}

function requireFiniteNumber(value: unknown, context: string): number {
  if (typeof value !== "number") {
    throw new DesignTokenSourceError(`${context} must contain a number`);
  }

  if (!Number.isFinite(value)) {
    throw new DesignTokenSourceError(
      `${context} must contain a finite number`,
    );
  }

  return value;
}

function requireNumber(
  source: SourceObject,
  field: string,
  context: string,
): number {
  return requireFiniteNumber(source[field], `${context}.${field}`);
}

function parseNumericGroup(
  value: unknown,
  identifiers: readonly string[],
  context: string,
): Record<string, number> {
  const source = requireObject(value, context);
  requireExactFields(source, identifiers, context);

  const result: Record<string, number> = {};

  for (const identifier of identifiers) {
    result[identifier] = requireFiniteNumber(
      source[identifier],
      `${context}.${identifier}`,
    );
  }

  return result;
}

function parseFontStack(value: unknown, context: string): string[] {
  const values = requireArray(value, context);
  const stack = values.map((font, index) => {
    if (typeof font !== "string" || font.trim().length === 0) {
      throw new DesignTokenSourceError(
        `${context}[${index}] must contain a non-empty string`,
      );
    }

    return font.trim();
  });

  if (stack.length === 0 || new Set(stack).size !== stack.length) {
    throw new DesignTokenSourceError(
      `${context} must contain unique values`,
    );
  }

  return stack;
}

function requireStrictOrder(
  values: readonly number[],
  descending: boolean,
  context: string,
): void {
  for (let index = 0; index < values.length - 1; index += 1) {
    const left = values[index]!;
    const right = values[index + 1]!;
    const valid = descending ? left > right : left < right;

    if (!valid) {
      const direction = descending ? "descending" : "increasing";
      throw new DesignTokenSourceError(
        `${context} must be strictly ${direction}`,
      );
    }
  }
}

function colorChannel(value: number): number {
  const normalized = value / 255;
  return normalized <= 0.04045
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4;
}

function luminance(color: string): number {
  const red = Number.parseInt(color.slice(1, 3), 16);
  const green = Number.parseInt(color.slice(3, 5), 16);
  const blue = Number.parseInt(color.slice(5, 7), 16);

  return (
    0.2126 * colorChannel(red) +
    0.7152 * colorChannel(green) +
    0.0722 * colorChannel(blue)
  );
}

function contrastRatio(foreground: string, background: string): number {
  const first = luminance(foreground);
  const second = luminance(background);
  const lighter = Math.max(first, second);
  const darker = Math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}

function parsePalette(value: unknown): DesignTokenSource["palette"] {
  const palette = requireObject(value, "Design token source.palette");
  requireExactFields(
    palette,
    Object.keys(paletteGroups),
    "Design token source.palette",
  );

  const result = {} as DesignTokenSource["palette"];

  for (const [groupId, tokenIds] of Object.entries(paletteGroups)) {
    const context = `Design token source.palette.${groupId}`;
    const group = requireObject(palette[groupId], context);
    requireExactFields(group, tokenIds, context);
    const parsed: Record<string, string> = {};

    for (const tokenId of tokenIds) {
      const color = requireText(group, tokenId, context);

      if (!colorPattern.test(color)) {
        throw new DesignTokenSourceError(
          `palette.${groupId}.${tokenId} must use lowercase six-digit hex`,
        );
      }

      parsed[tokenId] = color;
    }

    Object.assign(result, { [groupId]: parsed });
  }

  return result;
}

function parseTypography(value: unknown): DesignTokenSource["typography"] {
  const context = "Design token source.typography";
  const typography = requireObject(value, context);
  requireExactFields(
    typography,
    ["fontStack", "monoStack", "sizes", "weights", "tracking"],
    context,
  );

  const sizes = parseNumericGroup(
    typography.sizes,
    typeSizeIds,
    `${context}.sizes`,
  );
  const weights = parseNumericGroup(
    typography.weights,
    typeWeightIds,
    `${context}.weights`,
  );
  const tracking = parseNumericGroup(
    typography.tracking,
    trackingIds,
    `${context}.tracking`,
  );

  requireStrictOrder(
    typeSizeIds.map((id) => sizes[id]!),
    true,
    "Typography sizes",
  );
  requireStrictOrder(
    typeWeightIds.map((id) => weights[id]!),
    false,
    "Typography weights",
  );

  return {
    fontStack: parseFontStack(typography.fontStack, `${context}.fontStack`),
    monoStack: parseFontStack(typography.monoStack, `${context}.monoStack`),
    sizes,
    weights,
    tracking,
  };
}

function parseSpacing(value: unknown): DesignTokenSource["spacing"] {
  const context = "Design token source.spacing";
  const spacing = requireObject(value, context);
  requireExactFields(spacing, ["unit", "steps"], context);
  const unit = requireInteger(spacing, "unit", context);

  if (unit <= 0) {
    throw new DesignTokenSourceError("Spacing unit must be positive");
  }

  const steps = requireArray(spacing.steps, `${context}.steps`).map(
    (step, index) => {
      if (
        typeof step !== "number" ||
        !Number.isInteger(step) ||
        step <= 0
      ) {
        throw new DesignTokenSourceError(
          `${context}.steps[${index}] must be a positive integer`,
        );
      }

      return step;
    },
  );

  requireStrictOrder(steps, false, "Spacing steps");

  if (
    steps.length === 0 ||
    steps[0] !== unit ||
    steps.some((step) => step % unit !== 0)
  ) {
    throw new DesignTokenSourceError(
      "Spacing steps must start at and align to the unit",
    );
  }

  return { unit, steps };
}

function parseSemantic(value: unknown): Record<string, Record<string, string>> {
  const context = "Design token source.semantic";
  const semantic = requireObject(value, context);
  requireExactFields(semantic, Object.keys(semanticRoleKinds), context);
  const result: Record<string, Record<string, string>> = {};

  for (const [groupId, roleKinds] of Object.entries(semanticRoleKinds)) {
    const groupContext = `${context}.${groupId}`;
    const group = requireObject(semantic[groupId], groupContext);
    requireExactFields(group, Object.keys(roleKinds), groupContext);
    const references: Record<string, string> = {};

    for (const roleId of Object.keys(roleKinds)) {
      references[roleId] = requireText(group, roleId, groupContext);
    }

    result[groupId] = references;
  }

  return result;
}

function paletteColorIndex(
  palette: DesignTokenSource["palette"],
): Map<string, string> {
  const colors = new Map<string, string>();

  for (const [groupId, group] of Object.entries(palette)) {
    for (const [tokenId, value] of Object.entries(group)) {
      colors.set(`${groupId}.${tokenId}`, value);
    }
  }

  return colors;
}

function parseRules(
  value: unknown,
  colors: ReadonlyMap<string, string>,
): DesignTokenSource["rules"] {
  const context = "Design token source.rules";
  const rules = requireObject(value, context);
  requireExactFields(
    rules,
    ["motion", "density", "cornerLanguage", "contrastPairs"],
    context,
  );

  const motion = requireText(rules, "motion", context);
  const density = requireText(rules, "density", context);
  const cornerLanguage = requireText(rules, "cornerLanguage", context);

  if (motion !== "static-github") {
    throw new DesignTokenSourceError(`Unsupported motion policy: ${motion}`);
  }
  if (density !== "editorial") {
    throw new DesignTokenSourceError(`Unsupported density policy: ${density}`);
  }
  if (cornerLanguage !== "soft-technical") {
    throw new DesignTokenSourceError(
      `Unsupported corner language: ${cornerLanguage}`,
    );
  }

  const contrastPairs: ContrastPair[] = [];
  const seenPairs = new Set<string>();

  for (const [index, rawPair] of requireArray(
    rules.contrastPairs,
    `${context}.contrastPairs`,
  ).entries()) {
    const pairContext = `${context}.contrastPairs[${index}]`;
    const pair = requireObject(rawPair, pairContext);
    requireExactFields(
      pair,
      ["foreground", "background", "minimum"],
      pairContext,
    );
    const foreground = requireText(pair, "foreground", pairContext);
    const background = requireText(pair, "background", pairContext);
    const minimum = requireNumber(pair, "minimum", pairContext);

    for (const colorId of [foreground, background]) {
      if (!colors.has(colorId)) {
        throw new DesignTokenSourceError(
          `Unknown contrast color: ${colorId}`,
        );
      }
    }

    const pairId = `${foreground}\u0000${background}`;

    if (seenPairs.has(pairId)) {
      throw new DesignTokenSourceError(
        `Duplicate contrast pair: ${foreground} on ${background}`,
      );
    }
    seenPairs.add(pairId);

    const actual = contrastRatio(
      colors.get(foreground)!,
      colors.get(background)!,
    );

    if (minimum <= 1 || minimum > 21) {
      throw new DesignTokenSourceError(
        `${pairContext}.minimum must be between one and 21`,
      );
    }

    if (actual < minimum) {
      throw new DesignTokenSourceError(
        `Contrast ${foreground} on ${background} does not meet minimum ${minimum.toFixed(1)}; actual ${actual.toFixed(3)}`,
      );
    }

    contrastPairs.push({
      foreground,
      background,
      minimum,
      actual,
    });
  }

  if (contrastPairs.length === 0) {
    throw new DesignTokenSourceError(
      "At least one contrast pair is required",
    );
  }

  return { motion, density, cornerLanguage, contrastPairs };
}

function rawTokenIndex(source: DesignTokenSource): Map<string, RawDesignToken> {
  const tokens = new Map<string, RawDesignToken>();

  const add = (
    tokenId: string,
    kind: DesignTokenKind,
    value: DesignTokenValue,
  ) => {
    if (tokens.has(tokenId)) {
      throw new DesignTokenSourceError(
        `Duplicate raw token path: ${tokenId}`,
      );
    }

    tokens.set(tokenId, { tokenId, kind, value });
  };

  for (const [groupId, group] of Object.entries(source.palette)) {
    for (const [tokenId, value] of Object.entries(group)) {
      add(`${groupId}.${tokenId}`, "color", value);
    }
  }

  add("typography.fontStack", "font-stack", source.typography.fontStack);
  add("typography.monoStack", "font-stack", source.typography.monoStack);

  for (const id of typeSizeIds) {
    add(`typography.sizes.${id}`, "length", source.typography.sizes[id]!);
  }
  for (const id of typeWeightIds) {
    add(
      `typography.weights.${id}`,
      "font-weight",
      source.typography.weights[id]!,
    );
  }
  for (const id of trackingIds) {
    add(
      `typography.tracking.${id}`,
      "tracking",
      source.typography.tracking[id]!,
    );
  }

  add("spacing.unit", "length", source.spacing.unit);
  source.spacing.steps.forEach((step, index) => {
    add(`spacing.steps.${index}`, "length", step);
  });

  for (const id of radiusIds) {
    add(`radii.${id}`, "length", source.radii[id]!);
  }
  for (const id of strokeIds) {
    add(`strokes.${id}`, "length", source.strokes[id]!);
  }
  for (const id of opacityIds) {
    add(`opacity.${id}`, "opacity", source.opacity[id]!);
  }
  for (const id of layoutIds) {
    add(
      `layout.${id}`,
      id === "columns" ? "number" : "length",
      source.layout[id]!,
    );
  }
  for (const id of effectIds) {
    add(
      `effects.${id}`,
      id === "glowOpacity" ? "opacity" : "length",
      source.effects[id]!,
    );
  }
  for (const id of motionDurationIds) {
    add(`motion.duration.${id}`, "duration", source.motion.duration[id]!);
  }

  return tokens;
}

export function parseDesignTokenSource(document: unknown): DesignTokenSource {
  const context = "Design token source";
  const source = requireObject(document, context);
  requireExactFields(
    source,
    [
      "schemaVersion",
      "themeId",
      "palette",
      "typography",
      "spacing",
      "radii",
      "strokes",
      "opacity",
      "layout",
      "effects",
      "motion",
      "semantic",
      "rules",
    ],
    context,
  );

  const schemaVersion = requireInteger(source, "schemaVersion", context);

  if (schemaVersion !== supportedSchemaVersion) {
    throw new DesignTokenSourceError(
      `Unsupported design token schemaVersion: ${schemaVersion}`,
    );
  }

  const themeId = requireText(source, "themeId", context);

  if (!identifierPattern.test(themeId)) {
    throw new DesignTokenSourceError(
      "Design token source.themeId must use lowercase kebab-case",
    );
  }

  const palette = parsePalette(source.palette);
  const typography = parseTypography(source.typography);
  const spacing = parseSpacing(source.spacing);
  const radii = parseNumericGroup(
    source.radii,
    radiusIds,
    "Design token source.radii",
  );
  const strokes = parseNumericGroup(
    source.strokes,
    strokeIds,
    "Design token source.strokes",
  );
  const opacity = parseNumericGroup(
    source.opacity,
    opacityIds,
    "Design token source.opacity",
  );
  const layout = parseNumericGroup(
    source.layout,
    layoutIds,
    "Design token source.layout",
  );
  const effects = parseNumericGroup(
    source.effects,
    effectIds,
    "Design token source.effects",
  );

  const motionSource = requireObject(
    source.motion,
    "Design token source.motion",
  );
  requireExactFields(
    motionSource,
    ["duration"],
    "Design token source.motion",
  );
  const motion = {
    duration: parseNumericGroup(
      motionSource.duration,
      motionDurationIds,
      "Design token source.motion.duration",
    ),
  };

  const positiveRadiiAndStrokes = [
    ...radiusIds.map((id) => radii[id]!),
    ...strokeIds.map((id) => strokes[id]!),
  ];

  if (positiveRadiiAndStrokes.some((value) => value <= 0)) {
    throw new DesignTokenSourceError("Radii and strokes must be positive");
  }

  const opacityValues = opacityIds.map((id) => opacity[id]!);
  requireStrictOrder(opacityValues, false, "Opacity values");

  if (opacityValues.some((value) => value <= 0 || value > 1)) {
    throw new DesignTokenSourceError(
      "Opacity values must be greater than zero and at most one",
    );
  }

  // The Python baseline validates layout bounds after integer coercion.
  // Preserve that accepted behavior during this migration.
  const canvasWidth = Math.trunc(layout.canvasWidth!);
  const columns = Math.trunc(layout.columns!);
  const safeInset = Math.trunc(layout.safeInset!);

  if (canvasWidth < 960 || canvasWidth > 1600) {
    throw new DesignTokenSourceError(
      "Layout canvasWidth must be between 960 and 1600",
    );
  }
  if (columns !== 12) {
    throw new DesignTokenSourceError("Layout columns must equal 12");
  }
  if (safeInset * 2 >= canvasWidth) {
    throw new DesignTokenSourceError(
      "Layout safeInset leaves no usable canvas width",
    );
  }

  if (effects.glowBlur! < 0 || effects.glowBlur! > 32) {
    throw new DesignTokenSourceError(
      "effects.glowBlur must be between zero and 32",
    );
  }
  if (effects.glowOpacity! < 0 || effects.glowOpacity! > 1) {
    throw new DesignTokenSourceError(
      "effects.glowOpacity must be between zero and one",
    );
  }

  const durationValues = motionDurationIds.map(
    (id) => motion.duration[id]!,
  );
  requireStrictOrder(durationValues, false, "Motion durations");

  if (durationValues.some((value) => value <= 0 || value > 1000)) {
    throw new DesignTokenSourceError(
      "Motion durations must be greater than zero and at most 1000 milliseconds",
    );
  }

  const semantic = parseSemantic(source.semantic);
  const colors = paletteColorIndex(palette);
  const rules = parseRules(source.rules, colors);

  return {
    schemaVersion: supportedSchemaVersion,
    themeId,
    palette,
    typography,
    spacing,
    radii,
    strokes,
    opacity,
    layout,
    effects,
    motion,
    semantic,
    rules,
  };
}

export function resolveSemanticDesignTokens(
  source: DesignTokenSource,
): ResolvedDesignTokenContract {
  const raw = rawTokenIndex(source);
  const authored = new Map<
    string,
    { reference: string; requiredKind: DesignTokenKind }
  >();

  for (const [groupId, roleKinds] of Object.entries(semanticRoleKinds)) {
    const group = source.semantic[groupId]!;

    for (const [roleId, requiredKind] of Object.entries(roleKinds)) {
      authored.set(`semantic.${groupId}.${roleId}`, {
        reference: group[roleId]!,
        requiredKind,
      });
    }
  }

  const resolvedCache = new Map<string, RawDesignToken>();

  const resolveToken = (
    path: string,
    stack: readonly string[],
  ): RawDesignToken => {
    const rawToken = raw.get(path);

    if (rawToken !== undefined) {
      return rawToken;
    }

    const cached = resolvedCache.get(path);

    if (cached !== undefined) {
      return cached;
    }

    const authoredEntry = authored.get(path);

    if (authoredEntry === undefined) {
      const owner = stack.at(-1);
      throw new DesignTokenSourceError(
        `${owner ?? path} references unknown token ${path}`,
      );
    }

    const cycleStart = stack.indexOf(path);

    if (cycleStart >= 0) {
      const cycle = [...stack.slice(cycleStart), path];
      throw new DesignTokenSourceError(
        `Semantic reference cycle: ${cycle.join(" -> ")}`,
      );
    }

    const target = resolveToken(authoredEntry.reference, [...stack, path]);

    if (target.kind !== authoredEntry.requiredKind) {
      throw new DesignTokenSourceError(
        `${path} requires a ${authoredEntry.requiredKind} token; ${authoredEntry.reference} resolves to ${target.kind}`,
      );
    }

    resolvedCache.set(path, target);
    return target;
  };

  const semantic = new Map<
    string,
    ReadonlyMap<string, ResolvedSemanticToken>
  >();

  for (const [groupId, roleKinds] of Object.entries(semanticRoleKinds)) {
    const group = new Map<string, ResolvedSemanticToken>();

    for (const [roleId, requiredKind] of Object.entries(roleKinds)) {
      const path = `semantic.${groupId}.${roleId}`;
      const reference = source.semantic[groupId]![roleId]!;
      const target = resolveToken(path, []);

      group.set(roleId, {
        reference,
        resolvedTokenId: target.tokenId,
        kind: requiredKind,
      });
    }

    semantic.set(groupId, group);
  }

  return {
    schemaVersion: source.schemaVersion,
    themeId: source.themeId,
    raw,
    semantic,
  };
}

export function loadDesignTokenSource(sourcePath: string): DesignTokenSource {
  const document = JSON.parse(readFileSync(sourcePath, "utf8")) as unknown;
  return parseDesignTokenSource(document);
}
