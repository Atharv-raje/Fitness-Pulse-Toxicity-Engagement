import logging
from db_connector import get_db_connection
from fourchan_client import FourChanClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FourChanCrawler")

def insert_posts_into_db(posts, conn, board_name):
    try:
        with conn.cursor() as cur:  # Initialize the cursor correctly here
            cur.execute("SET search_path TO fourchan_schema;")
            for post in posts:
                try:
                    cur.execute("""
                        INSERT INTO fourchan_schema.chanposts (post_id, name, comment, filename, ext, w, h, time, resto, board_name)
                        VALUES (%(post_id)s, %(name)s, %(comment)s, %(filename)s, %(ext)s, %(w)s, %(h)s, %(time)s, %(resto)s, %(board_name)s)
                        ON CONFLICT (post_id) DO NOTHING;
                    """, {
                        'post_id': post.get('no'),
                        'name': post.get('name', ''),
                        'comment': post.get('com', ''),
                        'filename': post.get('filename', ''),
                        'ext': post.get('ext', ''),
                        'w': post.get('w'),
                        'h': post.get('h'),
                        'time': post.get('time'),
                        'resto': post.get('resto', 0),
                        'board_name': board_name
                    })
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Error inserting post {post.get('no')}: {e}")
    except Exception as e:
        logger.error(f"Error initializing cursor or inserting posts: {e}")

def fetch_threads_and_store(board="fit"):
    client = FourChanClient()
    conn = get_db_connection()
    try:
        catalog = client.get_catalog(board)
        for page in catalog:
            for thread in page.get("threads", []):
                thread_posts = client.get_thread(board, thread["no"]).get("posts", [])
                insert_posts_into_db(thread_posts, conn, board)
    except Exception as e:
        logger.error(f"Error during crawl: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fetch_threads_and_store()