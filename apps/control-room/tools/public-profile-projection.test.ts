// @vitest-environment node

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, test } from "vitest";

import {
  loadProfileSource,
  parseProfileSource,
  type ProfileSource,
} from "./profile-source.ts";

const packageRoot = process.cwd();
const projectionModulePath = resolve(
  packageRoot,
  "tools/public-profile-projection.ts",
);
const repositoryProfilePath = resolve(
  packageRoot,
  "../../profile/profile.json",
);
const committedFrontendProfilePath = resolve(
  packageRoot,
  "src/generated/public-profile.json",
);

type MutableRecord = Record<string, unknown>;

async function projectionModule() {
  expect(
    existsSync(projectionModulePath),
    "public-profile-projection.ts must exist",
  ).toBe(true);

  if (!existsSync(projectionModulePath)) {
    throw new Error("public-profile-projection.ts must exist");
  }

  return import("./public-profile-projection.ts");
}

function projectionDocument(): MutableRecord {
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
        id: "later-project",
        name: "Later Project",
        summary: "Second public project.",
        status: "active",
        public: true,
        featured: false,
        priority: 20,
        technologyIds: ["typescript"],
        evidenceIds: ["later-tests"],
        linkIds: [],
      },
      {
        id: "first-project",
        name: "First Project",
        summary: "First public project.",
        status: "completed",
        public: true,
        featured: true,
        priority: 10,
        technologyIds: ["typescript"],
        evidenceIds: ["first-tests", "private-notes"],
        linkIds: ["public-link", "private-link"],
      },
      {
        id: "private-project",
        name: "Private Project",
        summary: "Nonpublic project.",
        status: "experimental",
        public: false,
        featured: false,
        priority: 0,
        technologyIds: [],
        evidenceIds: ["private-notes"],
        linkIds: ["private-link"],
      },
    ],
    evidence: [
      {
        id: "first-tests",
        kind: "tests",
        label: "First tests",
        summary: "Public verification.",
        public: true,
        linkId: null,
      },
      {
        id: "later-tests",
        kind: "tests",
        label: "Later tests",
        summary: "Public verification.",
        public: true,
        linkId: null,
      },
      {
        id: "private-notes",
        kind: "documentation",
        label: "Private notes",
        summary: "Nonpublic details.",
        public: false,
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
        projectIds: ["first-project", "private-project"],
        evidenceIds: ["first-tests", "private-notes"],
      },
    ],
    disciplines: [
      {
        id: "software-architecture",
        name: "Software Architecture",
        summary: "Clear boundaries.",
        public: true,
        projectIds: ["first-project", "private-project"],
        evidenceIds: ["first-tests", "private-notes"],
      },
    ],
    links: [
      {
        id: "public-link",
        label: "Public link",
        kind: "repository",
        url: "https://github.com/example/public",
        public: true,
      },
      {
        id: "private-link",
        label: "Private link",
        kind: "documentation",
        url: "https://example.com/private",
        public: false,
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

function parsedProjectionDocument(): ProfileSource {
  return parseProfileSource(projectionDocument());
}

describe("public profile projection", () => {
  test("filters private records and references in deterministic order", async () => {
    const { projectPublicProfile } = await projectionModule();

    const profile = projectPublicProfile(parsedProjectionDocument());

    expect(profile.projects.map((project) => project.id)).toEqual([
      "first-project",
      "later-project",
    ]);
    expect(profile.projects[0]?.evidenceIds).toEqual(["first-tests"]);
    expect(profile.projects[0]?.linkIds).toEqual(["public-link"]);
    expect(profile.technologies[0]?.projectIds).toEqual(["first-project"]);
    expect(profile.technologies[0]?.evidenceIds).toEqual(["first-tests"]);
    expect(profile.disciplines[0]?.projectIds).toEqual(["first-project"]);
    expect(profile.links.map((link) => link.id)).toEqual(["public-link"]);
    expect(profile.evidence.map((record) => record.id)).toEqual([
      "first-tests",
      "later-tests",
    ]);
  });

  test("requires public evidence for every projected project", async () => {
    const { projectPublicProfile } = await projectionModule();
    const document = projectionDocument();
    collectionRecord(document, "projects", 0).public = false;
    collectionRecord(document, "projects", 1).evidenceIds = [
      "private-notes",
    ];
    const source = parseProfileSource(document);

    expect(() => projectPublicProfile(source)).toThrow(
      "Public project first-project has no public evidence",
    );
  });

  test("requires a public dependency for projected technologies", async () => {
    const { projectPublicProfile } = await projectionModule();
    const document = projectionDocument();
    collectionRecord(document, "technologies").projectIds = [
      "private-project",
    ];
    collectionRecord(document, "technologies").evidenceIds = [
      "private-notes",
    ];
    const source = parseProfileSource(document);

    expect(() => projectPublicProfile(source)).toThrow(
      "Public technology typescript has no public dependency",
    );
  });

  test("requires a public dependency for projected disciplines", async () => {
    const { projectPublicProfile } = await projectionModule();
    const document = projectionDocument();
    collectionRecord(document, "disciplines").projectIds = [
      "private-project",
    ];
    collectionRecord(document, "disciplines").evidenceIds = [
      "private-notes",
    ];
    const source = parseProfileSource(document);

    expect(() => projectPublicProfile(source)).toThrow(
      "Public discipline software-architecture has no public dependency",
    );
  });

  test("rendered frontend data contains no authoring visibility fields", async () => {
    const { projectPublicProfile, renderPublicProfile } =
      await projectionModule();

    const rendered = renderPublicProfile(
      projectPublicProfile(parsedProjectionDocument()),
    );
    const document = JSON.parse(rendered) as MutableRecord;

    expect(document.schemaVersion).toBe(1);
    expect(document.sourceSchemaVersion).toBe(2);
    expect(rendered).not.toContain("private-project");
    expect(rendered).not.toContain("private-notes");
    expect(rendered).not.toContain("Nonpublic details");

    for (const collection of [
      "projects",
      "evidence",
      "technologies",
      "disciplines",
      "links",
    ]) {
      const records = document[collection] as MutableRecord[];
      expect(records.every((record) => !("public" in record))).toBe(true);
    }
  });

  test("all rendered references resolve inside the projected document", async () => {
    const { projectPublicProfile } = await projectionModule();
    const profile = projectPublicProfile(parsedProjectionDocument());

    const projectIds = new Set(profile.projects.map((record) => record.id));
    const evidenceIds = new Set(profile.evidence.map((record) => record.id));
    const technologyIds = new Set(
      profile.technologies.map((record) => record.id),
    );
    const linkIds = new Set(profile.links.map((record) => record.id));

    for (const project of profile.projects) {
      expect(
        project.technologyIds.every((id) => technologyIds.has(id)),
      ).toBe(true);
      expect(
        project.evidenceIds.every((id) => evidenceIds.has(id)),
      ).toBe(true);
      expect(project.linkIds.every((id) => linkIds.has(id))).toBe(true);
    }

    for (const technology of profile.technologies) {
      expect(
        technology.projectIds.every((id) => projectIds.has(id)),
      ).toBe(true);
      expect(
        technology.evidenceIds.every((id) => evidenceIds.has(id)),
      ).toBe(true);
    }
  });

  test("rendering is byte-stable and preserves the accepted repository artifact", async () => {
    const { projectPublicProfile, renderPublicProfile } =
      await projectionModule();
    const source = loadProfileSource(repositoryProfilePath);
    const profile = projectPublicProfile(source);
    const first = renderPublicProfile(profile);
    const second = renderPublicProfile(profile);
    const committed = readFileSync(committedFrontendProfilePath, "utf8");

    expect(first).toBe(second);
    expect(first.endsWith("\n")).toBe(true);
    expect(first).toBe(committed);
  });
});
