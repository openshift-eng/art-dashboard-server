FROM registry.redhat.io/ubi9/ubi-minimal:latest
RUN microdnf install -y python pip && python3 -m pip install --upgrade pip && pip3 install slack_sdk requests
COPY check_schedule.py /check_schedule.py
