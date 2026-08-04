import { initialSceneState } from "@/lib/scene-contract";

export function ScenePlaceholder() {
  return (
    <section
      className="scene-frame"
      aria-labelledby="scene-title"
      data-quality-tier={initialSceneState.qualityTier}
    >
      <div className="scene-architecture" aria-hidden="true">
        <div className="scene-track">
          <span className="scene-stage">Authored profile</span>
          <span className="scene-connector" />
          <span className="scene-stage">Public projection</span>
          <span className="scene-connector" />
          <span className="scene-stage">Semantic shell</span>
        </div>

        <div className="scene-field">
          <span className="scene-signal scene-signal-primary" />
          <span className="scene-signal scene-signal-secondary" />
          <span className="scene-signal scene-signal-tertiary" />
        </div>
      </div>

      <div className="scene-caption">
        <p className="eyebrow">Evidence-led foundation</p>
        <h2 id="scene-title">
          From validated profile data to a usable interface
        </h2>
        <p>
          The visible identity, projects, and evidence come from one public
          projection. The future spatial layer remains optional, so the
          portfolio stays complete when 3D is unavailable.
        </p>
      </div>
    </section>
  );
}
