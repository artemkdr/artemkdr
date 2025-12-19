# Guide
This guide explains how the `update-stats-in-readme.py` script works and how to set it up for your GitHub profile `README.md`.

## What the script does
`update-stats-in-readme.py` fetches your GitHub contribution statistics for the current year and updates specific sections of your `README.md` with that data. The script looks for predefined markers in the README to identify where to insert the statistics and a random photo of the day.

The sections are marked with the following HTML comments:

```markdown
<!--STATS_START-->
... (stats will be inserted here) ...
<!--STATS_END-->

<!--PHOTO_START-->
... (photo will be inserted here) ...
<!--PHOTO_END-->
```

The photo section must immediately follow the stats section.

### Statistics retrieved
- **Total commits**
- **Pull requests reviewed**
- **Issues closed**
- **Repositories contributed to**
- **Top 10 languages** (by bytes across repositories you've contributed to)
- **Power day** (the day of the week with the highest single-day contribution count)

Important: the script uses GitHub's GraphQL API and requires authentication with a Personal Access Token (PAT).
Create a GitHub Personal Access Token with the necessary permissions and expose it as an environment variable on your machine or in your CI/CD pipeline.

- For access to private repositories, use a classic token with the `repo` scope.
- For organization repositories (public or private), a classic token with the `repo` scope also works, but you must authorize the token for the organization (Organization Settings → Third party access → Personal access tokens).

### Random photo from Google Photos
The script can also fetch a random photo from a public Google Photos album. Provide the album's share link via the `GOOGLE_PHOTO_ALBUM_LINK` environment variable.

The link should look similar to this:

```
https://photos.google.com/share/AF2QipOP-sOjKxg6NIQvtK893Lt8XgnHdowP0oa1ZsvYvQaPac0iio0DcsU4en09JXt3ZA?key=RGI0VWVwemZ4WkRCanJkbk1JYmxmVxN2Wm1SVzhR
```

Important: make sure the album is set to "Anyone with the link can view".

## Updating your README daily
You can set up a GitHub Action to run this script on a schedule (for example, daily) and automatically update your README.

- See the workflow example in [.github/workflows/update-readme.yml](.github/workflows/update-readme.yml) for a sample configuration.
- Store `GITHUB_TOKEN` and `GOOGLE_PHOTO_ALBUM_LINK` as repository secrets.
- Adjust the schedule as needed (the example runs daily at 19:00 UTC).
