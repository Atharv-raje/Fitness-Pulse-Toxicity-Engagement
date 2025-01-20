import schedule
import time
from toxicity_pipeline import process_comments_parallel

schedule.every(30).minutes.do(process_comments_parallel)

print("Toxicity analysis scheduler started. Press Ctrl+C to stop.")

# Run once at startup
process_comments_parallel()

while True:
    schedule.run_pending()
    time.sleep(1)