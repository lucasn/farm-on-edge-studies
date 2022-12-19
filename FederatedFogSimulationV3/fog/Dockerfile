FROM python:3.9.15-slim

WORKDIR /fog

COPY . .

RUN pip3 install -r requirements.txt

CMD ["python3", "-u", "fog.py"]