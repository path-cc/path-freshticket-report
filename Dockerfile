FROM python:3.14

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

CMD ["python", "main.py"]
