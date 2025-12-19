import os
import requests
import re
import random
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
    return ", ".join([f"![]({f'https://placehold.co/10x10/{data['color'][1:]}/{data['color'][1:]}.png'}) {name}" for name, data in top_10])

def update_readme(stats, photo_link):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    stats_start_marker = "<!--STATS_START-->"
    stats_end_marker = "<!--STATS_END-->"

    photo_start_marker = "<!--PHOTO_START-->"
    photo_end_marker = "<!--PHOTO_END-->"
    
    # Power Day Emoji Logic
    day_emojis = {
        "Monday": "☕", "Tuesday": "🚀", "Wednesday": "🐪", 
        "Thursday": "⚡", "Friday": "🎉", "Saturday": "🎮", "Sunday": "🌞"
    }
    day_emoji = day_emojis.get(stats['power_day'], "📅")

    # Generate the Markdown
    new_stats = f"{stats_start_marker}\n"
    new_stats += f"### 📊 My GitHub stats for the year as of {stats['last_updated']}\n"
    new_stats += f"- 🔭 **{stats['commits']}** commits\n"
    new_stats += f"- 🛠️ Worked on **{stats['projects']}** projects\n"
    new_stats += f"- {day_emoji} Power Day: **{stats['power_day']}s**\n"
    new_stats += f"- 🧠 Top 10 Languages: {stats['top_languages']}\n"
    new_stats += f"- 🔒 Closed **{stats['closed_issues']}** Issues\n"
    new_stats += f"- 🤝 Reviewed **{stats['reviews']}** Pull Requests\n"
    new_stats += f"{stats_end_marker}"

    # Update Photo Section
    new_photo_section = f"{photo_start_marker}\n"
    if photo_link:
        new_photo_section += f"![Random Photo]({photo_link})\n"
    new_photo_section += f"{photo_end_marker}"

    if stats_start_marker in content and stats_end_marker in content:
        stats_pre = content.split(stats_start_marker)[0]
        stats_post = content.split(stats_end_marker)[1]

        photo_pre = stats_post.split(photo_start_marker)[0]
        photo_post = stats_post.split(photo_end_marker)[1]

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(stats_pre + new_stats + photo_pre + new_photo_section + photo_post)
        print("README updated successfully.")
    else:
        print("Markers not found in README.md")

def get_random_photo_from_shared_album(album_url):
    # 1. Handle short URLs (e.g., photos.app.goo.gl)
    response = requests.get(album_url, allow_redirects=True)
    if response.status_code != 200:
        print("Failed to access the album. It may be private or the URL is incorrect.")
        return None

    
    # 2. Scrape the page for image URLs
    # Google Photos embeds the photo data in a javascript array script
    # We look for the pattern that generally holds the media items
    # Note: This regex is looking for the specific JSON structure Google uses
    
    # This regex looks for image base URLs which always start with lh3.googleusercontent.com
    # and follow a specific pattern in the source code.
    # The ["] matches the quote before the URL
    url_pattern = r'"(https:\/\/lh3\.googleusercontent\.com\/pw\/[a-zA-Z0-9_-]+)"'
    
    # Find all matches in the page content
    all_urls = re.findall(url_pattern, response.text)
    
    # Deduplicate URLs
    unique_urls = list(set(all_urls))
    
    if not unique_urls:
        print("No photos found or album is private/empty.")
        return None

    # 3. Pick a random photo
    random_photo_url = random.choice(unique_urls)
    
    # 4. Clean the URL (The raw URL is often low res or has params)
    # Appending '=w800&h=800' forces a low-res version
    low_res_url = f"{random_photo_url}=w500-h500?authuser=0"
    
    return low_res_url

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
    last_updated = now.strftime("%d.%m.%Y")
    
    # Bundle stats
    stats = {
        "commits": commits,
        "projects": project_count,
        "power_day": power_day,
        "top_languages": top_languages,
        "reviews": reviews,
        "closed_issues": closed_issues,
        "last_updated": last_updated
    }
    
    print(f"Calculated Stats: {stats}")
    
    # Pick a random photo from a shared album (example URL)
    photo_link = get_random_photo_from_shared_album("https://photos.google.com/share/AF1QipOP-sOjKxg6NIQvtK893Lt6XgnHdowP0oa1ZsvYvQaPac0iio0DcsU4en09JXt3ZA?key=RGI0VWVwemZ4WkRCanJkbk1JYmxmVzN2Wm1SVzhR")
    if photo_link:
        print(f"Random Photo URL: {photo_link}")
    else:
        print("No photo could be retrieved.")
    
    # Update README
    update_readme(stats, photo_link)


if __name__ == "__main__":
    main()
