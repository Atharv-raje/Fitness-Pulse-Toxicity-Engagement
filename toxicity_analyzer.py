import os
import psycopg2
import requests
from concurrent.futures import ThreadPoolExecutor
from db_connector import get_db_connection
from dotenv import load_dotenv
import time
from requests.exceptions import RequestException

load_dotenv()

API_TOKEN = os.getenv('MODERATE_HATESPEECH_API_TOKEN')

if not API_TOKEN:
    raise Exception("API token not found in environment variables.")

CONF_THRESHOLD = 0.9  # Confidence threshold

# Fetch posts from reddit_posts table
def fetch_posts():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM public.reddit_posts;')
            return cursor.fetchall()
    finally:
        conn.close()

# Fetch comments from reddit_comments table
def fetch_comments():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM public.reddit_comments;')
            return cursor.fetchall()
    finally:
        conn.close()

def fetch_post_by_id(post_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM public.reddit_posts WHERE id = %s;', (post_id,))
            post = cursor.fetchone()
            return post
    finally:
        conn.close()

def hs_check_comment(comment_text, max_retries=3):
    data = {
        "token": API_TOKEN,
        "text": comment_text
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://api.moderatehatespeech.com/api/v1/moderate/",
                json=data,
                timeout=10  # Set a timeout
            )
            response.raise_for_status()
            result = response.json()
            if result.get("class") == "flag" and float(result.get("confidence", 0)) > CONF_THRESHOLD:
                return 1  # Toxic
            else:
                return 0  # Not toxic
        except RequestException as e:
            print(f"API request error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                sleep_time = 2 ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print("Max retries exceeded. Skipping this comment/post.")
                return None  # Indicate an error occurred

# Process and store posts
def process_posts(posts):
    with ThreadPoolExecutor(max_workers=10) as executor:
        for post in posts:
            executor.submit(process_single_post, post)

def process_single_post(post, conn=None):
    own_connection = False
    if conn is None:
        conn = get_db_connection()
        own_connection = True
    try:
        if own_connection:
            conn.autocommit = False  # Disable autocommit mode
        toxic_analysis = hs_check_comment(post[2])  # Analyze body
        if toxic_analysis is None:
            if own_connection:
                conn.rollback()
            return  # Skip if error occurred
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO public.processed_reddit_posts
                (id, title, body, created_utc, score, url, subreddit, toxic_analysis)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    body = EXCLUDED.body,
                    created_utc = EXCLUDED.created_utc,
                    score = EXCLUDED.score,
                    url = EXCLUDED.url,
                    subreddit = EXCLUDED.subreddit,
                    toxic_analysis = EXCLUDED.toxic_analysis;
                ''',
                (post[0], post[1], post[2], post[3], post[4], post[5], post[6], toxic_analysis)
            )
        if own_connection:
            conn.commit()
        print(f"Processed post {post[0]}: Toxicity Analysis = {toxic_analysis}")
    except Exception as e:
        if own_connection:
            conn.rollback()
        print(f"Error processing post {post[0]}: {e}")
    finally:
        if own_connection:
            conn.close()

# Process and store comments
def process_comments(comments):
    with ThreadPoolExecutor(max_workers=10) as executor:
        for comment in comments:
            executor.submit(process_single_comment, comment)

def process_single_comment(comment):
    conn = get_db_connection()
    try:
        conn.autocommit = False  # Disable autocommit mode
        toxic_analysis = hs_check_comment(comment[2])  # Analyze body
        if toxic_analysis is None:
            conn.rollback()
            return  # Skip if error occurred
        with conn.cursor() as cursor:
            # Get subreddit from the parent post
            cursor.execute('SELECT subreddit FROM public.reddit_posts WHERE id = %s;', (comment[1],))
            result = cursor.fetchone()
            subreddit = result[0] if result else None

            # Check if the post exists in processed_reddit_posts
            cursor.execute('SELECT 1 FROM public.processed_reddit_posts WHERE id = %s;', (comment[1],))
            if cursor.fetchone() is None:
                # Process the parent post on-the-fly
                parent_post = fetch_post_by_id(comment[1])
                if parent_post:
                    process_single_post(parent_post, conn)  # Pass the existing connection
                else:
                    # Parent post not found in original posts
                    print(f"Parent post {comment[1]} not found. Skipping comment {comment[0]}.")
                    conn.rollback()
                    return

            cursor.execute(
                '''
                INSERT INTO public.processed_reddit_comments
                (id, post_id, body, created_utc, score, subreddit, toxic_analysis)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    post_id = EXCLUDED.post_id,
                    body = EXCLUDED.body,
                    created_utc = EXCLUDED.created_utc,
                    score = EXCLUDED.score,
                    subreddit = EXCLUDED.subreddit,
                    toxic_analysis = EXCLUDED.toxic_analysis;
                ''',
                (comment[0], comment[1], comment[2], comment[3], comment[4], subreddit, toxic_analysis)
            )
        conn.commit()
        print(f"Processed comment {comment[0]}: Toxicity Analysis = {toxic_analysis}")
    except Exception as e:
        conn.rollback()
        print(f"Error processing comment {comment[0]}: {e}")
    finally:
        conn.close()

def run_toxicity_pipeline():
    print("Starting toxicity analysis pipeline...")

    # Fetch data
    posts = fetch_posts()
    comments = fetch_comments()

    # Process in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(process_posts, posts)
        executor.submit(process_comments, comments)

    print("Toxicity analysis pipeline completed.")

if __name__ == "__main__":
    run_toxicity_pipeline()
