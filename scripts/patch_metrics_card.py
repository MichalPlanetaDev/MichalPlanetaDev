#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar


PROFILE_USER = os.environ.get(
    "PROFILE_USER",
    "MichalPlanetaDev",
).strip()

PROFILE_TOKEN = os.environ.get(
    "PROFILE_TOKEN",
    "",
).strip()

SVG_PATH = Path("github-metrics.svg")
UTC = dt.timezone.utc
T = TypeVar("T")


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

    body = None

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def safely(
    label: str,
    operation: Callable[[], T],
) -> T | None:
    try:
        return operation()
    except Exception as error:
        print(
            f"[WARN] {label} unavailable: "
            f"{type(error).__name__}: {error}"
        )
        return None


def escaped(value: object) -> str:
    return html.escape(str(value), quote=True)


def contribution_summary() -> dict[str, int]:
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

    errors = result.get("errors")
    if errors:
        raise RuntimeError(str(errors))

    collection = result["data"]["user"]["contributionsCollection"]
    days: list[dict[str, Any]] = []

    for week in collection["contributionCalendar"]["weeks"]:
        days.extend(week["contributionDays"])

    days = [
        day
        for day in days
        if dt.date.fromisoformat(day["date"]) >= start.date()
    ]

    active_days = sum(
        1
        for day in days
        if int(day["contributionCount"]) > 0
    )

    contributions = sum(
        int(day["contributionCount"])
        for day in days
    )

    streak = 0

    for day in reversed(days):
        if int(day["contributionCount"]) == 0:
            if streak:
                break
            continue

        streak += 1

    return {
        "contributions": contributions,
        "active_days": active_days,
        "streak": streak,
        "commits": int(collection["totalCommitContributions"]),
        "pull_requests": int(
            collection["totalPullRequestContributions"]
        ),
        "reviews": int(
            collection["totalPullRequestReviewContributions"]
        ),
        "issues": int(collection["totalIssueContributions"]),
    }


def achievement_summary() -> dict[str, int]:
    user = request_json(
        f"https://api.github.com/users/{PROFILE_USER}"
    )

    repositories = request_json(
        f"https://api.github.com/users/{PROFILE_USER}/repos"
        "?per_page=100&type=owner&sort=updated"
    )

    owned = [
        repository
        for repository in repositories
        if (
            not repository.get("fork", False)
            and repository.get("owner", {}).get("login", "").lower()
            == PROFILE_USER.lower()
        )
    ]

    return {
        "repositories": int(user.get("public_repos", 0)),
        "stars": sum(
            int(repository.get("stargazers_count", 0))
            for repository in owned
        ),
        "forks": sum(
            int(repository.get("forks_count", 0))
            for repository in owned
        ),
        "followers": int(user.get("followers", 0)),
    }


def icon(path: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0 0 16 16" width="16" height="16">'
        f'<path fill-rule="evenodd" d="{path}"/>'
        "</svg>"
    )


def section(
    title: str,
    heading_icon: str,
    rows: list[str],
    marker: str,
) -> str:
    row_icon = icon(
        "M8 1a7 7 0 100 14A7 7 0 008 1z"
        "m3.03 4.97a.75.75 0 00-1.06-1.06"
        "L7 7.879 5.53 6.409a.75.75 0 00-1.06 1.06"
        "l2 2a.75.75 0 001.06 0l3.5-3.5z"
    )

    row_markup = "".join(
        (
            '<div class="field">'
            f"{row_icon}"
            f"{escaped(row)}"
            "</div>"
        )
        for row in rows
    )

    return (
        f'<section data-profile-repair="{marker}">'
        '<h2 class="field">'
        f"{icon(heading_icon)}"
        f"{escaped(title)}"
        "</h2>"
        f"{row_markup}"
        "</section>"
    )


def section_bounds(
    svg: str,
    heading: str,
) -> tuple[int, int] | None:
    heading_position = svg.find(heading)

    if heading_position < 0:
        return None

    start = svg.rfind("<section", 0, heading_position)
    end = svg.find("</section>", heading_position)

    if start < 0 or end < 0:
        return None

    return start, end + len("</section>")


def ensure_minimum_height(
    svg: str,
    minimum_height: int,
) -> str:
    pattern = re.compile(
        r'(<svg\b[^>]*\bheight=")(\d+)(")',
        re.DOTALL,
    )

    match = pattern.search(svg)

    if not match:
        print("[WARN] Root SVG height was not found")
        return svg

    current_height = int(match.group(2))

    if current_height >= minimum_height:
        return svg

    return (
        svg[: match.start()]
        + match.group(1)
        + str(minimum_height)
        + match.group(3)
        + svg[match.end() :]
    )


