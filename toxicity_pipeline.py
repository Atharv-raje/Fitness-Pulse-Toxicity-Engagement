import psycopg2
import requests
from db_connector import get_db_connection
from concurrent.futures import ThreadPoolExecutor
import logging
from dotenv import load_dotenv
import os

load_dotenv()

# Constants
API_TOKEN = os.getenv('MODERATE_HATESPEECH_API_TOKEN')
CONF_THRESHOLD = 0.9

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ToxicityPipeline")

def fetch_comments():
    """
    Fetch unprocessed comments from the chanposts table in four_chan_schema.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            logger.info("Fetching unprocessed comments from four_chan_schema.chanposts table...")
            cursor.execute("""
                SELECT post_id, name, comment, filename, ext, w, h, time, resto, board_name
                FROM four_chan_schema.chanposts
                WHERE comment IS NOT NULL
                  AND post_id NOT IN (SELECT post_id FROM four_chan_schema.processed_chanposts);
            """)
            comments = cursor.fetchall()
            logger.info(f"Fetched {len(comments)} comments.")
            return comments
    except psycopg2.Error as e:
        logger.error(f"Error fetching comments: {e}")
        return []
    finally:
        conn.close()

def analyze_toxicity(comment_text):
    """
    Perform toxicity analysis on the comment using the ModerateHateSpeech API.
    """
    data = {"token": API_TOKEN, "text": comment_text}
    try:
        response = requests.post("https://api.moderatehatespeech.com/api/v1/moderate/", json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        is_toxic = 1 if result.get("class") == "flag" and float(result.get("confidence", 0)) > CONF_THRESHOLD else 0
        return is_toxic
    except requests.RequestException as e:
        logger.error(f"Error analyzing comment: {e}")
        return None

def store_processed_comment(comment, toxic_analysis):
    """
    Store the processed comment in the processed_chanposts table in four_chan_schema.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            logger.info(f"Storing processed comment with post_id: {comment[0]}...")
            cursor.execute("""
                INSERT INTO four_chan_schema.processed_chanposts
                (post_id, name, comment, filename, ext, w, h, time, resto, board_name, toxic_analysis)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (post_id) DO NOTHING;
            """, comment + (toxic_analysis,))
            conn.commit()
            logger.info(f"Stored comment {comment[0]} with Toxicity Analysis = {toxic_analysis}")
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Error storing processed comment {comment[0]}: {e}")
    finally:
        conn.close()

def process_comment(comment):
    """
    Process a single comment: perform toxicity analysis and store the result.
    """
    toxic_analysis = analyze_toxicity(comment[2])  # Analyze the ⁠ comment ⁠ field
    if toxic_analysis is not None:
        store_processed_comment(comment, toxic_analysis)

def process_comments_parallel():
    """
    Process all comments in parallel.
    """
    comments = fetch_comments()
    if not comments:
        logger.info("No unprocessed comments found.")
        return

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(process_comment, comments)

if __name__ == "__main__":
    logger.info("Starting Toxicity Analysis Pipeline...")
    process_comments_parallel()
    logger.info("Toxicity Analysis Pipeline completed.")