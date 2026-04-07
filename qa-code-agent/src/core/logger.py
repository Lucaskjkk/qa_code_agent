import logging
import logging.config
import yaml
import os

def setup_logging(default_path="configs/logging.yaml", default_level=logging.INFO):
    if os.path.exists(default_path):
        with open(default_path, "r") as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

def get_logger(name):
    setup_logging()
    return logging.getLogger(name)
