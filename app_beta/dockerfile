FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8889
CMD ["gunicorn", "--workers=2", "--threads=4", "--bind=0.0.0.0:8889", "app:app"]
