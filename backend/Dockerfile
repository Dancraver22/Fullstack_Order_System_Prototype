FROM python:3.11-slim

# Set working directory
WORKDIR /code

# Copy requirements first to leverage Docker caching
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of your application code
COPY ./app /code/app

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT