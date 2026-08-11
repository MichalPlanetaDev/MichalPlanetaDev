import generatedProfile from "@/generated/public-profile.json";

import type { PublicProfile } from "./public-profile-contract";

export type {
  PublicDiscipline,
  PublicEvidence,
  PublicIdentity,
  PublicLink,
  PublicProfile,
  PublicProject,
  PublicTechnology,
} from "./public-profile-contract";

export const publicProfile: PublicProfile = generatedProfile;

if (publicProfile.schemaVersion !== 1) {
  throw new Error(
    `Unsupported frontend profile schema: ${publicProfile.schemaVersion}`,
  );
}
