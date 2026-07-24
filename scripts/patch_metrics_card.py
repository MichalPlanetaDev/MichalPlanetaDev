#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
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

SVG_PATH = Path("github-metrics.svg")
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

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def escaped(value: object) -> str:
    return html.escape(
        str(value),
        quote=True,
    )


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
        "commits": int(
            collection[
                "totalCommitContributions"
            ]
        ),
        "pull_requests": int(
            collection[
                "totalPullRequestContributions"
            ]
        ),
        "reviews": int(
            collection[
                "totalPullRequestReviewContributions"
            ]
        ),
        "issues": int(
            collection[
                "totalIssueContributions"
            ]
        ),
    }


def achievement_summary() -> dict[str, int]:
    user = request_json(
        f"https://api.github.com/users/"
        f"{PROFILE_USER}"
    )

    repositories = request_json(
        f"https://api.github.com/users/"
        f"{PROFILE_USER}/repos"
        "?per_page=100&type=owner&sort=updated"
    )

    owned = [
        repository
        for repository in repositories
        if (
            not repository.get(
                "fork",
                False,
            )
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

    return {
        "repositories": int(
            user.get(
                "public_repos",
                0,
            )
        ),
        "stars": sum(
            int(
                repository.get(
                    "stargazers_count",
                    0,
                )
            )
            for repository in owned
        ),
        "forks": sum(
            int(
                repository.get(
                    "forks_count",
                    0,
                )
            )
            for repository in owned
        ),
        "followers": int(
            user.get(
                "followers",
                0,
            )
        ),
    }


def icon(path: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0 0 16 16" width="16" height="16">'
        f'<path fill-rule="evenodd" d="{path}"/>'
        '</svg>'
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
            f'<div class="field">'
            f'{row_icon}'
            f'{escaped(row)}'
            f'</div>'
        )
        for row in rows
    )

    return (
        f'<section data-profile-repair="{marker}">'
        f'<h2 class="field">'
        f'{icon(heading_icon)}'
        f'{escaped(title)}'
        f'</h2>'
        f'{row_markup}'
        f'</section>'
    )


def section_bounds(
    svg: str,
    heading: str,
) -> tuple[int, int] | None:
    heading_position = svg.find(heading)

    if heading_position < 0:
        return None

    start = svg.rfind(
        "<section",
        0,
        heading_position,
    )

    end = svg.find(
        "</section>",
        heading_position,
    )

    if start < 0 or end < 0:
        return None

    return (
        start,
        end + len("</section>"),
    )


def increase_height(
    svg: str,
    added_height: int,
) -> str:
    pattern = re.compile(
        r'(<svg\b[^>]*\bheight=")(\d+)(")',
        re.DOTALL,
    )

    match = pattern.search(svg)

    if not match:
        raise RuntimeError(
            "Could not locate the root SVG height"
        )

    height = (
        int(match.group(2))
        + added_height
    )

    return (
        svg[:match.start()]
        + match.group(1)
        + str(height)
        + match.group(3)
        + svg[match.end():]
    )


def widen_language_bar(svg: str) -> str:
    pattern = re.compile(
        r'<svg class="bar" '
        r'xmlns="http://www\.w3\.org/2000/svg"'
        r'[^>]*>',
        re.DOTALL,
    )

    replacement = (
        '<svg class="bar" '
        'xmlns="http://www.w3.org/2000/svg" '
        'width="100%" '
        'height="10" '
        'viewBox="0 0 460 8" '
        'preserveAspectRatio="none" '
        'style="'
        'display:block;'
        'width:calc(100% - 64px);'
        'max-width:780px;'
        'height:10px;'
        'margin:6px auto 8px;'
        'overflow:hidden;'
        'border-radius:5px;'
        '">'
    )

    updated_svg, replacement_count = pattern.subn(
        replacement,
        svg,
        count=1,
    )

    if replacement_count != 1:
        raise RuntimeError(
            "Could not locate exactly one language bar"
        )

    return updated_svg

def main() -> None:
    activity = contribution_summary()
    achievements = achievement_summary()

    svg = SVG_PATH.read_text(
        encoding="utf-8",
    )

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

    habits = section(
        "Recent coding habits",
        (
            "M8 1.5a4.5 4.5 0 00-2.8 8.02"
            "c.34.27.55.66.55 1.1v.63h4.5v-.63"
            "c0-.44.21-.83.55-1.1A4.5 4.5 0 008 1.5z"
            "m-2.25 11.25h4.5v1.5h-4.5v-1.5z"
        ),
        [
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
        ],
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
        [
            (
                f'{achievements["repositories"]} repositories · '
                f'{achievements["stars"]} stars · '
                f'{achievements["forks"]} forks · '
                f'{achievements["followers"]} followers'
            )
        ],
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
            "INTJ-T · Architect · Turbulent",
            (
                "Introverted · Intuitive · "
                "Thinking · Judging"
            ),
        ],
        "personality",
    )

    music_bounds = section_bounds(
        svg,
        "Recently played",
    )

    if music_bounds is None:
        insertion = svg.find(
            "<footer>"
        )

        if insertion < 0:
            raise RuntimeError(
                "Could not locate the music section or footer"
            )

        svg = (
            svg[:insertion]
            + habits
            + achievements_section
            + personality
            + svg[insertion:]
        )

    else:
        music_start, music_end = (
            music_bounds
        )

        svg = (
            svg[:music_start]
            + habits
            + svg[music_start:music_end]
            + achievements_section
            + personality
            + svg[music_end:]
        )

    svg = increase_height(
        svg,
        126,
    )

    if "Unexpected error" in svg:
        raise RuntimeError(
            "The generated SVG still contains Unexpected error"
        )

    SVG_PATH.write_text(
        svg,
        encoding="utf-8",
    )

    print(
        "[PASS] Repaired github-metrics.svg "
        "without changing its visual system"
    )


if __name__ == "__main__":
    main()
