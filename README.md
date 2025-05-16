# IsDB - Finance Assistant

A conversational AI assistant for finance.

## Project Structure

- `rag/`: Backend service using RAG (Retrieval Augmented Generation)
- `isdb-frontend/`: Frontend React application with TypeScript

## Setup and Running Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/muohannedxd/isdb-finance.git
cd isdb-finance
```

### 2. Backend Setup (rag)

#### **Prerequisites:**
- Python 3.9+
- Conda (recommended for environment management)
- Together AI API key (Get it from [Together AI Platform](https://www.together.ai/))

#### **Steps:**

1. Navigate to the backend directory:
```bash
cd rag
```

2. Create and activate a Conda environment:
```bash
conda create -n rag-env
conda activate rag-env
```

3. Install requirements:
```bash
conda install --file requirements.txt
```
or:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the rag directory (see `.env.example`):
```bash
echo "TOGETHER_API_KEY=your_api_key_here" > .env
```

5. Add your documents:
- Place your pharmaceutical documents in `rag/data/`
- Supported formats: PDF, TXT, DOCX, etc.

6. Create the vector database:
```bash
python create_database.py
```

7. Run the backend:
- For CLI testing:
```bash
python query_data.py
```
- For the web API server:
```bash
python app.py
```

The backend server will start on http://localhost:5001

### 3. Frontend Setup (isdb-frontend)

#### **Prerequisites:**
- Node.js 16+
- npm or yarn

#### **Steps:**

1. Navigate to the frontend directory:
```bash
cd isdb-frontend
```

2. Install dependencies:
```bash
npm install
# or if using yarn
yarn install
```

3. Start the development server:
```bash
npm run dev
# or if using yarn
yarn dev
```

The frontend application will be available at http://localhost:5173

## Usage

1. Make sure both backend and frontend servers are running
2. Access the web interface at http://localhost:5173
3. Start asking questions about pharmaceutical processes, procedures, and documentation

## Notes

- The backend uses Together AI's LLM through their API for generating responses
- Documents are processed and stored in a Chroma vector database for efficient retrieval
- The frontend uses React with TypeScript and modern UI components
- All conversations are stored locally in the browser's localStorage

## License

MIT License - See LICENSE file for details
