# Use a slightly older, more stable Python base image
FROM python:3.10-bullseye

# Install system build tools required for some Python packages
RUN apt-get update && apt-get install -y build-essential git



# Install all Python dependencies
RUN pip install \
    "git+https://github.com/InjectiveLabs/sdk-python.git@master" \
    hyperliquid-python-sdk \
    ccxt \
    pandas scikit-learn==1.6.1 numpy python-dotenv python-telegram-bot joblib pytz

# Keep the container running so we can connect to it
CMD ["tail", "-f", "/dev/null"]