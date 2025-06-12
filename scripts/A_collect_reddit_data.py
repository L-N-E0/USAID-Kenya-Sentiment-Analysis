import praw
import json
import os
import sys # Import sys for path manipulation
import pandas as pd # Still needed for some internal PRAW functionalities, though not directly for CSV saving
from datetime import datetime, timezone
import time

# --- Path Configuration for finding config.py ---
# This block explicitly adds the project root to Python's system path.
# This ensures that 'config.py' (located in the project root) can be found
# when this script is run from a subdirectory like 'scripts/'.
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_dir, os.pardir))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import API credentials and personal identifier from config.py ---
# This block attempts to load sensitive information and your unique identifier
# from the config.py file located in the project's root directory.
# If the file or required variables are missing, it will print an error and exit.
try:
    from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, YOUR_IDENTIFIER
except ImportError:
    print("Error: config.py not found or missing required credentials.")
    print("Please ensure config.py is in the project root and defines:")
    print("  - REDDIT_CLIENT_ID")
    print("  - REDDIT_CLIENT_SECRET")
    print("  - REDDIT_USER_AGENT")
    print("  - YOUR_IDENTIFIER")
    exit()

# --- Configuration for Data Collection ---
# Keywords and phrases to search for on Reddit related to USAID funding cuts in Kenya.
SEARCH_KEYWORDS = [
    "USAID Kenya funding cuts",
    "USAID Kenya aid",
    "US aid Kenya",
    "American aid Kenya",
    "Kenya development aid",
    "foreign aid Kenya cuts",
    "USAID Kenya health",
    "USAID Kenya education"
]

# Define the start timestamp for data collection.
# Unix timestamp for Dec 3, 2024, 00:00:00 UTC (approx. last 6 months from current date in 2025).
# This is a suggested value to manage data volume.
START_TIMESTAMP = 1701561600

# List of subreddits to search. 'all' searches across all of Reddit,
# while others are more targeted.
TARGET_SUBREDDITS = [
    "news",            # General news
    "worldnews",       # International news
    "politics",        # Political discussions
    "africa",          # Discussions related to Africa
    "kenya",           # Specific to Kenya
    "globaldevelopment", # Discussions on global development and aid
    "internationalrelations" # Discussions on international policy
]

# Maximum number of posts to attempt to retrieve per search query per subreddit.
# This is a suggested value (reduced from 500) to manage data volume for limited RAM.
MAX_POSTS_PER_QUERY = 150

# Maximum number of comments to collect for each post.
MAX_COMMENTS_PER_POST = 200

# Construct the output directory path for raw data.
# This ensures the data is saved in 'your_project_folder/data/raw/'.
DATA_OUTPUT_DIR = os.path.join(project_root, "data", "raw") # Changed to use project_root for consistency

# Ensure the output directory exists. If it doesn't, create it.
# 'exist_ok=True' prevents an error if the directory already exists.
os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)


def initialize_reddit():
    """
    Initializes the PRAW Reddit instance using credentials from config.py.
    This function handles the OAuth authentication flow for script applications,
    which will typically open a browser tab for user authorization the first time it runs.
    """
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        print("Authenticating with Reddit... Please check your browser if a new tab opens for authorization.")
        # Attempt to get the current user to trigger the OAuth flow.
        # The script will pause here until authorization is completed in the browser.
        print(f"Successfully logged in as: {reddit.user.me()}")
        print("Reddit instance initialized successfully.")
        return reddit
    except Exception as e:
        print(f"Error initializing Reddit: {e}")
        print("Please verify your config.py credentials and ensure you followed the Reddit app setup instructions correctly.")
        exit()


def collect_posts(reddit_instance, query, subreddit_name="all", limit=MAX_POSTS_PER_QUERY, time_filter='all'):
    """
    Collects Reddit posts based on a search query from a specified subreddit.
    Filters posts by a defined START_TIMESTAMP to get relevant recent data.
    """
    posts_data = []
    print(f"Searching for '{query}' in r/{subreddit_name} (limit={limit}, time_filter='{time_filter}')...")
    try:
        # Perform the search. The 'time_filter' is for the API,
        # but we apply a more precise filter using START_TIMESTAMP below.
        search_results = reddit_instance.subreddit(subreddit_name).search(
            query,
            limit=limit,
            time_filter=time_filter, # e.g., 'all', 'year', 'month'
            sort='relevance' # Sort by relevance is often good for search queries
        )

        for submission in search_results:
            # Filter by the defined START_TIMESTAMP to ensure posts are within our desired timeframe.
            if submission.created_utc >= START_TIMESTAMP:
                posts_data.append({
                    'id': submission.id,
                    'title': submission.title,
                    'selftext': submission.selftext, # The body content of the post
                    'url': submission.url,           # URL to the external link (if any) or Reddit post
                    'author': str(submission.author) if submission.author else '[deleted]', # Author's username
                    'created_utc': submission.created_utc, # Unix timestamp of creation
                    'score': submission.score,       # Upvotes minus downvotes
                    'num_comments': submission.num_comments, # Number of top-level comments
                    'subreddit': submission.subreddit.display_name, # Name of the subreddit
                    'permalink': submission.permalink # Permalink to the Reddit post
                })
        print(f"Found {len(posts_data)} relevant posts for query '{query}' in r/{subreddit_name}.")
    except Exception as e:
        print(f"Error collecting posts for '{query}' in r/{subreddit_name}: {e}")
    return posts_data


