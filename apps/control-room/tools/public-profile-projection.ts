import type {
  PublicDiscipline,
  PublicEvidence,
  PublicLink,
  PublicProfile,
  PublicProject,
  PublicTechnology,
} from "../src/lib/public-profile-contract.ts";
import {
  ProfileSourceError,
  type ProfileSource,
} from "./profile-source.ts";

function byIdentifier<T extends { id: string }>(
  left: T,
  right: T,
): number {
  return left.id.localeCompare(right.id);
}

function publicEvidence(source: ProfileSource): PublicEvidence[] {
  const links = new Set(
    source.links.filter((link) => link.public).map((link) => link.id),
  );

  return source.evidence
    .filter((record) => record.public)
    .map((record) => {
      if (record.linkId !== null && !links.has(record.linkId)) {
        throw new ProfileSourceError(
          `Public evidence ${record.id} depends on nonpublic link ${record.linkId}`,
        );
      }

      return {
        id: record.id,
        kind: record.kind,
        label: record.label,
        linkId: record.linkId,
        summary: record.summary,
      };
    })
    .sort(byIdentifier);
}

function publicLinks(source: ProfileSource): PublicLink[] {
  return source.links
    .filter((link) => link.public)
    .map((link) => ({
      id: link.id,
      kind: link.kind,
      label: link.label,
      url: link.url,
    }))
    .sort(byIdentifier);
}

function publicProjects(
  source: ProfileSource,
  publicEvidenceIds: ReadonlySet<string>,
  publicTechnologyIds: ReadonlySet<string>,
  publicLinkIds: ReadonlySet<string>,
): PublicProject[] {
  return source.projects
    .filter((project) => project.public && project.status !== "unpublished")
    .map((project) => {
      const evidenceIds = project.evidenceIds.filter((identifier) =>
        publicEvidenceIds.has(identifier),
      );

      if (evidenceIds.length === 0) {
        throw new ProfileSourceError(
          `Public project ${project.id} has no public evidence`,
        );
      }

      return {
        evidenceIds,
        featured: project.featured,
        id: project.id,
        linkIds: project.linkIds.filter((identifier) =>
          publicLinkIds.has(identifier),
        ),
        name: project.name,
        priority: project.priority,
        status: project.status,
        summary: project.summary,
        technologyIds: project.technologyIds.filter((identifier) =>
          publicTechnologyIds.has(identifier),
        ),
      };
    })
    .sort(
      (left, right) =>
        left.priority - right.priority || left.id.localeCompare(right.id),
    );
}

function publicTechnologies(
  source: ProfileSource,
  publicProjectIds: ReadonlySet<string>,
  publicEvidenceIds: ReadonlySet<string>,
): PublicTechnology[] {
  return source.technologies
    .filter((technology) => technology.public)
    .map((technology) => {
      const projectIds = technology.projectIds.filter((identifier) =>
        publicProjectIds.has(identifier),
      );
      const evidenceIds = technology.evidenceIds.filter((identifier) =>
        publicEvidenceIds.has(identifier),
      );

      if (projectIds.length === 0 && evidenceIds.length === 0) {
        throw new ProfileSourceError(
          `Public technology ${technology.id} has no public dependency`,
        );
      }

      return {
        category: technology.category,
        evidenceIds,
        id: technology.id,
        name: technology.name,
        projectIds,
        usage: technology.usage,
      };
    })
    .sort(byIdentifier);
}

function publicDisciplines(
  source: ProfileSource,
  publicProjectIds: ReadonlySet<string>,
  publicEvidenceIds: ReadonlySet<string>,
): PublicDiscipline[] {
  return source.disciplines
    .filter((discipline) => discipline.public)
    .map((discipline) => {
      const projectIds = discipline.projectIds.filter((identifier) =>
        publicProjectIds.has(identifier),
      );
      const evidenceIds = discipline.evidenceIds.filter((identifier) =>
        publicEvidenceIds.has(identifier),
      );

      if (projectIds.length === 0 && evidenceIds.length === 0) {
        throw new ProfileSourceError(
          `Public discipline ${discipline.id} has no public dependency`,
        );
      }

      return {
        evidenceIds,
        id: discipline.id,
        name: discipline.name,
        projectIds,
        summary: discipline.summary,
      };
    })
    .sort(byIdentifier);
}

export function projectPublicProfile(source: ProfileSource): PublicProfile {
  const evidence = publicEvidence(source);
  const links = publicLinks(source);
  const publicEvidenceIds = new Set(evidence.map((record) => record.id));
  const publicLinkIds = new Set(links.map((record) => record.id));
  const publicTechnologyIds = new Set(
    source.technologies
      .filter((technology) => technology.public)
      .map((technology) => technology.id),
  );
  const projects = publicProjects(
    source,
    publicEvidenceIds,
    publicTechnologyIds,
    publicLinkIds,
  );
  const publicProjectIds = new Set(projects.map((project) => project.id));

  return {
    disciplines: publicDisciplines(
      source,
      publicProjectIds,
      publicEvidenceIds,
    ),
    displayName: source.displayName,
    environmentId: source.environmentId,
    evidence,
    generator: {
      name: "profile-system",
      version: "0.1.0",
    },
    identity: {
      headline: source.identity.headline,
      motto: source.identity.motto,
      role: source.identity.role,
      summary: source.identity.summary,
    },
    links,
    profileId: source.profileId,
    projects,
    schemaVersion: 1,
    sourceSchemaVersion: source.schemaVersion,
    technologies: publicTechnologies(
      source,
      publicProjectIds,
      publicEvidenceIds,
    ),
  };
}

export function renderPublicProfile(profile: PublicProfile): string {
  return `${JSON.stringify(profile, null, 2)}\n`;
}
