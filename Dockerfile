#
# Use docker-ce to persist volumes with --mount
#
# docker run -p=60160:60160 --mount=source=data,target=/tmp/db/
#

FROM python:3.6.8-slim-stretch

RUN mkdir /tmp/db

RUN apt-get update && apt-get -y --no-install-recommends upgrade
RUN apt-get install -y apt-utils libterm-readline-gnu-perl gcc

RUN mkdir /app
RUN python3 --version
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools
COPY ./requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

RUN apt-get remove -y python3-dev python3-pip gcc g++ --purge
RUN apt-get autoremove -y
RUN apt-get install -y
RUN rm -rf /var/lib/apt/lists/*
RUN rm -rf /root/.cache

RUN rm -rf /tmp/requirements.txt

COPY . /app

CMD ["/app/dockerrun.sh"]