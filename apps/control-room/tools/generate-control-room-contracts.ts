import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve } from "node:path";

import {
  loadDesignTokenSource,
  resolveSemanticDesignTokens,
} from "./design-token-source.ts";
import {
  projectFrontendDesignTokens,
  renderDesignTokenCss,
  renderDesignTokenTypescript,
} from "./frontend-design-token-projection.ts";
import { replaceFrontendContracts } from "./frontend-contract-transaction.ts";
import { loadProfileSource } from "./profile-source.ts";
import {
  projectPublicProfile,
  renderPublicProfile,
} from "./public-profile-projection.ts";

export interface ControlRoomContractPaths {
  profileSource: string;
  designTokenSource: string;
  outputRoot: string;
}

const toolDirectory = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(toolDirectory, "..");
const repositoryRoot = resolve(packageRoot, "../..");

const defaultPaths: ControlRoomContractPaths = {
  profileSource: resolve(repositoryRoot, "profile/profile.json"),
  designTokenSource: resolve(
    repositoryRoot,
    "profile/design-tokens.json",
  ),
  outputRoot: resolve(packageRoot, "src/generated"),
};

export async function generateControlRoomContracts(
  paths: ControlRoomContractPaths,
): Promise<void> {
  const profile = projectPublicProfile(
    loadProfileSource(paths.profileSource),
  );
  const resolvedTokens = resolveSemanticDesignTokens(
    loadDesignTokenSource(paths.designTokenSource),
  );
  const frontendTokens = projectFrontendDesignTokens(resolvedTokens);

  const publicProfile = renderPublicProfile(profile);
  const designTokenCss = renderDesignTokenCss(frontendTokens);
  const designTokenTypescript =
    renderDesignTokenTypescript(frontendTokens);

  await replaceFrontendContracts({
    publicProfile: {
      path: resolve(paths.outputRoot, "public-profile.json"),
      content: publicProfile,
    },
    designTokenCss: {
      path: resolve(paths.outputRoot, "design-tokens.css"),
      content: designTokenCss,
    },
    designTokenTypescript: {
      path: resolve(paths.outputRoot, "design-tokens.ts"),
      content: designTokenTypescript,
    },
  });
}

function parseCliArguments(
  arguments_: readonly string[],
): ControlRoomContractPaths {
  const paths = { ...defaultPaths };
  const optionTargets: Record<
    string,
    keyof ControlRoomContractPaths
  > = {
    "--profile-source": "profileSource",
    "--design-token-source": "designTokenSource",
    "--output-root": "outputRoot",
  };

  for (let index = 0; index < arguments_.length; index += 1) {
    const option = arguments_[index]!;
    const target = optionTargets[option];

    if (target === undefined) {
      throw new Error(`Unknown option: ${option}`);
    }

    const value = arguments_[index + 1];

    if (value === undefined || value.startsWith("--")) {
      throw new Error(`Missing value for ${option}`);
    }

    paths[target] = resolve(value);
    index += 1;
  }

  return paths;
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export async function runControlRoomContractsCli(
  arguments_: readonly string[],
): Promise<number> {
  try {
    await generateControlRoomContracts(parseCliArguments(arguments_));
    return 0;
  } catch (error) {
    console.error(`control-room-contracts: ${errorText(error)}`);
    return 2;
  }
}

function isDirectExecution(): boolean {
  const entry = process.argv[1];

  if (entry === undefined) {
    return false;
  }

  return pathToFileURL(resolve(entry)).href === import.meta.url;
}

if (isDirectExecution()) {
  process.exitCode = await runControlRoomContractsCli(
    process.argv.slice(2),
  );
}
