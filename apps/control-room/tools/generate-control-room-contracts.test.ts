// @vitest-environment node

import { existsSync, readFileSync } from "node:fs";
import {
  mkdir,
  readFile,
  rm,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

import { afterEach, describe, expect, test } from "vitest";

const packageRoot = process.cwd();
const generatorModulePath = resolve(
  packageRoot,
  "tools/generate-control-room-contracts.ts",
);
const profileSource = resolve(
  packageRoot,
  "../../profile/profile.json",
);
const designTokenSource = resolve(
  packageRoot,
  "../../profile/design-tokens.json",
);
const committedRoot = resolve(packageRoot, "src/generated");
const temporaryRoots: string[] = [];

afterEach(async () => {
  await Promise.all(
    temporaryRoots.splice(0).map((root) =>
      rm(root, { force: true, recursive: true }),
    ),
  );
});

async function generatorModule() {
  expect(
    existsSync(generatorModulePath),
    "generate-control-room-contracts.ts must exist",
  ).toBe(true);

  if (!existsSync(generatorModulePath)) {
    throw new Error("generate-control-room-contracts.ts must exist");
  }

  return import("./generate-control-room-contracts.ts");
}

async function temporaryRoot(label: string): Promise<string> {
  const root = join(
    tmpdir(),
    `control-room-contracts-${label}-${crypto.randomUUID()}`,
  );
  temporaryRoots.push(root);
  await mkdir(root, { recursive: true });
  return root;
}

async function expectCommittedParity(outputRoot: string): Promise<void> {
  for (const name of [
    "public-profile.json",
    "design-tokens.css",
    "design-tokens.ts",
  ]) {
    await expect(readFile(join(outputRoot, name), "utf8")).resolves.toBe(
      readFileSync(join(committedRoot, name), "utf8"),
    );
  }
}

describe("Control Room contract generator", () => {
  test("generates all three accepted frontend contracts", async () => {
    const { generateControlRoomContracts } = await generatorModule();
    const outputRoot = await temporaryRoot("library");

    await generateControlRoomContracts({
      profileSource,
      designTokenSource,
      outputRoot,
    });

    await expectCommittedParity(outputRoot);
  });

  test("is deterministic across independent output roots", async () => {
    const { generateControlRoomContracts } = await generatorModule();
    const first = await temporaryRoot("first");
    const second = await temporaryRoot("second");

    await generateControlRoomContracts({
      profileSource,
      designTokenSource,
      outputRoot: first,
    });
    await generateControlRoomContracts({
      profileSource,
      designTokenSource,
      outputRoot: second,
    });

    for (const name of [
      "public-profile.json",
      "design-tokens.css",
      "design-tokens.ts",
    ]) {
      await expect(readFile(join(first, name), "utf8")).resolves.toBe(
        await readFile(join(second, name), "utf8"),
      );
    }
  });

  test("invalid profile input preserves every existing destination", async () => {
    const { generateControlRoomContracts } = await generatorModule();
    const root = await temporaryRoot("invalid");
    const invalidProfile = join(root, "invalid-profile.json");
    const outputRoot = join(root, "generated");

    await mkdir(outputRoot, { recursive: true });
    await writeFile(invalidProfile, "{}\n", "utf8");
    await writeFile(
      join(outputRoot, "public-profile.json"),
      "old profile\n",
      "utf8",
    );
    await writeFile(
      join(outputRoot, "design-tokens.css"),
      "old css\n",
      "utf8",
    );
    await writeFile(
      join(outputRoot, "design-tokens.ts"),
      "old ts\n",
      "utf8",
    );

    await expect(
      generateControlRoomContracts({
        profileSource: invalidProfile,
        designTokenSource,
        outputRoot,
      }),
    ).rejects.toThrow();

    await expect(
      readFile(join(outputRoot, "public-profile.json"), "utf8"),
    ).resolves.toBe("old profile\n");
    await expect(
      readFile(join(outputRoot, "design-tokens.css"), "utf8"),
    ).resolves.toBe("old css\n");
    await expect(
      readFile(join(outputRoot, "design-tokens.ts"), "utf8"),
    ).resolves.toBe("old ts\n");
  });

  test("direct Node CLI uses repository sources by default", async () => {
    await generatorModule();
    const outputRoot = await temporaryRoot("cli");
    const execution = spawnSync(
      process.execPath,
      [generatorModulePath, "--output-root", outputRoot],
      { encoding: "utf8" },
    );

    expect(execution.status, execution.stderr).toBe(0);
    expect(execution.stderr).toBe("");
    await expectCommittedParity(outputRoot);
  });

  test("direct CLI rejects unknown flags and missing values", async () => {
    await generatorModule();

    const unknown = spawnSync(
      process.execPath,
      [generatorModulePath, "--unexpected"],
      { encoding: "utf8" },
    );
    expect(unknown.status).toBe(2);
    expect(unknown.stderr).toContain(
      "control-room-contracts: Unknown option: --unexpected",
    );

    const missing = spawnSync(
      process.execPath,
      [generatorModulePath, "--output-root"],
      { encoding: "utf8" },
    );
    expect(missing.status).toBe(2);
    expect(missing.stderr).toContain(
      "control-room-contracts: Missing value for --output-root",
    );
  });

  test("package script exposes the native generator", async () => {
    await generatorModule();
    const packageDocument = JSON.parse(
      readFileSync(resolve(packageRoot, "package.json"), "utf8"),
    ) as { scripts?: Record<string, string> };

    expect(packageDocument.scripts?.["generate:contracts"]).toBe(
      "node tools/generate-control-room-contracts.ts",
    );
  });
});
