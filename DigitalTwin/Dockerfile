FROM python:3.11-slim

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONDONTWRITEBYTECODE=1 \
    COGNITIVE_TWIN_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    wget \
    ffmpeg \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    libmagic1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    tzdata \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Set locale and timezone
RUN ln -fs /usr/share/zoneinfo/UTC /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml /app/
RUN pip install --upgrade pip && \
    pip install -e . && \
    python -m spacy download en_core_web_trf && \
    python -m nltk.downloader punkt wordnet stopwords vader_lexicon

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/data/raw /app/data/interim /app/data/processed /app/data/models /app/logs

# Set up volume mount points
VOLUME ["/app/data", "/app/logs", "/app/config"]

# Set entrypoint
ENTRYPOINT ["python", "-m", "cognitive_twin.cli"]

# Default command
CMD ["run", "--all"]