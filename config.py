import os
from dotenv import load_dotenv
from models import ClientConfig

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

DEFAULT_CLIENT = ClientConfig(
    client_name="Poni Insurtech",
    keywords=["Poni", "Poni Insurtech", "Poni Insurance"],
    competitors=[
        "Bolttech",
        "Igloo",
        "Singlife",
        "FWD Insurance",
        "ZA Tech",
    ],
    markets=["Singapore", "Hong Kong", "Southeast Asia", "Asia Pacific"],
    industry_keywords=[
        "insurtech",
        "insurance technology",
        "digital insurance",
        "embedded insurance",
        "parametric insurance",
        "microinsurance",
    ],
)
