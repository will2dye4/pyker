FROM python:3.7-alpine

COPY . /pyker

WORKDIR /pyker
RUN python setup.py install
CMD python

