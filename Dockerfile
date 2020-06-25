FROM python:3
USER root
RUN pip3 install mysql-client
WORKDIR /opt/app-root/src
COPY requirements.txt ./
RUN pip3 install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python3", "manage.py", "runserver", "8080"]
