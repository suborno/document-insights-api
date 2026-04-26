# Document Insights API

Backend assignment for document processing and summarization.

Note: I decided to use MySQL instead of MongoDB for data storage.

## Setup Instructions

1. Start the services (MySQL and Redis):
   ```bash
   docker-compose up -d mysql redis
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```
