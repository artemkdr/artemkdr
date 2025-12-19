import os
import requests
from datetime import datetime, timedelta, timezone
from collections import Counter
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ["GITHUB_REPOSITORY"].split("/")[0]
API_URL = "https://api.github.com/graphql"

# Date Calculations
now = datetime.now(timezone.utc)
one_year_ago = now - timedelta(days=365)

# GraphQL Query
query = """
query($username: String!, $yearStart: DateTime!, $end: DateTime!, $issuesQuery: String!) {
  user(login: $username) {
    yearStats: contributionsCollection(from: $yearStart, to: $end) {
      totalCommitContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
      commitContributionsByRepository {
        repository {
          name
          languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
            edges {
              size
              node {
                name
                color
              }
            }
          }
        }
      }
    }
  }
  closedIssues: search(type: ISSUE, query: $issuesQuery, first: 0) {
    issueCount
  }
}
"""

variables = {
    "username": USERNAME,
    "yearStart": one_year_ago.isoformat(),
    "end": now.isoformat(),
    "issuesQuery": f"is:issue is:closed author:{USERNAME}"
}

headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

def run_query():
    response = requests.post(API_URL, json={'query': query, 'variables': variables}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed: {response.status_code}. {query}")

def get_most_active_day(weeks):
    day_counter = Counter()
    for week in weeks:
        for day in week['contributionDays']:
            if day['contributionCount'] > 0:
                date_obj = datetime.strptime(day['date'], '%Y-%m-%d')
                day_name = date_obj.strftime('%A')
                day_counter[day_name] += day['contributionCount']
    return day_counter.most_common(1)[0][0] if day_counter else "N/A"

def get_top_languages(repos):
    # Aggregate language sizes across all repositories
    lang_info = {}
    for item in repos:
        repo = item['repository']
        edges = repo.get('languages', {}).get('edges', [])
        for edge in edges:
            node = edge.get('node')
            size = edge.get('size', 0)
            if not node or not node.get('name') or not size:
                continue
            name = node['name']
            color = node.get('color') or "#cccccc"
            if name not in lang_info:
                lang_info[name] = {"size": 0, "color": color}
            lang_info[name]["size"] += size
            # Preserve first non-empty color seen
            if not lang_info[name].get("color") and color:
                lang_info[name]["color"] = color

    top_10 = sorted(lang_info.items(), key=lambda kv: kv[1]["size"], reverse=True)[:10]
    return ", ".join([f"<span style=\"color:{data['color']}\">●</span> {name}" for name, data in top_10])

def update_readme(stats):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!--START-->"
    end_marker = "<!--END-->"
    
    # Power Day Emoji Logic
    day_emojis = {
        "Monday": "☕", "Tuesday": "🚀", "Wednesday": "🐪", 
        "Thursday": "⚡", "Friday": "🎉", "Saturday": "🎮", "Sunday": "🌞"
    }
    day_emoji = day_emojis.get(stats['power_day'], "📅")

    # Generate the Markdown
    new_stats = f"{start_marker}\n"
    new_stats += f"- 🔭 **{stats['commits']}** commits\n"
    new_stats += f"- 🛠️ Worked on **{stats['projects']}** projects\n"
    new_stats += f"- {day_emoji} Power Day: **{stats['power_day']}s**\n"
    new_stats += f"- 🧠 Top 10 Languages: **{stats['top_languages']}**\n"
    new_stats += f"- 🔒 Closed **{stats['closed_issues']}** Issues\n"
    new_stats += f"- 🤝 Reviewed **{stats['reviews']}** Pull Requests\n"
    new_stats += f"{end_marker}"

    if start_marker in content and end_marker in content:
        pre = content.split(start_marker)[0]
        post = content.split(end_marker)[1]
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(pre + new_stats + post)
        print("README updated successfully.")
    else:
        print("Markers not found in README.md")

def main():
    data = run_query()
    
    # Parsing Data
    year_stats = data['data']['user']['yearStats']
    closed_issues = data['data']['closedIssues']['issueCount']
    commits = year_stats['totalCommitContributions']
    weeks = year_stats['contributionCalendar']['weeks']
    repo_contributions = year_stats['commitContributionsByRepository']
    reviews = year_stats['totalPullRequestReviewContributions']
    
    # Processing Logic
    project_count = len(repo_contributions)
    power_day = get_most_active_day(weeks)
    top_languages = get_top_languages(repo_contributions)
    
    # Bundle stats
    stats = {
        "commits": commits,
        "projects": project_count,
        "power_day": power_day,
        "top_languages": top_languages,
        "reviews": reviews,
        "closed_issues": closed_issues
    }
    
    print(f"Calculated Stats: {stats}")
    update_readme(stats)

if __name__ == "__main__":
    main()
