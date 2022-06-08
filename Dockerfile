FROM ghcr.io/binkhq/python:3.10-pipenv

WORKDIR /app
ADD . .

RUN apt-get update && apt-get -y install libtk8.6
RUN pipenv install --system --deploy --ignore-pipfile


# ENTRYPOINT [ "linkerd-await", "--" ]
CMD [ "python3", "index.py" ]
