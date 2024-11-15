import os
import requests
import random
import re

# Configuration
ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")  # Retrieve from GitHub Actions secrets
TOPICS_FILE = "topics.txt"

# GitHub API headers
HEADERS = {
    "Authorization": f"token {ACCESS_TOKEN}",
    "Accept": "application/vnd.github.mercy-preview+json"
}

def sanitize_topic(topic):
    """Sanitizes a topic to meet GitHub's requirements."""
    topic = topic.strip()[:50]  # Limit to 50 characters
    topic = topic.replace(" ", "-")  # Replace spaces with hyphens
    topic = re.sub(r'[^a-z0-9\-]', '', topic.lower())  # Keep lowercase letters, numbers, and hyphens
    return topic

def get_repositories():
    """Fetches the list of repositories for the authenticated user."""
    url = "https://api.github.com/user/repos"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return [repo["full_name"] for repo in response.json()]
    else:
        print(f"Failed to fetch repositories: {response.status_code} {response.text}")
        return []

def get_topics_from_file():
    """Reads and sanitizes topics from the topics.txt file."""
    with open(TOPICS_FILE, "r") as file:
        topics = [sanitize_topic(line) for line in file if line.strip()]
    return topics

def find_similar_topics(repo_name, topics):
    """Finds topics similar to the repository name."""
    similar_topics = [topic for topic in topics if repo_name.lower() in topic]
    return similar_topics

def assign_topics_to_repo(full_repo_name, topics):
    """Assigns 10–14 sanitized topics to a repository."""
    repo_name = full_repo_name.split("/")[-1]
    similar_topics = find_similar_topics(repo_name, topics)
    
    if len(similar_topics) < 10:
        # If not enough similar topics, fill up with random ones from the list
        additional_topics = random.sample(topics, min(14 - len(similar_topics), len(topics)))
        similar_topics = list(set(similar_topics + additional_topics))
    
    selected_topics = similar_topics[:14]  # Ensure no more than 14 topics

    # Assign topics to the repository via GitHub API
    url = f"https://api.github.com/repos/{full_repo_name}/topics"
    response = requests.put(
        url,
        headers=HEADERS,
        json={"names": selected_topics}
    )
    if response.status_code == 200:
        print(f"Successfully assigned topics to {full_repo_name}: {selected_topics}")
    else:
        print(f"Failed to assign topics to {full_repo_name}: {response.status_code} {response.text}")

def main():
    repositories = get_repositories()
    if not repositories:
        print("No repositories found.")
        return

    topics = get_topics_from_file()
    if not topics:
        print("No valid topics found in topics.txt.")
        return

    for full_repo_name in repositories:
        assign_topics_to_repo(full_repo_name, topics)

if __name__ == "__main__":
    main()
