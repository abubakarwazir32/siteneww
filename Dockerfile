# Python + Playwright ke liye official image
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Dependencies install karo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source code copy karo
COPY . .

# Port expose karo
EXPOSE 8000

# App chalaao
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