def collect_comments_for_post(reddit_instance, submission_id, limit=MAX_COMMENTS_PER_POST):
    """
    Collects comments for a given Reddit submission (post) ID.
    Expands 'More Comments' links to retrieve a more comprehensive set of comments.
    """
    comments_data = []
    try:
        submission = reddit_instance.submission(id=submission_id)
        # Replace 'MoreComments' objects with actual comments.
        # limit=0 attempts to fetch all comments, but be mindful of very large threads.
        submission.comments.replace_more(limit=0)
        
        # Iterate through all comments and collect their data.
        for comment in submission.comments.list():
            # Ensure the object is indeed a PRAW Comment object (not a 'MoreComments' placeholder).
            if isinstance(comment, praw.models.Comment):
                # Ensure the comment has an author (i.e., not deleted).
                if comment.author:
                    comments_data.append({
                        'comment_id': comment.id,
                        'comment_body': comment.body,
                        'comment_author': str(comment.author),
                        'comment_score': comment.score,
                        'comment_created_utc': comment.created_utc,
                        'parent_id': comment.parent_id, # ID of the parent comment or post
                        'submission_id': submission_id # Link back to the original post
                    })
                    # Stop collecting comments for this post if the limit is reached.
                    if len(comments_data) >= limit:
                        break
    except Exception as e:
        print(f"Error collecting comments for submission {submission_id}: {e}")
    return comments_data


def main():
    """
    Main function to orchestrate the Reddit data collection process.
    Initializes Reddit, collects posts based on keywords and subreddits,
    then collects comments for unique posts, and finally saves the data.
    """
    reddit = initialize_reddit()

    all_posts = []
    # all_comments will still be populated but not saved separately to CSV.
    # It's primarily used here for extending the comments list attached to posts.
    all_comments = []

    # --- Step 1: Collect Posts ---
    # Iterate through each search keyword and each target subreddit to collect posts.
    for keyword in SEARCH_KEYWORDS:
        for subreddit_name in TARGET_SUBREDDITS:
            posts = collect_posts(reddit, keyword, subreddit_name=subreddit_name, time_filter='all')
            all_posts.extend(posts)
            # Introduce a small delay to comply with Reddit's API rate limits.
            time.sleep(1) # Adjust this value if you encounter rate limit errors frequently.

    # Calculate and print the total number of unique posts found across all searches.
    print(f"\nTotal posts collected (before deduplication): {len(all_posts)}")
    # Deduplicate posts based on their unique ID.
    # This ensures each post is processed only once, even if found by multiple searches.
    unique_posts = {post['id']: post for post in all_posts}.values()
    print(f"Processing {len(unique_posts)} unique posts for comment collection...")


    # --- Step 2: Collect Comments for Unique Posts ---
    # Iterate through each unique post to collect its comments.
    for i, post in enumerate(unique_posts):
        # Print progress to the console.
        print(f"Collecting comments for post {i+1}/{len(unique_posts)}: '{post['title'][:50]}...'")
        comments = collect_comments_for_post(reddit, post['id'])
        # Embed the collected comments directly into the post's dictionary.
        post['comments'] = comments
        # Add all collected comments to a flat list (for potential debugging/monitoring, but not saved to CSV)
        all_comments.extend(comments)
        # Small delay between collecting comments for different posts.
        time.sleep(0.5) # Adjust if needed.

    # --- Step 3: Save Collected Data (JSON Only) ---
    # Use the unique identifier from config.py for naming files.
    collector_id = YOUR_IDENTIFIER

    # Generate a timestamp for unique filenames.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save all data (posts with embedded comments) as a JSON file.
    # This preserves the hierarchical structure of posts and their comments.
    json_filename = os.path.join(DATA_OUTPUT_DIR, f"{collector_id}_reddit_data_with_comments_{timestamp}.json")
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(list(unique_posts), f, ensure_ascii=False, indent=4)
    print(f"\nAll Reddit data (posts with embedded comments) saved to: {json_filename}")

    print("\nReddit data collection complete.")

if __name__ == "__main__":
    main()
