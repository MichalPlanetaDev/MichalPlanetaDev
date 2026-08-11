import { createHash } from "node:crypto";

import type {
  DesignTokenKind,
  DesignTokenValue,
  ResolvedDesignTokenContract,
} from "./design-token-source.ts";

export interface ResolvedFrontendToken {
  role: string;
  sourceTokenId: string;
  kind: DesignTokenKind;
  value: DesignTokenValue;
}

export interface FrontendDesignTokens {
  schemaVersion: number;
  themeId: string;
  fingerprint: string;
  raw: Readonly<
    Record<string, Readonly<Record<string, ResolvedFrontendToken>>>
  >;
  semantic: Readonly<
    Record<string, Readonly<Record<string, ResolvedFrontendToken>>>
  >;
}

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

function sortedEntries<T>(
  source: Readonly<Record<string, T>>,
): Array<[string, T]> {
  return Object.entries(source).sort(([left], [right]) =>
    compareText(left, right),
  );
}

function canonicalValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(canonicalValue);
  }

  if (value !== null && typeof value === "object") {
    const source = value as Record<string, unknown>;
    return Object.fromEntries(
      Object.keys(source)
        .sort(compareText)
        .map((key) => [key, canonicalValue(source[key])]),
    );
  }

  return value;
}

function canonicalTokenRecord(token: ResolvedFrontendToken) {
  return {
    kind: token.kind,
    sourceTokenId: token.sourceTokenId,
    value: token.value,
  };
}

function fingerprintFor(
  schemaVersion: number,
  themeId: string,
  raw: FrontendDesignTokens["raw"],
  semantic: FrontendDesignTokens["semantic"],
): string {
  const record = {
    raw: Object.fromEntries(
      sortedEntries(raw).map(([groupId, group]) => [
        groupId,
        Object.fromEntries(
          sortedEntries(group).map(([roleId, token]) => [
            roleId,
            canonicalTokenRecord(token),
          ]),
        ),
      ]),
    ),
    schemaVersion,
    semantic: Object.fromEntries(
      sortedEntries(semantic).map(([groupId, group]) => [
        groupId,
        Object.fromEntries(
          sortedEntries(group).map(([roleId, token]) => [
            roleId,
            canonicalTokenRecord(token),
          ]),
        ),
      ]),
    ),
    themeId,
  };
  const canonical = JSON.stringify(canonicalValue(record));

  return createHash("sha256").update(canonical, "utf8").digest("hex");
}

export function projectFrontendDesignTokens(
  contract: ResolvedDesignTokenContract,
): FrontendDesignTokens {
  const groupedRaw: Record<string, Record<string, ResolvedFrontendToken>> = {};

  for (const [tokenId, token] of [...contract.raw.entries()].sort(
    ([left], [right]) => compareText(left, right),
  )) {
    const separator = tokenId.indexOf(".");
    const groupId = separator === -1 ? tokenId : tokenId.slice(0, separator);
    const role = separator === -1 ? "" : tokenId.slice(separator + 1);
    const group = groupedRaw[groupId] ?? {};
    group[role] = {
      role,
      sourceTokenId: token.tokenId,
      kind: token.kind,
      value: token.value,
    };
    groupedRaw[groupId] = group;
  }

  const semantic: Record<
    string,
    Record<string, ResolvedFrontendToken>
  > = {};

  for (const [groupId, group] of [...contract.semantic.entries()].sort(
    ([left], [right]) => compareText(left, right),
  )) {
    const resolvedRoles: Record<string, ResolvedFrontendToken> = {};

    for (const [roleId, reference] of [...group.entries()].sort(
      ([left], [right]) => compareText(left, right),
    )) {
      const source = contract.raw.get(reference.resolvedTokenId);

      if (source === undefined) {
        throw new Error(
          `Resolved semantic token ${groupId}.${roleId} references missing raw token ${reference.resolvedTokenId}`,
        );
      }

      resolvedRoles[roleId] = {
        role: roleId,
        sourceTokenId: source.tokenId,
        kind: reference.kind,
        value: source.value,
      };
    }

    semantic[groupId] = resolvedRoles;
  }

  const raw = groupedRaw;
  const fingerprint = fingerprintFor(
    contract.schemaVersion,
    contract.themeId,
    raw,
    semantic,
  );

  return {
    schemaVersion: contract.schemaVersion,
    themeId: contract.themeId,
    fingerprint,
    raw,
    semantic,
  };
}

function cssName(identifier: string): string {
  return identifier
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replaceAll(".", "-")
    .toLowerCase();
}

function expandExponent(text: string): string {
  const match = text.match(/^(-?)(\d+)(?:\.(\d*))?[eE]([+-]?\d+)$/);

  if (match === null) {
    return text;
  }

  const sign = match[1] ?? "";
  const integer = match[2] ?? "0";
  const fraction = match[3] ?? "";
  const exponent = Number.parseInt(match[4] ?? "0", 10);
  const digits = `${integer}${fraction}`;
  const decimalIndex = integer.length + exponent;

  if (decimalIndex <= 0) {
    return `${sign}0.${"0".repeat(-decimalIndex)}${digits}`;
  }

  if (decimalIndex >= digits.length) {
    return `${sign}${digits}${"0".repeat(decimalIndex - digits.length)}`;
  }

  return `${sign}${digits.slice(0, decimalIndex)}.${digits.slice(decimalIndex)}`;
}

