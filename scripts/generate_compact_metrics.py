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
        "User-Agent": f"{PROFILE_USER}-compact-profile-metrics",
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


def escaped(value: object) -> str:
    return html.escape(
        str(value),
        quote=True,
    )


def contribution_metrics() -> dict[str, int]:
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

    total = sum(
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
        "total": total,
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


def achievement_metrics() -> dict[str, int]:
    user = request_json(
        f"https://api.github.com/users/{PROFILE_USER}"
    )

    repositories = request_json(
        f"https://api.github.com/users/{PROFILE_USER}/repos"
        "?per_page=100&type=owner&sort=updated"
    )

    repositories = [
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
        for repository in repositories
    )

    forks = sum(
        int(
            repository.get(
                "forks_count",
                0,
            )
        )
        for repository in repositories
    )

    return {
        "repositories": int(
            user.get(
                "public_repos",
                0,
            )
        ),
        "stars": stars,
        "forks": forks,
        "followers": int(
            user.get(
                "followers",
                0,
            )
        ),
    }


def personality_type() -> str:
    result = "INTJ-T"

    if not PERSONALITY_URL:
        return result

    try:
        page = request_text(
            PERSONALITY_URL
        )

        match = re.search(
            r"\bINTJ(?:-[AT])?\b",
            page,
            flags=re.IGNORECASE,
        )

        if match:
            result = match.group(0).upper()

    except Exception:
        pass

    return result


activity = contribution_metrics()
achievements = achievement_metrics()
personality = personality_type()

svg = f"""<svg
  xmlns="http://www.w3.org/2000/svg"
  width="480"
  height="238"
  viewBox="0 0 480 238"
  role="img"
>
  <style>
    svg {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Helvetica,
        Arial,
        sans-serif;
      font-size: 13px;
    }}

    .background {{
      fill: #1a1b27;
      stroke: #414868;
      stroke-width: 1;
    }}

    .heading {{
      fill: #70a5fd;
      font-size: 14px;
      font-weight: 500;
    }}

    .label {{
      fill: #a9b1d6;
      font-size: 12px;
    }}

    .value {{
      fill: #c0caf5;
      font-size: 12px;
      font-weight: 600;
    }}

    .icon {{
      fill: #bb9af7;
      font-size: 13px;
      font-weight: 700;
    }}

    .divider {{
      stroke: #292e42;
      stroke-width: 1;
    }}
  </style>

  <rect
    class="background"
    x="0.5"
    y="0.5"
    width="479"
    height="237"
    rx="6"
  />

  <text
    class="icon"
    x="20"
    y="30"
  >◉</text>

  <text
    class="heading"
    x="42"
    y="30"
  >Recent coding habits</text>

  <text
    class="label"
    x="42"
    y="54"
  >Contributions</text>

  <text
    class="value"
    x="154"
    y="54"
  >{escaped(activity["total"])}</text>

  <text
    class="label"
    x="218"
    y="54"
  >Active days</text>

  <text
    class="value"
    x="300"
    y="54"
  >{escaped(activity["active_days"])}/14</text>

  <text
    class="label"
    x="354"
    y="54"
  >Current streak</text>

  <text
    class="value"
    x="444"
    y="54"
    text-anchor="end"
  >{escaped(activity["streak"])} d</text>

  <text
    class="label"
    x="42"
    y="76"
  >Commits</text>

  <text
    class="value"
    x="154"
    y="76"
  >{escaped(activity["commits"])}</text>

  <text
    class="label"
    x="218"
    y="76"
  >Pull requests</text>

  <text
    class="value"
    x="300"
    y="76"
  >{escaped(activity["pull_requests"])}</text>

  <text
    class="label"
    x="354"
    y="76"
  >Reviews</text>

  <text
    class="value"
    x="444"
    y="76"
    text-anchor="end"
  >{escaped(activity["reviews"])}</text>

  <line
    class="divider"
    x1="20"
    y1="94"
    x2="460"
    y2="94"
  />

  <text
    class="icon"
    x="20"
    y="121"
  >◆</text>

  <text
    class="heading"
    x="42"
    y="121"
  >Achievements</text>

  <text
    class="label"
    x="42"
    y="145"
  >Repositories</text>

  <text
    class="value"
    x="132"
    y="145"
  >{escaped(achievements["repositories"])}</text>

  <text
    class="label"
    x="184"
    y="145"
  >Stars</text>

  <text
    class="value"
    x="226"
    y="145"
  >{escaped(achievements["stars"])}</text>

  <text
    class="label"
    x="278"
    y="145"
  >Forks</text>

  <text
    class="value"
    x="322"
    y="145"
  >{escaped(achievements["forks"])}</text>

  <text
    class="label"
    x="370"
    y="145"
  >Followers</text>

  <text
    class="value"
    x="444"
    y="145"
    text-anchor="end"
  >{escaped(achievements["followers"])}</text>

  <line
    class="divider"
    x1="20"
    y1="163"
    x2="460"
    y2="163"
  />

  <text
    class="icon"
    x="20"
    y="190"
  >◇</text>

  <text
    class="heading"
    x="42"
    y="190"
  >Personality</text>

  <text
    class="value"
    x="130"
    y="190"
  >{escaped(personality)}</text>

  <text
    class="label"
    x="42"
    y="214"
  >Introverted · Intuitive · Thinking · Judging · Turbulent</text>
</svg>
"""

Path(
    "supplemental-metrics.svg"
).write_text(
    svg,
    encoding="utf-8",
)

print(
    "[PASS] Generated supplemental-metrics.svg"
)
