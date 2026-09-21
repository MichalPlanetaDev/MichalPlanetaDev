import { readFileSync } from "node:fs";

export type ProjectStatus =
  | "completed"
  | "active"
  | "experimental"
  | "unpublished";

export type EvidenceKind =
  | "repository"
  | "demo"
  | "documentation"
  | "tests"
  | "architecture"
  | "benchmark"
  | "diagram"
  | "artifact";

export type TechnologyCategory =
  | "language"
  | "framework"
  | "runtime"
  | "database"
  | "graphics"
  | "testing"
  | "automation"
  | "tool"
  | "platform";

export type LinkKind =
  | "repository"
  | "demo"
  | "documentation"
  | "profile"
  | "contact"
  | "artifact";

export interface ProfileIdentitySource {
  headline: string;
  role: string;
  motto: string;
  summary: string;
}

export interface ProjectSource {
  id: string;
  name: string;
  summary: string;
  status: ProjectStatus;
  public: boolean;
  featured: boolean;
  priority: number;
  technologyIds: string[];
  evidenceIds: string[];
  linkIds: string[];
}

export interface EvidenceSource {
  id: string;
  kind: EvidenceKind;
  label: string;
  summary: string;
  public: boolean;
  linkId: string | null;
}

export interface TechnologySource {
  id: string;
  name: string;
  category: TechnologyCategory;
  usage: string;
  public: boolean;
  projectIds: string[];
  evidenceIds: string[];
}

export interface DisciplineSource {
  id: string;
  name: string;
  summary: string;
  public: boolean;
  projectIds: string[];
  evidenceIds: string[];
}

export interface LinkSource {
  id: string;
  label: string;
  kind: LinkKind;
  url: string;
  public: boolean;
}

export interface ProfileSource {
  schemaVersion: 2;
  profileId: string;
  displayName: string;
  environmentId: string;
  identity: ProfileIdentitySource;
  projects: ProjectSource[];
  evidence: EvidenceSource[];
  technologies: TechnologySource[];
  disciplines: DisciplineSource[];
  links: LinkSource[];
}

export class ProfileSourceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ProfileSourceError";
  }
}

type SourceObject = Record<string, unknown>;

type IdentifiedSource =
  | ProjectSource
  | EvidenceSource
  | TechnologySource
  | DisciplineSource
  | LinkSource;

const supportedSchemaVersion = 2 as const;
const identifierPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const projectStatuses = new Set<ProjectStatus>([
  "completed",
  "active",
  "experimental",
  "unpublished",
]);

const evidenceKinds = new Set<EvidenceKind>([
  "repository",
  "demo",
  "documentation",
  "tests",
  "architecture",
  "benchmark",
  "diagram",
  "artifact",
]);

const technologyCategories = new Set<TechnologyCategory>([
  "language",
  "framework",
  "runtime",
  "database",
  "graphics",
  "testing",
  "automation",
  "tool",
  "platform",
]);

const linkKinds = new Set<LinkKind>([
  "repository",
  "demo",
  "documentation",
  "profile",
  "contact",
  "artifact",
]);

function requireObject(value: unknown, context: string): SourceObject {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new ProfileSourceError(`${context} must contain a JSON object`);
  }

  return value as SourceObject;
}

function requireArray(value: unknown, context: string): unknown[] {
  if (!Array.isArray(value)) {
    throw new ProfileSourceError(`${context} must contain a JSON array`);
  }

  return value;
}

