FROM python:3.10-slim

WORKDIR /cloud

COPY ./requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "-u", "cloud.py"]