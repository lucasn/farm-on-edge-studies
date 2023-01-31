FROM python:3.10-slim

WORKDIR /fog

RUN apt update

RUN apt install -y iputils-ping

COPY ./requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "-u", "fog.py"]