# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /project_epsilon

# Copy the current directory contents into the container at /app
COPY . /project_epsilon

# Install Poetry
# RUN pip install poetry
# RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to the PATH
# ENV PATH="$HOME/.local/bin:$PATH"

# Configure Poetry to not create a virtual environment
# RUN poetry config virtualenvs.create false

# Install dependencies using Poetry
# RUN poetry install --no-dev
RUN pip install -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run app.py when the container launches
CMD ["poetry", "run", "python", "flask_app.py"]