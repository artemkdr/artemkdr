# Guide to make the update-stats-in-readme.py work
This guide will help you set up and run the `update-stats-in-readme.py` script to update your GitHub README with your contribution statistics.

The only thing you need to do is to create a GitHub Personal Access Token (PAT) with the necessary permissions and set it as an environment variable on your machine / CI/CD pipeline.

If you need to access private repositories, the simplest is to use classic token with `repo` scope.
If you need to access an organization's repositories (public and private), the classic token with `repo` scope will also work, but you have to authorize the token usage for the organization (in organization settings -> third party access -> Personal access tokens).

There is also a workflow file `.github/workflows/update-stats-in-readme.yml` that can run the script automatically on a schedule (once a day / week) or manually via workflow dispatch.