import time
import schedule
from toxicity_analyzer import run_toxicity_pipeline

# Schedule the pipeline to run every 10 minutes
schedule.every(10).minutes.do(run_toxicity_pipeline)

print("Toxicity analysis scheduler started. Press Ctrl+C to exit.")

# Run the pipeline once at startup
run_toxicity_pipeline()

while True:
    schedule.run_pending()
    time.sleep(1)
