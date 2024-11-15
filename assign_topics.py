import os
import requests
import random
import re

# Configuration
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")  # Retrieve from GitHub Actions secrets
if not ACCESS_TOKEN:
    print("Environment variable ACCESS_TOKEN is not set.")
    print("Ensure the secret is defined in GitHub Actions and passed correctly.")
    raise ValueError("ACCESS_TOKEN is not set!")

# GitHub API headers
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/vnd.github.mercy-preview+json"
}

TOPICS_FILE = "topics.txt"

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

def get_repo_topics(full_repo_name):
    """Fetches the current topics of a repository."""
    url = f"https://api.github.com/repos/{full_repo_name}/topics"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("names", [])
    else:
        print(f"Failed to fetch topics for {full_repo_name}: {response.status_code} {response.text}")
        return []

def get_topics_from_file():
    """Reads and sanitizes topics from the topics.txt file."""
    if not os.path.exists(TOPICS_FILE):
        print(f"{TOPICS_FILE} does not exist!")
        return []
    with open(TOPICS_FILE, "r") as file:
        topics = [sanitize_topic(line) for line in file if line.strip()]
    return topics

def find_similar_topics(repo_name, topics):
    """Finds topics similar to the repository name."""
    return [topic for topic in topics if repo_name.lower() in topic]

def assign_topics_to_repo(full_repo_name, topics):
    """Assigns 10–14 sanitized topics to a repository."""
    repo_name = full_repo_name.split("/")[-1]
    current_topics = get_repo_topics(full_repo_name)

    # Skip repositories that already have topics assigned
    if current_topics:
        print(f"Skipping {full_repo_name}: Topics already assigned ({current_topics})")
        return

    similar_topics = find_similar_topics(repo_name, topics)
    if len(similar_topics) < 10:
        additional_topics = random.sample(topics, min(14 - len(similar_topics), len(topics)))
        similar_topics = list(set(similar_topics + additional_topics))
    
    selected_topics = similar_topics[:14]

    url = f"https://api.github.com/repos/{full_repo_name}/topics"
    response = requests.put(url, headers=HEADERS, json={"names": selected_topics})
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
