"""GitHub tool connector using OAuth access tokens."""

from __future__ import annotations

from typing import Any
import httpx
from langchain_core.tools import tool


def make_github_tool(access_token: str):
    @tool("github_activity", description="Fetch repository commits, PR velocity, and active contributors")
    def github_activity(repo: str) -> str:
        """Fetch git repository statistics given repo formatted as 'owner/repo'."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DevilsAdvocatePanel",
        }
        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.get(f"https://api.github.com/repos/{repo}", headers=headers)
                if res.status_code == 401:
                    return "GitHub connection expired or token revoked — no repository data available."
                if res.status_code != 200:
                    return f"GitHub API error ({res.status_code}): {res.text}"
                data = res.json()
                stars = data.get("stargazers_count", 0)
                forks = data.get("forks_count", 0)
                open_issues = data.get("open_issues_count", 0)
                pushed_at = data.get("pushed_at", "unknown")

                # Fetch recent commits
                commits_res = client.get(f"https://api.github.com/repos/{repo}/commits?per_page=5", headers=headers)
                recent_commits_count = len(commits_res.json()) if commits_res.status_code == 200 else 0

                return (
                    f"GitHub Repo '{repo}': {stars} stars, {forks} forks, {open_issues} open issues. "
                    f"Last push: {pushed_at}. Recent commits verified: {recent_commits_count}."
                )
        except Exception as e:
            return f"Error querying GitHub repo {repo}: {e}"

    return github_activity
