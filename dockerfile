# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /project_epsilon

# Copy the current directory contents into the container at /app
COPY . /project_epsilon

# Install Poetry
RUN pip install poetry

# Install dependencies using Poetry
RUN poetry install

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["poetry", "run", "python", "flask_app.py"]