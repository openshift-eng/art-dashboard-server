FROM fedora:32
USER root
RUN dnf install -y \
    # runtime dependencies
    krb5-workstation python3.6 python3-pip krb5-devel openssl-devel
WORKDIR /opt/app-root/src
COPY requirements.txt ./
RUN pip3.6 install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python3", "manage.py", "runserver", "8080"]
