FROM mcr.microsoft.com/vscode/devcontainers/python:3.7

RUN pipx install pipenv

RUN mkdir /home/vscode/app
WORKDIR /home/vscode/app

COPY Pipfile Pipfile.lock .
RUN pipenv sync

COPY . .
