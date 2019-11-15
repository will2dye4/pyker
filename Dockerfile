FROM python:3.7-alpine

# Copy package into container
COPY . /pyker
WORKDIR /pyker

# Install package
RUN python setup.py install

# Run Python interpreter
CMD python
