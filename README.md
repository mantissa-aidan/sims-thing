# Python Backend with MongoDB, Langchain, and Ollama

This project is a Python-based backend service that integrates with MongoDB for data storage and uses Langchain to interact with a locally hosted Ollama model.

## Prerequisites

- Python 3.8+
- Pip (Python package installer)
- MongoDB instance running (local or remote)
- Ollama service running and accessible (e.g., at `http://192.168.0.190:11434`)
  - Ensure you have pulled a model, e.g., `ollama pull llama2`

## Setup

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root of the project directory and add the following variables. Update them according to your setup:
    ```env
    MONGODB_URI="mongodb://host.docker.internal:27017/sims_mud_db"
    OLLAMA_BASE_URL="http://192.168.0.190:11434"
    OLLAMA_MODEL="qwen2:8b"
    FLASK_APP="app.py"
    FLASK_DEBUG="1"
    ```
    - Use `host.docker.internal` for `MONGODB_URI` (or `OLLAMA_BASE_URL`) if the service (MongoDB/Ollama) is running directly on the same machine that is running Docker Desktop (Mac/Windows).
    - If Ollama (or MongoDB) is running on a different machine on your local network, use its specific IP address (e.g., `http://192.168.0.190:11434` as shown for Ollama).
    - If Ollama and MongoDB are running as other Docker containers managed by the same Docker Compose file (not the case here), you would typically use the service names (e.g., `http://ollama:11434`).

## Running the Application

1.  **Ensure your MongoDB server is running.**
2.  **Ensure your Ollama service is running and the specified model in `app.py` (default: `llama2`) is available.**
    You can run Ollama with a specific model using:
    ```bash
    ollama serve
    # In another terminal, if you haven't pulled the model:
    # ollama pull llama2 
    ```

3.  **Start the Flask application:**
    ```bash
    python app.py
    ```
    The application will typically start on `http://0.0.0.0:5001`.

## Dockerizing the Application

This application can be containerized using Docker. While you can use `docker build` and `docker run` directly (see older instructions below if needed), the recommended method is using Docker Compose.

**Using Docker Compose (Recommended)**

Two Docker Compose files are provided:
- `docker-compose.yml`: For running the main application.
- `docker-compose.test.yml`: For running tests.

1.  **Environment Variables (`.env` file):**
    Make sure you have a `.env` file in the root of your project. Docker Compose will load this. Key variables:
    ```env
    # MONGODB_URI is now typically set within the docker-compose.yml files to 'mongodb://mongo:27017/sims_mud_db'
    # to connect to the MongoDB service also managed by Docker Compose.
    # You can still have it here for reference or for running app.py outside Docker Compose.
    # MONGODB_URI="mongodb://localhost:27017/sims_mud_db"

    OLLAMA_BASE_URL="http://192.168.0.190:11434" # Your actual Ollama IP and port
    OLLAMA_MODEL="qwen2:8b" # Specify the Ollama model to use (default in app.py is qwen2:8b)
    FLASK_APP="app.py"
    FLASK_DEBUG="1"
    ```
    - `OLLAMA_BASE_URL`: If Ollama is running on a different machine on your local network, use its specific IP address. If it were running on the same machine as Docker Desktop (and not in another container managed by compose), you might use `http://host.docker.internal:11434`.
    - `OLLAMA_MODEL`: Specifies which model Ollama should serve. Ensure this model is available in your Ollama instance (e.g., via `ollama pull qwen2:8b`).
    - The `app` and `test` services in the `docker-compose*.yml` files are configured to connect to a MongoDB container named `mongo` using `MONGODB_URI=mongodb://mongo:27017/sims_mud_db`.

2.  **Running the Application (with MongoDB):**
    ```bash
    docker-compose up --build
    ```
    This command will now also start a MongoDB container if it's not already running. The application service (`app`) will wait for the MongoDB service (`mongo`) to be available before starting (due to `depends_on`).