def widen_language_bar(svg: str) -> str:
    pattern = re.compile(
        r'<svg class="bar"\s+'
        r'xmlns="http://www\.w3\.org/2000/svg"'
        r'[^>]*>',
        re.DOTALL,
    )

    replacement = (
        '<svg class="bar" '
        'xmlns="http://www.w3.org/2000/svg" '
        'width="780" '
        'height="10" '
        'viewBox="0 0 460 8" '
        'preserveAspectRatio="none" '
        'style="display:block; margin:6px auto 8px; '
        'overflow:hidden; border-radius:5px;">'
    )

    updated_svg, replacement_count = pattern.subn(
        replacement,
        svg,
        count=1,
    )

    if replacement_count == 0:
        print(
            "[WARN] Language bar was not found; "
            "the original Metrics layout was preserved"
        )
        return svg

    return updated_svg


def insert_sections(
    svg: str,
    habits: str,
    achievements: str,
    personality: str,
) -> str:
    music_bounds = section_bounds(svg, "Recently played")

    if music_bounds is not None:
        music_start, music_end = music_bounds
        return (
            svg[:music_start]
            + habits
            + svg[music_start:music_end]
            + achievements
            + personality
            + svg[music_end:]
        )

    footer_position = svg.find("<footer>")

    if footer_position >= 0:
        return (
            svg[:footer_position]
            + habits
            + achievements
            + personality
            + svg[footer_position:]
        )

    foreign_object_end = svg.find("</foreignObject>")

    if foreign_object_end >= 0:
        return (
            svg[:foreign_object_end]
            + habits
            + achievements
            + personality
            + svg[foreign_object_end:]
        )

    raise RuntimeError(
        "Could not locate a safe insertion point in github-metrics.svg"
    )


def main() -> None:
    if not SVG_PATH.is_file():
        raise RuntimeError("github-metrics.svg does not exist")

    activity = safely(
        "GitHub contribution summary",
        contribution_summary,
    )

    achievements_data = safely(
        "GitHub achievement summary",
        achievement_summary,
    )

    if activity is None:
        habit_rows = [
            "Contribution data temporarily unavailable"
        ]
    else:
        habit_rows = [
            (
                f'{activity["contributions"]} contributions · '
                f'{activity["active_days"]}/14 active days · '
                f'{activity["streak"]}-day streak'
            ),
            (
                f'{activity["commits"]} commits · '
                f'{activity["pull_requests"]} pull requests · '
                f'{activity["reviews"]} reviews'
            ),
        ]

    if achievements_data is None:
        achievement_rows = [
            "Repository data temporarily unavailable"
        ]
    else:
        achievement_rows = [
            (
                f'{achievements_data["repositories"]} repositories · '
                f'{achievements_data["stars"]} stars · '
                f'{achievements_data["forks"]} forks · '
                f'{achievements_data["followers"]} followers'
            )
        ]

    habits = section(
        "Recent coding habits",
        (
            "M8 1.5a4.5 4.5 0 00-2.8 8.02"
            "c.34.27.55.66.55 1.1v.63h4.5v-.63"
            "c0-.44.21-.83.55-1.1A4.5 4.5 0 008 1.5z"
            "m-2.25 11.25h4.5v1.5h-4.5v-1.5z"
        ),
        habit_rows,
        "habits",
    )

    achievements_section = section(
        "Achievements",
        (
            "M5 2h6v2h3v2c0 2-1.2 3.4-3 3.8"
            "V12h2v2H3v-2h2V9.8C3.2 9.4 2 8 2 6"
            "V4h3V2zm-1 4c0 .9.4 1.5 1 1.8V6H4"
            "zm7 1.8c.6-.3 1-.9 1-1.8h-1v1.8z"
        ),
        achievement_rows,
        "achievements",
    )

    personality = section(
        "Personality",
        (
            "M8 1a7 7 0 100 14A7 7 0 008 1z"
            "M5.25 6.5a1 1 0 110-2 1 1 0 010 2z"
            "m5.5 0a1 1 0 110-2 1 1 0 010 2z"
            "M4.5 9h7a3.5 3.5 0 01-7 0z"
        ),
        [
            (
                "INTJ-T · Architect · Introverted · Intuitive · "
                "Thinking · Judging · Turbulent"
            )
        ],
        "personality",
    )

    svg = SVG_PATH.read_text(encoding="utf-8")
    svg = widen_language_bar(svg)

    svg = re.sub(
        (
            r'<section data-profile-repair="'
            r'(?:habits|achievements|personality)'
            r'">.*?</section>'
        ),
        "",
        svg,
        flags=re.DOTALL,
    )

    svg = insert_sections(
        svg,
        habits,
        achievements_section,
        personality,
    )

    svg = ensure_minimum_height(svg, 560)

    if "Unexpected error" in svg:
        raise RuntimeError(
            "The generated SVG still contains Unexpected error"
        )

    SVG_PATH.write_text(svg, encoding="utf-8")

    print(
        "[PASS] Repaired github-metrics.svg with stable "
        "habits, achievements and personality sections"
    )


if __name__ == "__main__":
    main()
