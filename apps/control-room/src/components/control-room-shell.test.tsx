import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ControlRoomShell } from "@/components/control-room-shell";
import { publicProfile } from "@/lib/public-profile";

describe("ControlRoomShell", () => {
  it("renders one semantic identity heading and complete navigation", () => {
    const { container } = render(
      <ControlRoomShell profile={publicProfile} />,
    );

    expect(container.querySelectorAll("h1")).toHaveLength(1);
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: publicProfile.displayName,
      }),
    ).toBeVisible();

    for (const label of [
      "Profile",
      "Projects",
      "Systems",
      "Evidence",
      "Contact",
    ]) {
      expect(
        screen.getByRole("link", {
          name: label,
        }),
      ).toBeVisible();
    }
  });

  it("keeps projects, evidence, and contact outside the scene layer", () => {
    const { container } = render(
      <ControlRoomShell profile={publicProfile} />,
    );

    expect(container.querySelector("canvas")).not.toBeInTheDocument();

    for (const project of publicProfile.projects) {
      expect(
        screen.getByRole("heading", {
          level: 3,
          name: project.name,
        }),
      ).toBeVisible();
    }

    expect(
      screen.getByRole("heading", {
        level: 2,
        name: "Evidence before claims",
      }),
    ).toBeVisible();

    const contactSection = container.querySelector("#contact");

    expect(contactSection).not.toBeNull();

    const contactLinks = within(contactSection as HTMLElement);

    for (const link of publicProfile.links) {
      expect(
        contactLinks.getByRole("link", {
          name: link.label,
        }),
      ).toHaveAttribute("href", link.url);
    }
  });
});
