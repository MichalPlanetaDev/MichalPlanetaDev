// @vitest-environment node

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, test } from "vitest";

const packageRoot = process.cwd();
const sourceModulePath = resolve(packageRoot, "tools/profile-source.ts");
const repositoryProfilePath = resolve(
  packageRoot,
  "../../profile/profile.json",
);

type MutableRecord = Record<string, unknown>;

async function profileSourceModule() {
  expect(
    existsSync(sourceModulePath),
    "profile-source.ts must exist",
  ).toBe(true);

  if (!existsSync(sourceModulePath)) {
    throw new Error("profile-source.ts must exist");
  }

  return import("./profile-source.ts");
}

function validProfileDocument(): MutableRecord {
  return {
    schemaVersion: 2,
    profileId: "michal-planeta",
    displayName: "Michał Planeta",
    environmentId: "planetary-observatory",
    identity: {
      headline: "A — CINEMATIC SYSTEMS ENGINEER",
      role: "Software engineer.",
      motto: "Build and verify.",
      summary: "Repository-grounded engineering profile.",
    },
    projects: [
      {
        id: "alpha-project",
        name: "Alpha Project",
        summary: "Public project.",
        status: "active",
        public: true,
        featured: true,
        priority: 10,
        technologyIds: ["typescript"],
        evidenceIds: ["alpha-tests"],
        linkIds: ["alpha-repository-link"],
      },
    ],
    evidence: [
      {
        id: "alpha-tests",
        kind: "tests",
        label: "Alpha tests",
        summary: "Behavioral verification.",
        public: true,
        linkId: null,
      },
    ],
    technologies: [
      {
        id: "typescript",
        name: "TypeScript",
        category: "language",
        usage: "Browser and build-time contracts.",
        public: true,
        projectIds: ["alpha-project"],
        evidenceIds: ["alpha-tests"],
      },
    ],
    disciplines: [
      {
        id: "software-architecture",
        name: "Software Architecture",
        summary: "Clear boundaries.",
        public: true,
        projectIds: ["alpha-project"],
        evidenceIds: ["alpha-tests"],
      },
    ],
    links: [
      {
        id: "alpha-repository-link",
        label: "Alpha repository",
        kind: "repository",
        url: "https://github.com/example/alpha",
        public: true,
      },
    ],
  };
}

function collectionRecord(
  document: MutableRecord,
  collection: string,
  index = 0,
): MutableRecord {
  const records = document[collection] as MutableRecord[];
  return records[index] as MutableRecord;
}

