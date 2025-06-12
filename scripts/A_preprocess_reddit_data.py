import pandas as pd
import os
import re
import json
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from datetime import datetime

# --- NLTK Data Downloads (Run once, then can comment out or remove) ---
# Uncomment these lines, run the script once, then comment them back.
# nltk.download('stopwords')
# nltk.download('wordnet')
# nltk.download('punkt')


# --- Configuration ---
# Get the project root path relative to this script
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_dir, os.pardir))

# Define paths for raw and processed data directories
RAW_DATA_DIR = os.path.join(project_root, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(project_root, "data", "processed")

# Ensure processed data directory exists
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# Your collector ID (used to identify your raw file and name the processed file)
# Make sure this matches the YOUR_IDENTIFIER in your config.py
YOUR_IDENTIFIER = "Agatha"

# Initialize NLTK tools
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def load_and_combine_reddit_data(identifier):
    """
    Loads raw Reddit data from the JSON file for a given identifier,
    flattens it into posts and comments, and combines them into a single DataFrame.
    """
    # Find the most recent JSON file for this identifier
    json_files = sorted([f for f in os.listdir(RAW_DATA_DIR) if f.startswith(f"{identifier}_reddit_data_with_comments_") and f.endswith(".json")], reverse=True)
    
    if not json_files:
        print(f"Error: No JSON file found for identifier '{identifier}' in {RAW_DATA_DIR}")
        return pd.DataFrame()

    latest_json_file = json_files[0]
    json_filepath = os.path.join(RAW_DATA_DIR, latest_json_file)

    print(f"Loading data from: {json_filepath}")
    with open(json_filepath, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    all_posts_flat = []
    all_comments_flat = []

    for post in raw_data:
        # Extract post data
        post_data = {
            'id': post.get('id'),
            'title': post.get('title'),
            'selftext': post.get('selftext'),
            'url': post.get('url'),
            'author': post.get('author'),
            'created_utc': post.get('created_utc'),
            'score': post.get('score'),
            'num_comments': post.get('num_comments'),
            'subreddit': post.get('subreddit'),
            'permalink': post.get('permalink')
        }
        all_posts_flat.append(post_data)

        # Extract comment data
        if 'comments' in post and post['comments']:
            for comment in post['comments']:
                comment_data = {
                    'comment_id': comment.get('comment_id'),
                    'comment_body': comment.get('comment_body'),
                    'comment_author': comment.get('comment_author'),
                    'comment_score': comment.get('comment_score'),
                    'comment_created_utc': comment.get('comment_created_utc'),
                    'parent_id': comment.get('parent_id'),
                    'submission_id': post.get('id') # Link comment to its parent post ID
                }
                all_comments_flat.append(comment_data)

    df_posts = pd.DataFrame(all_posts_flat)
    df_comments = pd.DataFrame(all_comments_flat)

    print(f"Extracted {len(df_posts)} posts and {len(df_comments)} comments from JSON.")

    # --- Combine posts and comments into a unified DataFrame ---
    
    # Prepare posts DataFrame for concatenation
    posts_df_formatted = df_posts[['id', 'title', 'selftext', 'created_utc', 'score', 'subreddit']].copy()
    posts_df_formatted.rename(columns={'id': 'text_id', 'selftext': 'text_content'}, inplace=True)
    posts_df_formatted['type'] = 'post'
    posts_df_formatted['text_content'] = posts_df_formatted['title'].fillna('') + ' ' + posts_df_formatted['text_content'].fillna('')
    # Add placeholder columns for comments to match structure
    posts_df_formatted['parent_id'] = None
    posts_df_formatted['submission_id'] = posts_df_formatted['text_id'] # Post's own ID as submission_id

    # Prepare comments DataFrame for concatenation
    comments_df_formatted = df_comments[['comment_id', 'comment_body', 'comment_created_utc', 'comment_score', 'parent_id', 'submission_id']].copy()
    comments_df_formatted.rename(columns={'comment_id': 'text_id', 'comment_body': 'text_content', 'comment_created_utc': 'created_utc', 'comment_score': 'score'}, inplace=True)
    comments_df_formatted['type'] = 'comment'
    # Add placeholder columns for posts to match structure
    comments_df_formatted['title'] = None
    comments_df_formatted['subreddit'] = None


    # Concatenate posts and comments
    combined_df = pd.concat([posts_df_formatted, comments_df_formatted], ignore_index=True)
    
    # Initial filtering for empty/deleted content
    combined_df['text_content'] = combined_df['text_content'].astype(str).str.strip()
    # Filter out entries where text content is empty or standard deleted/removed messages
    combined_df = combined_df[combined_df['text_content'] != '']
    combined_df = combined_df[combined_df['text_content'] != '[deleted]']
    combined_df = combined_df[combined_df['text_content'] != '[removed]']

    print(f"Combined DataFrame has {len(combined_df)} entries after initial filtering.")
    return combined_df

def clean_text(text):
    """
    Performs comprehensive text cleaning steps:
    - Lowercasing
    - Removing URLs, emails, hashtags, mentions, numbers
    - Removing punctuation and special characters
    - Removing extra spaces
    - Removing stop words
    - Lemmatization
    """
    text = str(text).lower() # Convert to string and lowercase

    # Remove URLs, emails, hashtags, mentions
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\S*@\S*\s?', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'@\w+', '', text)
    
    # Remove numbers
    text = re.sub(r'\d+', '', text)

    # Remove punctuation and special characters
    text = re.sub(r'[^\w\s]', '', text)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Tokenization, Stop word removal, and Lemmatization
    tokens = nltk.word_tokenize(text)
    
    # Remove stop words and lemmatize
    cleaned_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    
    return ' '.join(cleaned_tokens)

def main():
    # Load and combine raw Reddit data from the JSON file
    combined_df = load_and_combine_reddit_data(YOUR_IDENTIFIER)
    
    if not combined_df.empty:
        print("Applying comprehensive text cleaning (lowercasing, removing URLs/punctuation/numbers, stop words, lemmatization)...")
        combined_df['cleaned_text'] = combined_df['text_content'].apply(clean_text)

        # Filter out entries where cleaned_text becomes empty after cleaning
        combined_df = combined_df[combined_df['cleaned_text'].astype(str).str.strip() != '']
        print(f"Final DataFrame has {len(combined_df)} entries after all cleaning steps.")

        # Save the processed data to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processed_filename = os.path.join(PROCESSED_DATA_DIR, f"{YOUR_IDENTIFIER}_reddit_processed_data_{timestamp}.csv")
        combined_df.to_csv(processed_filename, index=False, encoding='utf-8')
        print(f"\nProcessed Reddit data saved to: {processed_filename}")
    else:
        print("No data to process. Please ensure raw JSON file exists and contains data.")

if __name__ == "__main__":
    main()
