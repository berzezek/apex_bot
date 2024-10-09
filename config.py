from dotenv import dotenv_values


config = dotenv_values(".env")

TOKEN = config.get("TOKEN", None)
CSV_FILE = config.get("CSV_FILE", None)
