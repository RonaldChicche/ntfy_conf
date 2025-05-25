import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///data.db")
    NTFY_URL = os.getenv("NTFY_URL", "http://localhost:80/")
    PLC_DWORD_VALUE = int(os.getenv("PLC_DWORD_VALUE", 32))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HISTORY_FILE = os.getenv("HISTORY_FILE")
    OPC_CLIENT = None
    TAGS_NODE = os.getenv("TAGS_NODE")

