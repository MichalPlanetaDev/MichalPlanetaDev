// @vitest-environment node

import { spawnSync } from "node:child_process";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { afterEach, describe, expect, test } from "vitest";

const packageRoot = process.cwd();
const temporaryRoots: string[] = [];

afterEach(() => {
  for (const root of temporaryRoots.splice(0)) {
    rmSync(root, { force: true, recursive: true });
  }
});

describe("native TypeScript tool boundary", () => {
  test("uses a dedicated compiler contract outside the Next.js program", () => {
    const toolConfigPath = resolve(packageRoot, "tsconfig.tools.json");

    expect(
      existsSync(toolConfigPath),
      "tsconfig.tools.json must exist",
    ).toBe(true);

    if (!existsSync(toolConfigPath)) {
      return;
    }

    const toolConfig = JSON.parse(
      readFileSync(toolConfigPath, "utf8"),
    ) as {
      compilerOptions?: Record<string, unknown>;
      include?: unknown;
    };
    const appConfig = JSON.parse(
      readFileSync(resolve(packageRoot, "tsconfig.json"), "utf8"),
    ) as {
      exclude?: unknown;
    };
    const packageDocument = JSON.parse(
      readFileSync(resolve(packageRoot, "package.json"), "utf8"),
    ) as {
      scripts?: Record<string, string>;
    };

    expect(toolConfig.compilerOptions).toMatchObject({
      erasableSyntaxOnly: true,
      module: "NodeNext",
      moduleResolution: "NodeNext",
      noEmit: true,
      rewriteRelativeImportExtensions: true,
      skipLibCheck: true,
      strict: true,
      target: "ESNext",
      types: ["node"],
      verbatimModuleSyntax: true,
    });
    expect(toolConfig.include).toEqual(["tools/**/*.ts"]);
    expect(appConfig.exclude).toEqual(
      expect.arrayContaining(["node_modules", "tools"]),
    );
    expect(packageDocument.scripts?.["typecheck:tools"]).toBe(
      "tsc --noEmit -p tsconfig.tools.json",
    );
  });

  test("Node executes erasable TypeScript with explicit TypeScript imports", () => {
    const fixtureRoot = mkdtempSync(
      join(tmpdir(), "control-room-native-typescript-"),
    );
    temporaryRoots.push(fixtureRoot);

    writeFileSync(
      join(fixtureRoot, "contract.ts"),
      [
        "export interface NativeContract {",
        "  label: string;",
        "}",
        "",
        "export const nativeContract: NativeContract = {",
        '  label: "native-typescript",',
        "};",
        "",
      ].join("\n"),
      "utf8",
    );
    writeFileSync(
      join(fixtureRoot, "entry.ts"),
      [
        'import { nativeContract } from "./contract.ts";',
        "",
        "console.log(nativeContract.label);",
        "",
      ].join("\n"),
      "utf8",
    );

    const execution = spawnSync(
      process.execPath,
      [join(fixtureRoot, "entry.ts")],
      { encoding: "utf8" },
    );

    expect(execution.status, execution.stderr).toBe(0);
    expect(execution.stdout).toBe("native-typescript\n");
  });
});
