import { render, screen } from "@testing-library/react";
import { Component } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SceneFailureBoundary } from "@/components/scene/scene-failure-boundary";

class FailingScene extends Component {
  public render(): never {
    throw new Error("scene initialization failed");
  }
}

describe("SceneFailureBoundary", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("preserves a semantic route when the scene fails", () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);

    render(
      <SceneFailureBoundary>
        <FailingScene />
      </SceneFailureBoundary>,
    );

    expect(
      screen.getByRole("heading", {
        level: 2,
        name: "Control Room overview",
      }),
    ).toBeVisible();

    expect(
      screen.getByText(
        /semantic portfolio remains fully available/i,
      ),
    ).toBeVisible();
  });
});