function requireExactFields(
  source: SourceObject,
  expectedFields: readonly string[],
  context: string,
): void {
  const expected = new Set(expectedFields);
  const actualFields = Object.keys(source);
  const missing = expectedFields
    .filter((field) => !(field in source))
    .sort();
  const unsupported = actualFields
    .filter((field) => !expected.has(field))
    .sort();

  if (missing.length > 0) {
    throw new ProfileSourceError(
      `${context} is missing fields: ${missing.join(", ")}`,
    );
  }

  if (unsupported.length > 0) {
    throw new ProfileSourceError(
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
    throw new ProfileSourceError(
      `${context}.${field} must contain a non-empty string`,
    );
  }

  return value.trim();
}

function requireBoolean(
  source: SourceObject,
  field: string,
  context: string,
): boolean {
  const value = source[field];

  if (typeof value !== "boolean") {
    throw new ProfileSourceError(
      `${context}.${field} must contain a boolean`,
    );
  }

  return value;
}

function requireNonNegativeInteger(
  source: SourceObject,
  field: string,
  context: string,
): number {
  const value = source[field];

  if (
    typeof value !== "number" ||
    !Number.isInteger(value) ||
    value < 0
  ) {
    throw new ProfileSourceError(
      `${context}.${field} must contain a non-negative integer`,
    );
  }

  return value;
}

function requireIdentifier(value: string, context: string): string {
  if (!identifierPattern.test(value)) {
    throw new ProfileSourceError(
      `${context} must use a lowercase kebab-case identifier`,
    );
  }

  return value;
}

function requireIdentifierField(
  source: SourceObject,
  field: string,
  context: string,
): string {
  return requireIdentifier(
    requireText(source, field, context),
    `${context}.${field}`,
  );
}

function requireIdentifierArray(
  source: SourceObject,
  field: string,
  context: string,
): string[] {
  const values = requireArray(source[field], `${context}.${field}`);
  const identifiers: string[] = [];
  const seen = new Set<string>();

  for (const [index, value] of values.entries()) {
    const itemContext = `${context}.${field}[${index}]`;

    if (typeof value !== "string") {
      throw new ProfileSourceError(
        `${itemContext} must contain a string`,
      );
    }

    const identifier = requireIdentifier(value.trim(), itemContext);

    if (seen.has(identifier)) {
      throw new ProfileSourceError(
        `Duplicate reference in ${context}.${field}: ${identifier}`,
      );
    }

    seen.add(identifier);
    identifiers.push(identifier);
  }

  return identifiers;
}

function requireChoice<T extends string>(
  source: SourceObject,
  field: string,
  context: string,
  choices: ReadonlySet<T>,
): T {
  const value = requireText(source, field, context);

  if (!choices.has(value as T)) {
    throw new ProfileSourceError(
      `Unsupported ${context}.${field}: ${value}`,
    );
  }

  return value as T;
}

function validateLinkUrl(
  kind: LinkKind,
  url: string,
  context: string,
): void {
  let parsed: URL;

  try {
    parsed = new URL(url);
  } catch {
    throw new ProfileSourceError(
      `${context}.url must contain an absolute https URL or contact mailto URL`,
    );
  }

  if (
    parsed.protocol === "https:" &&
    /^https:\/\//i.test(url) &&
    parsed.host.length > 0
  ) {
    return;
  }

  if (kind === "contact" && parsed.protocol === "mailto:") {
    const mailPath = parsed.pathname;
    const atCount = [...mailPath].filter((character) => character === "@").length;

    if (parsed.host.length === 0 && atCount === 1) {
      return;
    }
  }

  throw new ProfileSourceError(
    `${context}.url must contain an absolute https URL or contact mailto URL`,
  );
}

function parseIdentity(value: unknown): ProfileIdentitySource {
  const context = "Profile source.identity";
  const source = requireObject(value, context);

  requireExactFields(
    source,
    ["headline", "role", "motto", "summary"],
    context,
  );

  return {
    headline: requireText(source, "headline", context),
    role: requireText(source, "role", context),
    motto: requireText(source, "motto", context),
    summary: requireText(source, "summary", context),
  };
}

function parseProjects(value: unknown): ProjectSource[] {
  return requireArray(value, "Profile source.projects").map(
    (rawProject, index) => {
      const context = `Profile source.projects[${index}]`;
      const source = requireObject(rawProject, context);

      requireExactFields(
        source,
        [
          "id",
          "name",
          "summary",
          "status",
          "public",
          "featured",
          "priority",
          "technologyIds",
          "evidenceIds",
          "linkIds",
        ],
        context,
      );

      const status = requireChoice(
        source,
        "status",
        context,
        projectStatuses,
      );
      const isPublic = requireBoolean(source, "public", context);
      const featured = requireBoolean(source, "featured", context);
      const id = requireIdentifierField(source, "id", context);

      if (status === "unpublished" && isPublic) {
        throw new ProfileSourceError(
          `Project ${id} with status unpublished must not be public`,
        );
      }

      if (!isPublic && featured) {
        throw new ProfileSourceError(
          `Project ${id} must not be featured when public is false`,
        );
      }

      return {
        id,
        name: requireText(source, "name", context),
        summary: requireText(source, "summary", context),
        status,
        public: isPublic,
        featured,
        priority: requireNonNegativeInteger(source, "priority", context),
        technologyIds: requireIdentifierArray(
          source,
          "technologyIds",
          context,
        ),
        evidenceIds: requireIdentifierArray(source, "evidenceIds", context),
        linkIds: requireIdentifierArray(source, "linkIds", context),
      };
    },
  );
}

function parseEvidence(value: unknown): EvidenceSource[] {
  return requireArray(value, "Profile source.evidence").map(
    (rawEvidence, index) => {
      const context = `Profile source.evidence[${index}]`;
      const source = requireObject(rawEvidence, context);

      requireExactFields(
        source,
        ["id", "kind", "label", "summary", "public", "linkId"],
        context,
      );

      const rawLinkId = source.linkId;
      let linkId: string | null;

      if (rawLinkId === null) {
        linkId = null;
      } else if (typeof rawLinkId === "string") {
        linkId = requireIdentifier(
          rawLinkId.trim(),
          `${context}.linkId`,
        );
      } else {
        throw new ProfileSourceError(
          `${context}.linkId must contain a string or null`,
        );
      }

      return {
        id: requireIdentifierField(source, "id", context),
        kind: requireChoice(source, "kind", context, evidenceKinds),
        label: requireText(source, "label", context),
        summary: requireText(source, "summary", context),
        public: requireBoolean(source, "public", context),
        linkId,
      };
    },
  );
}

function parseTechnologies(value: unknown): TechnologySource[] {
  return requireArray(value, "Profile source.technologies").map(
    (rawTechnology, index) => {
      const context = `Profile source.technologies[${index}]`;
      const source = requireObject(rawTechnology, context);

      requireExactFields(
        source,
        [
          "id",
          "name",
          "category",
          "usage",
          "public",
          "projectIds",
          "evidenceIds",
        ],
        context,
      );

      return {
        id: requireIdentifierField(source, "id", context),
        name: requireText(source, "name", context),
        category: requireChoice(
          source,
          "category",
          context,
          technologyCategories,
        ),
        usage: requireText(source, "usage", context),
        public: requireBoolean(source, "public", context),
        projectIds: requireIdentifierArray(source, "projectIds", context),
        evidenceIds: requireIdentifierArray(source, "evidenceIds", context),
      };
    },
  );
}

function parseDisciplines(value: unknown): DisciplineSource[] {
  return requireArray(value, "Profile source.disciplines").map(
    (rawDiscipline, index) => {
      const context = `Profile source.disciplines[${index}]`;
      const source = requireObject(rawDiscipline, context);

      requireExactFields(
        source,
        ["id", "name", "summary", "public", "projectIds", "evidenceIds"],
        context,
      );

      return {
        id: requireIdentifierField(source, "id", context),
        name: requireText(source, "name", context),
        summary: requireText(source, "summary", context),
        public: requireBoolean(source, "public", context),
        projectIds: requireIdentifierArray(source, "projectIds", context),
        evidenceIds: requireIdentifierArray(source, "evidenceIds", context),
      };
    },
  );
}

function parseLinks(value: unknown): LinkSource[] {
  return requireArray(value, "Profile source.links").map(
    (rawLink, index) => {
      const context = `Profile source.links[${index}]`;
      const source = requireObject(rawLink, context);

      requireExactFields(
        source,
        ["id", "label", "kind", "url", "public"],
        context,
      );

      const kind = requireChoice(source, "kind", context, linkKinds);
      const url = requireText(source, "url", context);
      validateLinkUrl(kind, url, context);

      return {
        id: requireIdentifierField(source, "id", context),
        label: requireText(source, "label", context),
        kind,
        url,
        public: requireBoolean(source, "public", context),
      };
    },
  );
}

function identifierMap<T extends IdentifiedSource>(
  records: readonly T[],
  collection: string,
): Map<string, T> {
  const byIdentifier = new Map<string, T>();

  for (const record of records) {
    if (byIdentifier.has(record.id)) {
      throw new ProfileSourceError(
        `Duplicate identifier in ${collection}: ${record.id}`,
      );
    }

    byIdentifier.set(record.id, record);
  }

  return byIdentifier;
}

function requireReferences(
  identifiers: readonly string[],
  available: ReadonlyMap<string, IdentifiedSource>,
  context: string,
): void {
  for (const identifier of identifiers) {
    if (!available.has(identifier)) {
      throw new ProfileSourceError(
        `Unresolved reference in ${context}: ${identifier}`,
      );
    }
  }
}

function validateReferences(profile: ProfileSource): void {
  const projects = identifierMap(profile.projects, "projects");
  const evidence = identifierMap(profile.evidence, "evidence");
  const technologies = identifierMap(
    profile.technologies,
    "technologies",
  );
  const disciplines = identifierMap(profile.disciplines, "disciplines");
  const links = identifierMap(profile.links, "links");

  const identifierOwners = new Map<string, string>();
  const collections: Array<
    readonly [string, ReadonlyMap<string, IdentifiedSource>]
  > = [
    ["projects", projects],
    ["evidence", evidence],
    ["technologies", technologies],
    ["disciplines", disciplines],
    ["links", links],
  ];

  for (const [collection, records] of collections) {
    for (const identifier of records.keys()) {
      const previousOwner = identifierOwners.get(identifier);

      if (previousOwner !== undefined) {
        throw new ProfileSourceError(
          `Duplicate global identifier ${identifier}: ${previousOwner} and ${collection}`,
        );
      }

      identifierOwners.set(identifier, collection);
    }
  }

  for (const project of profile.projects) {
    const context = `project ${project.id}`;
    requireReferences(project.technologyIds, technologies, context);
    requireReferences(project.evidenceIds, evidence, context);
    requireReferences(project.linkIds, links, context);
  }

  for (const evidenceRecord of profile.evidence) {
    if (evidenceRecord.linkId === null) {
      continue;
    }

    const link = links.get(evidenceRecord.linkId);

    if (link === undefined) {
      throw new ProfileSourceError(
        `Unresolved reference in evidence ${evidenceRecord.id}: ${evidenceRecord.linkId}`,
      );
    }

    if (evidenceRecord.public && !link.public) {
      throw new ProfileSourceError(
        `Public evidence ${evidenceRecord.id} references nonpublic link ${evidenceRecord.linkId}`,
      );
    }
  }

  for (const technology of profile.technologies) {
    const context = `technology ${technology.id}`;
    requireReferences(technology.projectIds, projects, context);
    requireReferences(technology.evidenceIds, evidence, context);
  }

  for (const discipline of profile.disciplines) {
    const context = `discipline ${discipline.id}`;
    requireReferences(discipline.projectIds, projects, context);
    requireReferences(discipline.evidenceIds, evidence, context);
  }
}

export function parseProfileSource(profileDocument: unknown): ProfileSource {
  const context = "Profile source";
  const source = requireObject(profileDocument, context);

  requireExactFields(
    source,
    [
      "schemaVersion",
      "profileId",
      "displayName",
      "environmentId",
      "identity",
      "projects",
      "evidence",
      "technologies",
      "disciplines",
      "links",
    ],
    context,
  );

  const schemaVersion = requireNonNegativeInteger(
    source,
    "schemaVersion",
    context,
  );

  if (schemaVersion !== supportedSchemaVersion) {
    throw new ProfileSourceError(
      `Unsupported schemaVersion: ${schemaVersion}`,
    );
  }

  const profile: ProfileSource = {
    schemaVersion: supportedSchemaVersion,
    profileId: requireIdentifierField(source, "profileId", context),
    displayName: requireText(source, "displayName", context),
    environmentId: requireIdentifierField(
      source,
      "environmentId",
      context,
    ),
    identity: parseIdentity(source.identity),
    projects: parseProjects(source.projects),
    evidence: parseEvidence(source.evidence),
    technologies: parseTechnologies(source.technologies),
    disciplines: parseDisciplines(source.disciplines),
    links: parseLinks(source.links),
  };

  validateReferences(profile);
  return profile;
}

export function loadProfileSource(sourcePath: string): ProfileSource {
  const document = JSON.parse(readFileSync(sourcePath, "utf8")) as unknown;
  return parseProfileSource(document);
}
