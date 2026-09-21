export type ControlRoomSurface =
  | "profile"
  | "projects"
  | "systems"
  | "evidence"
  | "contact";

export type MotionPreference = "full" | "reduced";
export type SceneQualityTier = "static" | "reduced" | "high";
export type ViewportClass = "mobile" | "tablet" | "desktop";
export type SceneFailureState = "ready" | "loading" | "unavailable";

export interface SceneState {
  activeProjectId: string | null;
  activeSurface: ControlRoomSurface;
  failureState: SceneFailureState;
  motionPreference: MotionPreference;
  qualityTier: SceneQualityTier;
  viewportClass: ViewportClass;
}

export interface AssetManifestSeed {
  fallbackId: string;
  id: string;
  qualityTier: SceneQualityTier;
  runtimePath: string | null;
}

export const initialSceneState: SceneState = {
  activeProjectId: null,
  activeSurface: "profile",
  failureState: "ready",
  motionPreference: "reduced",
  qualityTier: "static",
  viewportClass: "desktop",
};
