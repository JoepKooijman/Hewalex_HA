FROM python:3.7-alpine/

COPY ./requirements.txt requirements.txt
RUN pip3 install -r /requirements.txt && rm requirements.txt

COPY ./hewalexconfig.ini ./hewagate/hewalexconfig.ini
COPY ./*.py ./hewagate/

RUN ls -la /hewagate/*

ENTRYPOINT [ "python3", "/hewagate/hewalex.py" ]
