from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import logging
from routes import register_blueprints

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("islamic_finance_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("islamic_finance_api")

app = Flask(__name__)
# Add CORS support to allow requests from frontend
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Register all blueprints
register_blueprints(app)

if __name__ == "__main__":
    logger.info("Starting Islamic Finance API server")
    app.run(host="0.0.0.0", port=5001)