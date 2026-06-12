FROM python:3.9-slim

# System me Chrome aur zaroori tools install karna
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Python libraries install karna
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Playwright ke andar ka asli browser download karna
RUN playwright install chromium
RUN playwright install-deps

COPY . .

# Bot ko chalu karna
CMD ["python", "bot.py"]
