FROM python:3.7-buster

RUN pip install pipenv && \
    adduser --disabled-password --gecos "pyslackops user" pyslackops

WORKDIR /home/pyslackops
USER pyslackops

COPY Pipfile* /home/pyslackops/
RUN pipenv sync
COPY . /home/pyslackops/

CMD ["pipenv", "run", "python", "main.py"]
