# TransmiEye · imagen para servidor (x86_64 o ARM, solo CPU)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
# PyTorch solo CPU (unos 700 MB en vez de los ~5 GB de la versión con CUDA)
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r backend/requirements.txt \
    && pip uninstall -y opencv-python && pip install opencv-python-headless

COPY backend backend
COPY frontend frontend
COPY modelos modelos
RUN mkdir -p videos data

EXPOSE 8000
WORKDIR /app/backend
CMD ["python", "run.py", "--red", "--proxy"]
