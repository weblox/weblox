FROM python:3.7-alpine as alpine
RUN apk add build-base

FROM alpine as alpine-devel
ADD requirements.txt /
RUN pip install -r requirements.txt

FROM alpine-devel as base
ADD * /
CMD [ "python", "./infra.py" ]