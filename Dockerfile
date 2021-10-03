FROM python:3.9.7-bullseye
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY metrics_server /app/metrics_server
CMD [ "python3", "-m", "metrics_server" ]
