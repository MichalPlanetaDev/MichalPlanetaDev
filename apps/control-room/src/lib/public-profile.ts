import generatedProfile from "@/generated/public-profile.json";

export interface PublicIdentity {
  headline: string;
  motto: string;
  role: string;
  summary: string;
}

export interface PublicProject {
  evidenceIds: string[];
  featured: boolean;
  id: string;
  linkIds: string[];
  name: string;
  priority: number;
  status: string;
  summary: string;
  technologyIds: string[];
}

export interface PublicEvidence {
  id: string;
  kind: string;
  label: string;
  linkId: string | null;
  summary: string;
}

export interface PublicTechnology {
  category: string;
  evidenceIds: string[];
  id: string;
  name: string;
  projectIds: string[];
  usage: string;
}

export interface PublicDiscipline {
  evidenceIds: string[];
  id: string;
  name: string;
  projectIds: string[];
  summary: string;
}

export interface PublicLink {
  id: string;
  kind: string;
  label: string;
  url: string;
}

export interface PublicProfile {
  disciplines: PublicDiscipline[];
  displayName: string;
  environmentId: string;
  evidence: PublicEvidence[];
  generator: {
    name: string;
    version: string;
  };
  identity: PublicIdentity;
  links: PublicLink[];
  profileId: string;
  projects: PublicProject[];
  schemaVersion: number;
  sourceSchemaVersion: number;
  technologies: PublicTechnology[];
}

export const publicProfile: PublicProfile = generatedProfile;

if (publicProfile.schemaVersion !== 1) {
  throw new Error(
    `Unsupported frontend profile schema: ${publicProfile.schemaVersion}`,
  );
}
