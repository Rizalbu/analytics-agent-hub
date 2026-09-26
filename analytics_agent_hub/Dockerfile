FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Expose port (Railway provides PORT env, default 8000)
EXPOSE 8000

# Set environment variables for standalone mode
ENV HUB_DB_PATH=/app/data/warehouse/funnel.duckdb
ENV HUB_SHEETS_DIR=/app/data/sheets
ENV HUB_SYNC_DB=/app/data/sync.duckdb

# Run startup script (bootstraps data + starts server)
CMD ["./start.sh"]
