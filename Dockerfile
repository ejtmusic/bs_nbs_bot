# Use a slightly older, more stable Python base image
FROM python:3.10-bullseye

# Install system build tools
RUN apt-get update && apt-get install -y build-essential git

# Install Python packages
RUN pip install pandas scikit-learn numpy
RUN pip install git+https://github.com/InjectiveLabs/sdk-python.git

# Keep the container running
CMD ["tail", "-f", "/dev/null"]