# Use an official Python runtime as a parent image
FROM python:3.7
ENV PYTHONUNBUFFERED 1

RUN apt-get update

COPY . /project
RUN pip install --upgrade pip
WORKDIR /project
RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN pip install uwsgi

EXPOSE 8000

RUN chmod +x start.sh
ENTRYPOINT ["sh", "./start.sh"]
