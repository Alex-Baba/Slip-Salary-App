# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install dependencies
COPY rquirements.txt /code/
RUN pip install --upgrade pip \
	&& pip install -r rquirements.txt

# Copy project files
COPY . /code/

# Ensure entrypoint script is executable
RUN chmod +x /code/docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Default command
ENTRYPOINT ["/code/docker-entrypoint.sh"]
