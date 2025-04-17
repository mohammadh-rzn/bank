# Backend Dockerfile
FROM python:3.9

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy the application files
COPY . .

# Expose port for Django
EXPOSE 8000

# Run database migrations and then start the Django server
CMD python manage.py migrate && python manage.py runserver 0.0.0.0:8000
