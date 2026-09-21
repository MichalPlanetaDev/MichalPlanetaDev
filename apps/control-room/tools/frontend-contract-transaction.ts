import { randomUUID } from "node:crypto";
import {
  mkdir,
  open,
  readFile,
  rename,
  rm,
} from "node:fs/promises";
import { basename, dirname, resolve } from "node:path";

export interface FrontendContractSet {
  publicProfile: {
    path: string;
    content: string;
  };
  designTokenCss: {
    path: string;
    content: string;
  };
  designTokenTypescript: {
    path: string;
    content: string;
  };
}

export type ReplaceContractFile = (
  sourcePath: string,
  destinationPath: string,
) => Promise<void>;

export class FrontendContractTransactionError extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "FrontendContractTransactionError";
  }
}

interface PreparedContract {
  destinationPath: string;
  content: string;
  existed: boolean;
  writePath: string | null;
  rollbackPath: string | null;
  replaced: boolean;
}

async function pathExists(path: string): Promise<boolean> {
  try {
    await readFile(path);
    return true;
  } catch (error) {
    if (
      error instanceof Error &&
      "code" in error &&
      error.code === "ENOENT"
    ) {
      return false;
    }

    throw error;
  }
}

async function writeSiblingFile(
  destinationPath: string,
  purpose: "write" | "rollback",
  content: string | Uint8Array,
): Promise<string> {
  const directory = dirname(destinationPath);
  await mkdir(directory, { recursive: true });

  const temporaryPath = resolve(
    directory,
    `.${basename(destinationPath)}.${purpose}.${randomUUID()}.tmp`,
  );
  const handle = await open(temporaryPath, "wx");

  try {
    await handle.writeFile(content);
    await handle.sync();
  } catch (error) {
    await handle.close();
    await rm(temporaryPath, { force: true });
    throw error;
  }

  await handle.close();
  return temporaryPath;
}

function contractSequence(
  contracts: FrontendContractSet,
): Array<{ path: string; content: string }> {
  return [
    contracts.publicProfile,
    contracts.designTokenCss,
    contracts.designTokenTypescript,
  ];
}

function requireDistinctDestinations(
  contracts: FrontendContractSet,
): void {
  const paths = contractSequence(contracts).map((contract) =>
    resolve(contract.path),
  );

  if (new Set(paths).size !== paths.length) {
    throw new FrontendContractTransactionError(
      "Frontend contract outputs must use distinct destination paths",
    );
  }
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export async function replaceFrontendContracts(
  contracts: FrontendContractSet,
  replaceContractFile: ReplaceContractFile = rename,
): Promise<void> {
  requireDistinctDestinations(contracts);

  const prepared: PreparedContract[] = [];

  try {
    for (const contract of contractSequence(contracts)) {
      const destinationPath = resolve(contract.path);
      prepared.push({
        destinationPath,
        content: contract.content,
        existed: await pathExists(destinationPath),
        writePath: null,
        rollbackPath: null,
        replaced: false,
      });
    }

    for (const contract of prepared) {
      contract.writePath = await writeSiblingFile(
        contract.destinationPath,
        "write",
        contract.content,
      );
    }

    for (const contract of prepared) {
      if (!contract.existed) {
        continue;
      }

      contract.rollbackPath = await writeSiblingFile(
        contract.destinationPath,
        "rollback",
        await readFile(contract.destinationPath),
      );
    }

    for (const contract of prepared) {
      if (contract.writePath === null) {
        throw new FrontendContractTransactionError(
          `Missing prepared write file for ${contract.destinationPath}`,
        );
      }

      await replaceContractFile(
        contract.writePath,
        contract.destinationPath,
      );
      contract.writePath = null;
      contract.replaced = true;
    }
  } catch (writeError) {
    const rollbackErrors: string[] = [];

    for (const contract of [...prepared].reverse()) {
      if (!contract.replaced) {
        continue;
      }

      try {
        if (contract.existed) {
          if (contract.rollbackPath === null) {
            throw new FrontendContractTransactionError(
              `Missing rollback file for existing output: ${contract.destinationPath}`,
            );
          }

          await replaceContractFile(
            contract.rollbackPath,
            contract.destinationPath,
          );
          contract.rollbackPath = null;
        } else {
          await rm(contract.destinationPath, { force: true });
        }

        contract.replaced = false;
      } catch (rollbackError) {
        rollbackErrors.push(
          `${contract.destinationPath}: ${errorText(rollbackError)}`,
        );
      }
    }

    if (rollbackErrors.length > 0) {
      throw new FrontendContractTransactionError(
        `Frontend contract generation failed during output replacement (${errorText(writeError)}); rollback was incomplete: ${rollbackErrors.join("; ")}`,
        { cause: writeError },
      );
    }

    throw writeError;
  } finally {
    for (const contract of prepared) {
      for (const temporaryPath of [
        contract.writePath,
        contract.rollbackPath,
      ]) {
        if (temporaryPath !== null) {
          await rm(temporaryPath, { force: true });
        }
      }
    }
  }
}
