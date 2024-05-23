FROM python:alpine
LABEL authors="matti"

COPY . /code
WORKDIR /code
RUN python -m pip install -r requirements.txt

ENTRYPOINT ["python", "bot.py"]