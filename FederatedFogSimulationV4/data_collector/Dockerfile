FROM python:3.10-slim

WORKDIR /data_collector

COPY . .

RUN pip3 install -r requirements.txt

CMD ["python3", "-u", "data_collector.py"]