3.  **Running Tests (with MongoDB):**
    ```bash
    docker-compose -f docker-compose.test.yml up --build --exit-code-from test --remove-orphans test
    ```
    This will also start a MongoDB container (or connect to an existing one if defined with the same service name and network, though here we use `sims-thing-mongo-test` container name and `mongo` service name). The tests will run against this database, and only the test runner's output will be shown. The command will also exit with the test suite's exit code and clean up containers afterwards.

**(Older) Docker Build and Run Instructions (using `run.sh` or manual commands):**

1.  **Build the Docker image:**
    Make sure you are in the root directory of the project (where the `Dockerfile` is located).
    ```bash
    docker build -t sims-thing .
    ```

2.  **Run the Docker container:**
    You need to pass the `MONGODB_URI` and `OLLAMA_BASE_URL` environment variables when running the container. 
    Replace `your_mongodb_connection_string` and `your_ollama_base_url` with your actual values.
    ```bash
    docker run -p 5001:5001 \
        -e MONGODB_URI="your_mongodb_connection_string" \
        -e OLLAMA_BASE_URL="your_ollama_base_url" \
        sims-thing
    ```
    For example, using the default local values:
    ```bash
    docker run -p 5001:5001 \
        -e MONGODB_URI="mongodb://host.docker.internal:27017/mydatabase" \
        -e OLLAMA_BASE_URL="http://host.docker.internal:11434" \
        sims-thing
    ```
    **Note for Docker Desktop users (Windows/Mac):** `host.docker.internal` can be used to refer to services running on your host machine from within the container. 
    If Ollama or MongoDB are running on a different machine accessible from your Docker host, use its IP address.

    The application inside the container will be accessible at `http://localhost:5001` on your host machine.

3.  **Using the `run.sh` script (Recommended):**
    A convenience script `run.sh` is provided to automate the build and run process.
    Make sure it's executable: `chmod +x run.sh`

    To run with default settings (MongoDB and Ollama accessible via `host.docker.internal`):
    ```bash
    ./run.sh
    ```

    To provide custom URIs:
    ```bash
    ./run.sh "your_mongodb_connection_string" "your_ollama_base_url"
    ```
    For example:
    ```bash
    ./run.sh "mongodb://myuser:mypass@192.168.1.100:27017/mydb" "http://192.168.1.101:11434"
    ```
    The script will stop and remove any existing container named `sims-thing-container` before starting a new one.

## API Endpoints

-   `GET /`
    -   A simple welcome message.
-   `GET /test_db`
    -   Tests the connection to the MongoDB database.
-   `POST /ask`
    -   Interacts with the Ollama model via Langchain.
    -   **Request Body (JSON):**
        ```json
        {
            "query": "Your question for the LLM"
        }
        ```
    -   **Success Response (JSON):**
        ```json
        {
            "response": "LLM's answer..."
        }
        ```
    -   **Error Response (JSON):**
        ```json
        {
            "error": "Error message..."
        }
        ```

## Testing

This project uses `pytest` for testing. The recommended way to run tests is using Docker Compose (see "Dockerizing the Application" section).

If you want to run tests in a local Python virtual environment (ensure MongoDB is accessible):

1.  **Create and activate a virtual environment (if not done):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate # or venv\Scripts\activate on Windows
    ```
2.  **Install dependencies (including pytest):**
    ```bash
    pip install pytest
    # or pip install -r requirements.txt if you are in an active venv
    ```

## Project Structure

```
/
|-- app.py                  # Main Flask application file
|-- requirements.txt        # Python dependencies
|-- .env                    # Environment variables (create this manually)
|-- project_checklist.md    # Project setup and task checklist
|-- README.md               # This file
|-- Dockerfile              # Docker build instructions
|-- run.sh                  # Script to build and run the Docker container
|-- tests/                  # Test files
|   |-- test_app.py         # Application tests
|-- venv/                   # Virtual environment directory (optional, if created)
```

## Further Development

-   Implement more robust error handling.
-   Add more specific API endpoints for your application's needs.
-   Expand MongoDB models and interactions.
-   Consider using Flask Blueprints for better organization as the app grows.
-   Add unit and integration tests. 