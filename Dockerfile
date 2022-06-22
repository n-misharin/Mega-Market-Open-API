FROM python:3

WORKDIR C:/Users/nikita/Desktop/projects/yandex-backend

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

CMD ["python", "main.py"]
