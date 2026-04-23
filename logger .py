import logging, os

LOG_DIR = "data/logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"{LOG_DIR}/bot.log"),
        logging.StreamHandler()
    ]
)

def log(msg, level="INFO"):
    if level == "INFO":
        logging.info(msg)
    elif level == "ERROR":
        logging.error(msg)
    elif level == "WARNING":
        logging.warning(msg)
    else:
        print(msg)