describe("authored profile source", () => {
  test("loads the repository schema-two profile", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = JSON.parse(
      readFileSync(repositoryProfilePath, "utf8"),
    ) as unknown;

    const profile = parseProfileSource(document);

    expect(profile.schemaVersion).toBe(2);
    expect(profile.profileId).toBe("michal-planeta");
    expect(profile.projects).toHaveLength(2);
    expect(profile.technologies.length).toBeGreaterThanOrEqual(10);
    expect(profile.disciplines).toHaveLength(4);
  });

  test("rejects unsupported top-level fields", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    document.unexpected = true;

    expect(() => parseProfileSource(document)).toThrow(
      "Profile source contains unsupported fields: unexpected",
    );
  });

  test("rejects unsupported fields inside project records", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    collectionRecord(document, "projects").unexpected = true;

    expect(() => parseProfileSource(document)).toThrow(
      "Profile source.projects[0] contains unsupported fields: unexpected",
    );
  });

  test("rejects unsupported schema versions", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    document.schemaVersion = 3;

    expect(() => parseProfileSource(document)).toThrow(
      "Unsupported schemaVersion: 3",
    );
  });

  test("rejects duplicate identifiers within a collection", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    const projects = document.projects as MutableRecord[];
    projects.push(structuredClone(projects[0]));

    expect(() => parseProfileSource(document)).toThrow(
      "Duplicate identifier in projects: alpha-project",
    );
  });

  test("rejects identifiers shared by different collections", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    collectionRecord(document, "technologies").id = "alpha-project";
    collectionRecord(document, "projects").technologyIds = [
      "alpha-project",
    ];

    expect(() => parseProfileSource(document)).toThrow(
      "Duplicate global identifier alpha-project: projects and technologies",
    );
  });

  test("rejects duplicate references in one relationship", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    collectionRecord(document, "projects").evidenceIds = [
      "alpha-tests",
      "alpha-tests",
    ];

    expect(() => parseProfileSource(document)).toThrow(
      "Duplicate reference in Profile source.projects[0].evidenceIds: alpha-tests",
    );
  });

  test("rejects unresolved project references", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    collectionRecord(document, "projects").technologyIds = [
      "missing-technology",
    ];

    expect(() => parseProfileSource(document)).toThrow(
      "Unresolved reference in project alpha-project: missing-technology",
    );
  });

  test("rejects unresolved evidence links", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    collectionRecord(document, "evidence").linkId = "missing-link";

    expect(() => parseProfileSource(document)).toThrow(
      "Unresolved reference in evidence alpha-tests: missing-link",
    );
  });

  test("rejects public evidence that references a nonpublic link", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    collectionRecord(document, "evidence").linkId =
      "alpha-repository-link";
    collectionRecord(document, "links").public = false;

    expect(() => parseProfileSource(document)).toThrow(
      "Public evidence alpha-tests references nonpublic link alpha-repository-link",
    );
  });

  test("rejects public unpublished projects", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    collectionRecord(document, "projects").status = "unpublished";

    expect(() => parseProfileSource(document)).toThrow(
      "Project alpha-project with status unpublished must not be public",
    );
  });

  test("rejects featured projects that are not public", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    collectionRecord(document, "projects").public = false;

    expect(() => parseProfileSource(document)).toThrow(
      "Project alpha-project must not be featured when public is false",
    );
  });

  test("rejects invalid project status values", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    collectionRecord(document, "projects").status = "shipping";

    expect(() => parseProfileSource(document)).toThrow(
      "Unsupported Profile source.projects[0].status: shipping",
    );
  });

  test("rejects identifiers outside lowercase kebab case", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    collectionRecord(document, "projects").id = "Alpha_Project";

    expect(() => parseProfileSource(document)).toThrow(
      "Profile source.projects[0].id must use a lowercase kebab-case identifier",
    );
  });

  test("rejects invalid link URLs", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = validProfileDocument();
    collectionRecord(document, "links").url = "http://example.com/alpha";

    expect(() => parseProfileSource(document)).toThrow(
      "Profile source.links[0].url must contain an absolute https URL or contact mailto URL",
    );
  });

  test("repository profile reflects post-contraction TypeScript architecture", async () => {
    const { parseProfileSource } = await profileSourceModule();
    const document = JSON.parse(
      readFileSync(repositoryProfilePath, "utf8"),
    ) as unknown;
    const profile = parseProfileSource(document);

    const profileProject = profile.projects.find(
      (project) => project.id === "github-profile-system",
    );

    expect(profileProject).toBeDefined();

    if (!profileProject) {
      throw new Error("github-profile-system project is missing");
    }

    expect(profileProject.technologyIds).toEqual([
      "typescript",
      "nodejs",
      "nextjs",
      "react",
      "pnpm",
      "github-actions",
      "playwright",
      "shellcheck",
    ]);

    for (const retiredTechnologyId of [
      "python",
      "uv",
      "svg",
      "xmllint",
    ]) {
      expect(
        profile.technologies.some(
          (technology) => technology.id === retiredTechnologyId,
        ),
      ).toBe(false);
    }

    const repositoryEvidence = profile.evidence.find(
      (evidence) => evidence.id === "profile-system-repository",
    );
    const testEvidence = profile.evidence.find(
      (evidence) => evidence.id === "profile-system-tests",
    );
    const renderingDiscipline = profile.disciplines.find(
      (discipline) => discipline.id === "rendering-and-graphics",
    );

    expect(repositoryEvidence).toBeDefined();
    expect(testEvidence).toBeDefined();
    expect(renderingDiscipline).toBeDefined();

    if (!repositoryEvidence || !testEvidence || !renderingDiscipline) {
      throw new Error("Required post-contraction evidence is missing");
    }

    const retiredEvidencePattern =
      /static svg capability probe|xml validation|static vector publication/i;

    expect(repositoryEvidence.summary).not.toMatch(
      retiredEvidencePattern,
    );
    expect(testEvidence.summary).not.toMatch(retiredEvidencePattern);
    expect(renderingDiscipline.summary).not.toMatch(
      retiredEvidencePattern,
    );
    expect(renderingDiscipline.projectIds).not.toContain(
      "github-profile-system",
    );
  });

});
