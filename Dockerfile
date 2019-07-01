FROM python:3.6

RUN apt update && apt install -y libhunspell-dev
ADD ./ /usr/src/app/
WORKDIR /usr/src/app/
RUN pip3 install -r requirements.txt

CMD sleep infinity