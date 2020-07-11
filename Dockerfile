FROM python:3.6
USER root
WORKDIR /opt/app-root/src
COPY requirements.txt ./
RUN pip3.6 install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python3", "manage.py", "runserver", "8080"]
