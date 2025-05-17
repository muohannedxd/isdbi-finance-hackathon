# IsDB - Finance Assistant

A conversational AI assistant for finance.

## Project Structure

- `usecase-service/`: Backend service for Islamic finance use cases (Port 5001)
- `reverse-transaction-service/`: Backend service for reverse transaction analysis (Port 5002)
- `isdb-frontend/`: Frontend React application with TypeScript (Port 5173)

## Setup and Running Instructions

### Option 1: Running Services Individually

#### 1. Clone the Repository

```bash
git clone https://github.com/muohannedxd/isdb-finance.git
cd isdb-finance
```

#### 2. Usecase Service Setup (Port 5001)

##### **Prerequisites:**
- Python 3.9+
- Conda (recommended for environment management)
- Together AI API key (Get it from [Together AI Platform](https://www.together.ai/))

##### **Steps:**

1. Navigate to the usecase service directory:
```bash
cd usecase-service
```

2. Create and activate a Conda environment:
```bash
conda create -n usecase-env python=3.9
conda activate usecase-env
```

3. Install requirements:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the usecase-service directory (see `.env.example`):
```bash
# Add your API keys and configuration
```

5. Run the service:
```bash
python app.py
```

The usecase service will start on http://localhost:5001

#### 3. Reverse Transaction Service Setup (Port 5002)

##### **Prerequisites:**
- Python 3.9+
- Gemini API key

##### **Steps:**

1. Navigate to the reverse transaction service directory:
```bash
cd reverse-transaction-service
```

2. Create and activate a Conda environment:
```bash
conda create -n reverse-env python=3.9
conda activate reverse-env
```

3. Install requirements:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the reverse-transaction-service directory (see `.env.example`):
```bash
# Add your GEMINI_API_KEY
```

5. Run the service:
```bash
python app.py
```

The reverse transaction service will start on http://localhost:5002

#### 4. Frontend Setup (Port 5173)

##### **Prerequisites:**
- Node.js 16+
- npm or yarn

##### **Steps:**

1. Navigate to the frontend directory:
```bash
cd isdb-frontend
```

2. Install dependencies:
```bash
yarn install
```

3. Start the development server:
```bash
yarn dev
```

The frontend application will be available at http://localhost:5173

### Option 2: Running with Docker

#### **Prerequisites:**
- Docker and Docker Compose installed on your system

#### **Steps:**

1. Clone the Repository:
```bash
git clone https://github.com/muohannedxd/isdb-finance.git
cd isdb-finance
```

2. Set up environment variables:
   - Create/update `.env` files in both service directories with your API keys

3. Build and start all services:
```bash
docker-compose up -d
```

This will start:
- Usecase service on http://localhost:5001
- Reverse transaction service on http://localhost:5002
- Frontend on http://localhost:5173

4. To stop all services:
```bash
docker-compose down
```

## Usage

1. Make sure all services are running (either individually or with Docker)
2. Access the web interface at http://localhost:5173
3. Start using the Islamic finance assistant

## Notes

- The usecase service uses Together AI's LLM through their API for generating responses
- The reverse transaction service uses Google's Gemini API for transaction analysis
- Documents are processed and stored in a Chroma vector database for efficient retrieval
- The frontend uses React with TypeScript and modern UI components
- All conversations are stored locally in the browser's localStorage

## License

MIT License - See LICENSE file for details
