// @vitest-environment node

import { existsSync } from "node:fs";
import {
  mkdir,
  readFile,
  readdir,
  rename,
  rm,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";

import { afterEach, describe, expect, test } from "vitest";

const packageRoot = process.cwd();
const transactionModulePath = resolve(
  packageRoot,
  "tools/frontend-contract-transaction.ts",
);
const temporaryRoots: string[] = [];

afterEach(async () => {
  await Promise.all(
    temporaryRoots.splice(0).map((root) =>
      rm(root, { force: true, recursive: true }),
    ),
  );
});

async function transactionModule() {
  expect(
    existsSync(transactionModulePath),
    "frontend-contract-transaction.ts must exist",
  ).toBe(true);

  if (!existsSync(transactionModulePath)) {
    throw new Error("frontend-contract-transaction.ts must exist");
  }

  return import("./frontend-contract-transaction.ts");
}

async function temporaryRoot(): Promise<string> {
  const root = join(
    tmpdir(),
    `control-room-contract-transaction-${crypto.randomUUID()}`,
  );
  temporaryRoots.push(root);
  await mkdir(root, { recursive: true });
  return root;
}

function contracts(root: string) {
  return {
    publicProfile: {
      path: join(root, "public-profile.json"),
      content: "new profile\n",
    },
    designTokenCss: {
      path: join(root, "design-tokens.css"),
      content: "new css\n",
    },
    designTokenTypescript: {
      path: join(root, "design-tokens.ts"),
      content: "new ts\n",
    },
  };
}

async function seedExisting(root: string): Promise<void> {
  await writeFile(join(root, "public-profile.json"), "old profile\n");
  await writeFile(join(root, "design-tokens.css"), "old css\n");
  await writeFile(join(root, "design-tokens.ts"), "old ts\n");
}

async function hiddenResidue(root: string): Promise<string[]> {
  return (await readdir(root))
    .filter((name) => name.startsWith("."))
    .sort();
}

describe("frontend contract transaction", () => {
  test("replaces all three contracts and removes transaction residue", async () => {
    const { replaceFrontendContracts } = await transactionModule();
    const root = await temporaryRoot();
    await seedExisting(root);

    await replaceFrontendContracts(contracts(root));

    await expect(
      readFile(join(root, "public-profile.json"), "utf8"),
    ).resolves.toBe("new profile\n");
    await expect(
      readFile(join(root, "design-tokens.css"), "utf8"),
    ).resolves.toBe("new css\n");
    await expect(
      readFile(join(root, "design-tokens.ts"), "utf8"),
    ).resolves.toBe("new ts\n");
    await expect(hiddenResidue(root)).resolves.toEqual([]);
  });

  test("restores earlier destinations when the final replacement fails", async () => {
    const { replaceFrontendContracts } = await transactionModule();
    const root = await temporaryRoot();
    await seedExisting(root);

    const replaceWithFinalWriteFailure = async (
      sourcePath: string,
      destinationPath: string,
    ) => {
      if (
        basename(destinationPath) === "design-tokens.ts" &&
        basename(sourcePath).includes(".write.")
      ) {
        throw new Error(
          `simulated TypeScript replacement failure: ${destinationPath}`,
        );
      }

      await rename(sourcePath, destinationPath);
    };

    await expect(
      replaceFrontendContracts(
        contracts(root),
        replaceWithFinalWriteFailure,
      ),
    ).rejects.toThrow("simulated TypeScript replacement failure");

    await expect(
      readFile(join(root, "public-profile.json"), "utf8"),
    ).resolves.toBe("old profile\n");
    await expect(
      readFile(join(root, "design-tokens.css"), "utf8"),
    ).resolves.toBe("old css\n");
    await expect(
      readFile(join(root, "design-tokens.ts"), "utf8"),
    ).resolves.toBe("old ts\n");
    await expect(hiddenResidue(root)).resolves.toEqual([]);
  });

  test("removes newly created earlier destinations after a later failure", async () => {
    const { replaceFrontendContracts } = await transactionModule();
    const root = await temporaryRoot();

    const replaceWithFinalWriteFailure = async (
      sourcePath: string,
      destinationPath: string,
    ) => {
      if (
        basename(destinationPath) === "design-tokens.ts" &&
        basename(sourcePath).includes(".write.")
      ) {
        throw new Error("simulated final replacement failure");
      }

      await rename(sourcePath, destinationPath);
    };

    await expect(
      replaceFrontendContracts(
        contracts(root),
        replaceWithFinalWriteFailure,
      ),
    ).rejects.toThrow("simulated final replacement failure");

    await expect(
      readFile(join(root, "design-tokens.ts"), "utf8"),
    ).rejects.toThrow();
    await expect(
      readFile(join(root, "design-tokens.css"), "utf8"),
    ).rejects.toThrow();
    await expect(
      readFile(join(root, "public-profile.json"), "utf8"),
    ).rejects.toThrow();
    await expect(hiddenResidue(root)).resolves.toEqual([]);
  });

  test("reports the primary write failure and an incomplete rollback failure", async () => {
    const {
      FrontendContractTransactionError,
      replaceFrontendContracts,
    } = await transactionModule();
    const root = await temporaryRoot();
    await seedExisting(root);

    const replaceWithWriteAndRollbackFailures = async (
      sourcePath: string,
      destinationPath: string,
    ) => {
      const sourceName = basename(sourcePath);
      const destinationName = basename(destinationPath);

      if (
        destinationName === "design-tokens.ts" &&
        sourceName.includes(".write.")
      ) {
        throw new Error(
          `simulated TypeScript replacement failure: ${destinationPath}`,
        );
      }

      if (
        destinationName === "public-profile.json" &&
        sourceName.includes(".rollback.")
      ) {
        throw new Error(
          `simulated profile rollback failure: ${destinationPath}`,
        );
      }

      await rename(sourcePath, destinationPath);
    };

    let failure: unknown;

    try {
      await replaceFrontendContracts(
        contracts(root),
        replaceWithWriteAndRollbackFailures,
      );
    } catch (error) {
      failure = error;
    }

    expect(failure).toBeInstanceOf(FrontendContractTransactionError);
    expect(String(failure)).toContain(
      "simulated TypeScript replacement failure",
    );
    expect(String(failure)).toContain(
      join(root, "design-tokens.ts"),
    );
    expect(String(failure)).toContain(
      "simulated profile rollback failure",
    );
    expect(String(failure)).toContain(
      join(root, "public-profile.json"),
    );
    await expect(
      readFile(join(root, "design-tokens.css"), "utf8"),
    ).resolves.toBe("old css\n");
    await expect(
      readFile(join(root, "design-tokens.ts"), "utf8"),
    ).resolves.toBe("old ts\n");
    await expect(hiddenResidue(root)).resolves.toEqual([]);
  });
});
