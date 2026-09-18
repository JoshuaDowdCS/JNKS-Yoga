# Stage 1: build the Next.js static export (next.config.ts has output: "export").
FROM node:20-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Empty API/WS URLs make the frontend call the same origin it was served from.
ENV NEXT_PUBLIC_API_URL="" NEXT_PUBLIC_WS_URL=""
RUN npm run build

# Stage 2: FastAPI serves the API, the WebSockets, and the exported frontend.
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*
COPY pipeline/requirements.txt pipeline/requirements.txt
RUN pip install --no-cache-dir -r pipeline/requirements.txt
COPY pipeline ./pipeline
COPY api.py .
COPY --from=frontend /app/out ./out
ENV PORT=8001
EXPOSE 8001
CMD ["python", "-m", "pipeline.server"]
