import os
import requests
from datetime import datetime, timedelta, timezone
from collections import Counter

# Configuration
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ["GITHUB_REPOSITORY"].split("/")[0]
API_URL = "https://api.github.com/graphql"

# Date Calculations
now = datetime.now(timezone.utc)
one_month_ago = now - timedelta(days=30)
one_year_ago = now - timedelta(days=365)

# GraphQL Query
query = """
query($username: String!, $monthStart: DateTime!, $yearStart: DateTime!, $end: DateTime!) {
  user(login: $username) {
    monthStats: contributionsCollection(from: $monthStart, to: $end) {
      totalCommitContributions
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
    yearStats: contributionsCollection(from: $yearStart, to: $end) {
      totalPullRequestReviewContributions
      commitContributionsByRepository {
        repository {
          primaryLanguage {
            name
          }
        }
      }
    }
  }
}
"""

variables = {
    "username": USERNAME,
    "monthStart": one_month_ago.isoformat(),
    "yearStart": one_year_ago.isoformat(),
    "end": now.isoformat()
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
    lang_counter = Counter()
    for item in repos:
        repo = item['repository']
        # Check if repo has a primary language (some empty repos don't)
        if repo['primaryLanguage']:
            lang_name = repo['primaryLanguage']['name']
            lang_counter[lang_name] += 1
            
    # Get top 3
    top_3 = lang_counter.most_common(3)
    # Format as string: "Python, JavaScript, Go"
    return ", ".join([lang[0] for lang in top_3])

def update_readme(stats):
    with open("README.md", "r") as f:
        content = f.read()

    start_marker = "`"
    end_marker = "`"
    
    # Power Day Emoji Logic
    day_emojis = {
        "Monday": "☕", "Tuesday": "🚀", "Wednesday": "🐪", 
        "Thursday": "⚡", "Friday": "🎉", "Saturday": "🎮", "Sunday": "🌞"
    }
    day_emoji = day_emojis.get(stats['power_day'], "📅")

    # Generate the Markdown
    new_stats = f"{start_marker}\n"
    new_stats += f"- 🔭 **{stats['commits']}** commits in the last 30 days\n"
    new_stats += f"- 🛠️ Worked on **{stats['projects']}** projects in the last year\n"
    new_stats += f"- {day_emoji} Power Day: **{stats['power_day']}s**\n"
    new_stats += f"- 🧠 Top 3 Languages: **{stats['top_languages']}**\n"
    new_stats += f"- 🤝 Reviewed **{stats['reviews']}** Pull Requests (last year)\n"
    new_stats += f"{end_marker}"

    if start_marker in content and end_marker in content:
        pre = content.split(start_marker)[0]
        post = content.split(end_marker)[1]
        with open("README.md", "w") as f:
            f.write(pre + new_stats + post)
        print("README updated successfully.")
    else:
        print("Markers not found in README.md")

def main():
    data = run_query()
    
    # Parsing Data
    commits = data['data']['user']['monthStats']['totalCommitContributions']
    weeks = data['data']['user']['monthStats']['contributionCalendar']['weeks']
    repo_contributions = data['data']['user']['yearStats']['commitContributionsByRepository']
    reviews = data['data']['user']['yearStats']['totalPullRequestReviewContributions']
    
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
        "reviews": reviews
    }
    
    print(f"Calculated Stats: {stats}")
    update_readme(stats)

if __name__ == "__main__":
    main()
