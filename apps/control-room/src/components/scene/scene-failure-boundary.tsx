"use client";

import type { ReactNode } from "react";
import { Component } from "react";

interface SceneFailureBoundaryProps {
  children: ReactNode;
}

interface SceneFailureBoundaryState {
  failed: boolean;
}

export class SceneFailureBoundary extends Component<
  SceneFailureBoundaryProps,
  SceneFailureBoundaryState
> {
  public state: SceneFailureBoundaryState = {
    failed: false,
  };

  public static getDerivedStateFromError(): SceneFailureBoundaryState {
    return {
      failed: true,
    };
  }

  public render(): ReactNode {
    if (this.state.failed) {
      return (
        <section
          className="scene-fallback"
          aria-labelledby="scene-fallback-title"
        >
          <p className="eyebrow">Spatial layer unavailable</p>
          <h2 id="scene-fallback-title">Control Room overview</h2>
          <p>
            The semantic portfolio remains fully available through the
            profile, projects, systems, evidence, and contact sections.
          </p>
        </section>
      );
    }

    return this.props.children;
  }
}
