# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Install build tools and dependencies
RUN apt-get update && apt-get install -y gcc

# Install any needed packages
RUN pip install --no-cache-dir streamlit

# Copy the current directory contents into the container at /app
COPY app.py /app/

# Expose the port that Streamlit will run on
EXPOSE 8501

# Run Streamlit when the container starts
CMD ["streamlit", "run", "app.py"]
