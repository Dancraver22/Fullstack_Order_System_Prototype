FROM python:3.11-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

# Copy the startup script into the container
COPY ./start.sh /code/start.sh
RUN chmod +x /code/start.sh

# Use Docker JSON array syntax with the shell wrapper to handle the port dynamically
CMD ["/code/start.sh"]