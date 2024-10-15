# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /bot

# Copy the appSettings.local.json file to the working directory
COPY appSettings.local.json .

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on (if needed)
EXPOSE 8000

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the bot when the container launches
CMD ["python3", "src/bot.py"]
