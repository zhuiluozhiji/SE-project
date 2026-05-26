FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl imagemagick tesseract-ocr tesseract-ocr-chi-sim \
    && curl -fsSL --retry 5 \
        -o /usr/share/tesseract-ocr/5/tessdata/chi_sim_vert.traineddata \
        https://raw.githubusercontent.com/tesseract-ocr/tessdata/main/chi_sim_vert.traineddata \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /workspace/backend
COPY tests /workspace/tests
COPY pytest.ini /workspace/pytest.ini
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
