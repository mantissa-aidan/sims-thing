# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Add Python's user script directory to PATH to find executables like pytest
ENV PATH="/root/.local/bin:${PATH}"

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --user can sometimes help with permissions and pathing for executables
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Make port 5001 available to the world outside this container
EXPOSE 5001

# Define environment variables for Flask. FLASK_DEBUG for development.
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=1
# FLASK_RUN_HOST and FLASK_RUN_PORT are set in the CMD or docker-compose command

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]

# Note: MONGODB_URI and OLLAMA_BASE_URL should be passed at runtime or via docker-compose for security and flexibility. 