function decimalText(value: number): string {
  if (Object.is(value, -0)) {
    return "0";
  }

  return expandExponent(String(value));
}

function rem(value: number): string {
  return `${decimalText(value / 16)}rem`;
}

function cssValue(token: ResolvedFrontendToken): string {
  const { value } = token;

  if (token.kind === "font-stack") {
    if (!Array.isArray(value)) {
      throw new TypeError(
        `${token.sourceTokenId} must contain a font stack`,
      );
    }

    return value.join(", ");
  }

  if (token.kind === "color") {
    if (typeof value !== "string") {
      throw new TypeError(
        `${token.sourceTokenId} must contain a color`,
      );
    }

    return value;
  }

  if (typeof value !== "number") {
    throw new TypeError(
      `${token.sourceTokenId} has incompatible ${token.kind} data`,
    );
  }

  if (token.kind === "duration") {
    return `${decimalText(value)}ms`;
  }
  if (token.kind === "length") {
    return token.sourceTokenId.startsWith("strokes.")
      ? `${decimalText(value)}px`
      : rem(value);
  }
  if (token.kind === "tracking") {
    return rem(value);
  }
  if (
    token.kind === "font-weight" ||
    token.kind === "number" ||
    token.kind === "opacity"
  ) {
    return decimalText(value);
  }

  throw new Error(`Unsupported frontend token kind: ${token.kind}`);
}

function cssDeclarations(
  tokens: FrontendDesignTokens,
): Array<[string, string]> {
  const declarations: Array<[string, string]> = [];

  for (const [groupId, group] of sortedEntries(tokens.raw)) {
    for (const [roleId, token] of sortedEntries(group)) {
      declarations.push([
        `--cr-raw-${cssName(groupId)}-${cssName(roleId)}`,
        cssValue(token),
      ]);
    }
  }

  for (const [groupId, group] of sortedEntries(tokens.semantic)) {
    for (const [roleId, token] of sortedEntries(group)) {
      declarations.push([
        `--cr-${cssName(groupId)}-${cssName(roleId)}`,
        cssValue(token),
      ]);
    }
  }

  return declarations;
}

export function renderDesignTokenCss(
  tokens: FrontendDesignTokens,
): string {
  const lines = [
    "/* Generated by profile-system. Do not edit directly. */",
    `/* schema-version: ${tokens.schemaVersion} */`,
    `/* theme-id: ${tokens.themeId} */`,
    `/* fingerprint: ${tokens.fingerprint} */`,
    ":root {",
  ];

  for (const [name, value] of cssDeclarations(tokens)) {
    lines.push(`  ${name}: ${value};`);
  }

  lines.push("}", "");
  return lines.join("\n");
}

function typescriptString(value: string): string {
  return JSON.stringify(value);
}

function typescriptRawValue(value: DesignTokenValue): string {
  if (typeof value === "number") {
    return decimalText(value);
  }

  if (typeof value === "string") {
    return typescriptString(value);
  }

  return `[${value.map(typescriptString).join(", ")}]`;
}

function typescriptObject(
  groups: FrontendDesignTokens["raw"] | FrontendDesignTokens["semantic"],
  indent: string,
  cssValues: boolean,
): string[] {
  const lines = ["{"];
  const entries = sortedEntries(groups);

  entries.forEach(([groupId, group], groupIndex) => {
    const groupSuffix = groupIndex < entries.length - 1 ? "," : "";
    lines.push(`${indent}${JSON.stringify(groupId)}: {`);
    const roleEntries = sortedEntries(group);

    roleEntries.forEach(([roleId, token], roleIndex) => {
      const suffix = roleIndex < roleEntries.length - 1 ? "," : "";
      const rendered = cssValues
        ? typescriptString(cssValue(token))
        : typescriptRawValue(token.value);
      lines.push(
        `${indent}  ${JSON.stringify(roleId)}: ${rendered}${suffix}`,
      );
    });

    lines.push(`${indent}}${groupSuffix}`);
  });

  lines.push(indent.slice(0, -2) + "}");
  return lines;
}

export function renderDesignTokenTypescript(
  tokens: FrontendDesignTokens,
): string {
  const rawLines = typescriptObject(tokens.raw, "    ", false);
  const semanticLines = typescriptObject(tokens.semantic, "    ", true);
  const lines = [
    "// Generated by profile-system. Do not edit directly.",
    "",
    "export const designTokens = {",
    "  meta: {",
    `    schemaVersion: ${tokens.schemaVersion},`,
    `    themeId: ${typescriptString(tokens.themeId)},`,
    `    fingerprint: ${typescriptString(tokens.fingerprint)},`,
    "  },",
    `  raw: ${rawLines[0]}`,
    ...rawLines.slice(1, -1),
    `${rawLines.at(-1)},`,
    `  semantic: ${semanticLines[0]}`,
    ...semanticLines.slice(1, -1),
    `${semanticLines.at(-1)},`,
    "} as const;",
    "",
    "export type DesignTokens = typeof designTokens;",
    'export type SemanticDesignTokens = DesignTokens["semantic"];',
    "",
  ];

  return lines.join("\n");
}
