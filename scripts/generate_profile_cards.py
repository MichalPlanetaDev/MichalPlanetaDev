#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


PROFILE_USER = os.environ.get(
    "PROFILE_USER",
    "MichalPlanetaDev",
).strip()

PROFILE_TOKEN = os.environ.get(
    "PROFILE_TOKEN",
    "",
).strip()

PERSONALITY_URL = os.environ.get(
    "PERSONALITY_URL",
    "",
).strip()

UTC = dt.timezone.utc


def request_json(
    url: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{PROFILE_USER}-profile-metrics",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if PROFILE_TOKEN:
        headers["Authorization"] = f"Bearer {PROFILE_TOKEN}"

    data = None

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def request_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "pl,en;q=0.8",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 Chrome/124 Safari/537.36"
            ),
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        return response.read().decode(
            "utf-8",
            errors="replace",
        )


def xml(value: object) -> str:
    return html.escape(
        str(value),
        quote=True,
    )


def compact(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"

    if value >= 1_000:
        return f"{value / 1_000:.1f}K"

    return str(value)


def create_card(
    output_path: Path,
    title: str,
    subtitle: str,
    metrics: list[tuple[str, str, str]],
    footer: str,
    accent: str,
) -> None:
    width = 900
    height = 250
    padding = 24
    gap = 12

    box_width = (
        width
        - 2 * padding
        - gap * (len(metrics) - 1)
    ) / len(metrics)

    boxes: list[str] = []

    for index, (label, value, detail) in enumerate(metrics):
        x = padding + index * (box_width + gap)

        boxes.append(
            f"""
            <g transform="translate({x:.2f},100)">
              <rect
                class="box"
                width="{box_width:.2f}"
                height="92"
                rx="10"
              />

              <text
                class="label"
                x="14"
                y="24"
              >{xml(label)}</text>

              <text
                class="value"
                x="14"
                y="56"
              >{xml(value)}</text>

              <text
                class="detail"
                x="14"
                y="78"
              >{xml(detail)}</text>
            </g>
            """
        )

    svg = f"""<svg
      xmlns="http://www.w3.org/2000/svg"
      width="100%"
      height="{height}"
      viewBox="0 0 {width} {height}"
      role="img"
    >
      <style>
        :root {{
          --background: #0d1117;
          --panel: #161b22;
          --border: #30363d;
          --primary: #f0f6fc;
          --secondary: #8b949e;
        }}

        @media (prefers-color-scheme: light) {{
          :root {{
            --background: #ffffff;
            --panel: #f6f8fa;
            --border: #d0d7de;
            --primary: #1f2328;
            --secondary: #59636e;
          }}
        }}

        text {{
          font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            Helvetica,
            Arial,
            sans-serif;
        }}

        .background {{
          fill: var(--background);
          stroke: var(--border);
        }}

        .box {{
          fill: var(--panel);
          stroke: var(--border);
        }}

        .title {{
          fill: var(--primary);
          font-size: 24px;
          font-weight: 700;
        }}

        .subtitle,
        .label,
        .detail,
        .footer {{
          fill: var(--secondary);
        }}

        .subtitle {{
          font-size: 14px;
        }}

        .label {{
          font-size: 12px;
          font-weight: 600;
        }}

        .value {{
          fill: var(--primary);
          font-size: 23px;
          font-weight: 700;
        }}

        .detail,
        .footer {{
          font-size: 11px;
        }}
      </style>

      <rect
        class="background"
        x="0.5"
        y="0.5"
        width="{width - 1}"
        height="{height - 1}"
        rx="13"
      />

      <rect
        x="24"
        y="23"
        width="5"
        height="48"
        rx="2.5"
        fill="{accent}"
      />

      <text
        class="title"
        x="43"
        y="44"
      >{xml(title)}</text>

      <text
        class="subtitle"
        x="43"
        y="68"
      >{xml(subtitle)}</text>

      {''.join(boxes)}

      <text
        class="footer"
        x="24"
        y="225"
      >{xml(footer)}</text>
    </svg>
    """

    output_path.write_text(
        svg,
        encoding="utf-8",
    )


def generate_coding_activity() -> None:
    now = dt.datetime.now(UTC)
    start = now - dt.timedelta(days=13)

    query = """
    query(
      $login: String!,
      $from: DateTime!,
      $to: DateTime!
    ) {
      user(login: $login) {
        contributionsCollection(
          from: $from,
          to: $to
        ) {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          restrictedContributionsCount

          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """

    result = request_json(
        "https://api.github.com/graphql",
        {
            "query": query,
            "variables": {
                "login": PROFILE_USER,
                "from": start.isoformat(),
                "to": now.isoformat(),
            },
        },
    )

    collection = (
        result["data"]
        ["user"]
        ["contributionsCollection"]
    )

    days: list[dict[str, Any]] = []

    for week in collection[
        "contributionCalendar"
    ]["weeks"]:
        days.extend(
            week["contributionDays"]
        )

    days = [
        day
        for day in days
        if dt.date.fromisoformat(
            day["date"]
        ) >= start.date()
    ]

    total_contributions = sum(
        int(day["contributionCount"])
        for day in days
    )

    active_days = sum(
        1
        for day in days
        if int(day["contributionCount"]) > 0
    )

    current_streak = 0

    for day in reversed(days):
        if int(day["contributionCount"]) == 0:
            if current_streak:
                break

            continue

        current_streak += 1

    pull_request_activity = (
        int(
            collection[
                "totalPullRequestContributions"
            ]
        )
        + int(
            collection[
                "totalPullRequestReviewContributions"
            ]
        )
    )

    private_contributions = int(
        collection[
            "restrictedContributionsCount"
        ]
    )

    private_detail = (
        f"{private_contributions} private"
        if private_contributions
        else "public activity"
    )

    create_card(
        Path("coding-activity.svg"),
        "Recent coding activity",
        "Stable fourteen-day activity calculated directly from GitHub",
        [
            (
                "Contributions",
                compact(total_contributions),
                "last 14 days",
            ),
            (
                "Active days",
                f"{active_days}/14",
                "days with activity",
            ),
            (
                "Current streak",
                f"{current_streak} d",
                "consecutive days",
            ),
            (
                "Commits",
                compact(
                    int(
                        collection[
                            "totalCommitContributions"
                        ]
                    )
                ),
                private_detail,
            ),
            (
                "PRs and reviews",
                compact(
                    pull_request_activity
                ),
                (
                    f'{collection["totalIssueContributions"]} '
                    "issues"
                ),
            ),
        ],
        (
            "Independent replacement for the unstable "
            "Metrics coding-habits plugin."
        ),
        "#2f81f7",
    )


def generate_engineering_achievements() -> None:
    user = request_json(
        f"https://api.github.com/users/{PROFILE_USER}"
    )

    repositories = request_json(
        f"https://api.github.com/users/{PROFILE_USER}/repos"
        "?per_page=100&type=owner&sort=updated"
    )

    owned_repositories = [
        repository
        for repository in repositories
        if (
            not repository.get("fork", False)
            and repository.get(
                "owner",
                {},
            ).get(
                "login",
                "",
            ).lower()
            == PROFILE_USER.lower()
        )
    ]

    stars = sum(
        int(
            repository.get(
                "stargazers_count",
                0,
            )
        )
        for repository in owned_repositories
    )

    forks = sum(
        int(
            repository.get(
                "forks_count",
                0,
            )
        )
        for repository in owned_repositories
    )

    languages = {
        repository["language"]
        for repository in owned_repositories
        if repository.get("language")
    }

    create_card(
        Path("engineering-achievements.svg"),
        "Engineering achievements",
        (
            "Repository-level results calculated "
            "from owned public projects"
        ),
        [
            (
                "Public repos",
                compact(
                    int(
                        user.get(
                            "public_repos",
                            0,
                        )
                    )
                ),
                "visible projects",
            ),
            (
                "Stars earned",
                compact(stars),
                "across repositories",
            ),
            (
                "Repository forks",
                compact(forks),
                "external reuse",
            ),
            (
                "Followers",
                compact(
                    int(
                        user.get(
                            "followers",
                            0,
                        )
                    )
                ),
                "GitHub audience",
            ),
            (
                "Languages",
                compact(
                    len(languages)
                ),
                "primary languages",
            ),
        ],
        (
            "Independent replacement for the unstable "
            "Metrics achievements plugin."
        ),
        "#f85149",
    )


def detect_personality() -> tuple[str, list[tuple[str, str, str]]]:
    personality_type = "INTJ"
    page_text = ""

    if PERSONALITY_URL:
        try:
            page_html = request_text(
                PERSONALITY_URL
            )

            type_match = re.search(
                r"\b(INTJ(?:-[AT])?)\b",
                page_html,
                flags=re.IGNORECASE,
            )

            if type_match:
                personality_type = (
                    type_match
                    .group(1)
                    .upper()
                )

            page_text = html.unescape(
                re.sub(
                    r"<[^>]+>",
                    " ",
                    page_html,
                )
            )

        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
        ):
            page_text = ""

    axes = [
        (
            "Mind",
            "Introverted",
            "Extraverted",
        ),
        (
            "Energy",
            "Intuitive",
            "Observant",
        ),
        (
            "Nature",
            "Thinking",
            "Feeling",
        ),
        (
            "Tactics",
            "Judging",
            "Prospecting",
        ),
        (
            "Identity",
            (
                "Assertive"
                if personality_type.endswith("-A")
                else "Turbulent"
                if personality_type.endswith("-T")
                else "Profile-specific"
            ),
            "",
        ),
    ]

    metrics: list[tuple[str, str, str]] = []

    for axis, primary, secondary in axes:
        detected_value = None
        detected_trait = primary

        if page_text:
            for trait in filter(
                None,
                (primary, secondary),
            ):
                patterns = [
                    (
                        rf"(\d{{1,3}})\s*%"
                        rf".{{0,80}}?{re.escape(trait)}"
                    ),
                    (
                        rf"{re.escape(trait)}"
                        rf".{{0,80}}?"
                        rf"(\d{{1,3}})\s*%"
                    ),
                ]

                for pattern in patterns:
                    match = re.search(
                        pattern,
                        page_text,
                        flags=(
                            re.IGNORECASE
                            | re.DOTALL
                        ),
                    )

                    if match:
                        percentage = int(
                            match.group(1)
                        )

                        if 0 <= percentage <= 100:
                            detected_value = (
                                f"{percentage}%"
                            )

                            detected_trait = trait
                            break

                if detected_value:
                    break

        metrics.append(
            (
                axis,
                detected_value or primary,
                detected_trait,
            )
        )

    return personality_type, metrics


def generate_personality_profile() -> None:
    personality_type, metrics = detect_personality()

    create_card(
        Path("personality-profile.svg"),
        f"Personality profile — {personality_type}",
        (
            "Shared 16Personalities result represented "
            "without the unstable Metrics plugin"
        ),
        metrics,
        "Personal profile URL is stored as a GitHub Actions secret.",
        "#a371f7",
    )


def main() -> None:
    generate_coding_activity()
    generate_engineering_achievements()
    generate_personality_profile()

    for output_path in (
        Path("coding-activity.svg"),
        Path("engineering-achievements.svg"),
        Path("personality-profile.svg"),
    ):
        if (
            not output_path.is_file()
            or output_path.stat().st_size == 0
        ):
            raise RuntimeError(
                f"Missing generated SVG: {output_path}"
            )

        print(
            f"[PASS] Generated {output_path}"
        )


if __name__ == "__main__":
    main()
