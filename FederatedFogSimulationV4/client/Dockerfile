FROM python:3.10-slim

WORKDIR /client

COPY . .

RUN pip3 install -r requirements.txt

CMD ["python3", "-u", "client.py"]