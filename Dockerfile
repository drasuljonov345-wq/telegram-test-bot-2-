# 1. Python 3.10 versiyasini tanlaymiz (eng barqaror)
FROM python:3.10-slim

# 2. Tesseract OCR va kerakli kutubxonalarni serverga o'rnatamiz
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Ishchi papkani yaratamiz
WORKDIR /app

# 4. Kutubxonalarni o'rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Bot kodini nusxalaymiz
COPY . .

# 6. Botni ishga tushirish (Asosiy faylingiz main.py bo'lsa)
CMD ["python", "main.py"]
