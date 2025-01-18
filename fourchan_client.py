import logging
import requests

# Logger setup
logger = logging.getLogger("FourChanClient")
logger.setLevel(logging.INFO)
if not logger.handlers:
    sh = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    sh.setFormatter(formatter)
    logger.addHandler(sh)

class FourChanClient:
    API_BASE = "https://a.4cdn.org"

    def get_catalog(self, board):
        try:
            api_call = f"{self.API_BASE}/{board}/catalog.json"
            return self.execute_request(api_call)
        except Exception as e:
            logger.error(f"Error fetching catalog for board {board}: {e}")
            return None

    def get_thread(self, board, thread_number):
        try:
            api_call = f"{self.API_BASE}/{board}/thread/{thread_number}.json"
            return self.execute_request(api_call)
        except Exception as e:
            logger.error(f"Error fetching thread {thread_number} from board {board}: {e}")
            return None

    def execute_request(self, api_call):
        try:
            logger.info(f"Making API call: {api_call}")
            resp = requests.get(api_call)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            return None

if __name__ == "__main__":
    client = FourChanClient()
    # Example usage: client.get_catalog("fit")