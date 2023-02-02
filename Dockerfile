FROM submitty/python:3.7
COPY ./redis_key_mig /app
WORKDIR /app
RUN /bin/bash -c 'pwd;ls -l /app'
#RUN  /usr/local/bin/python -m pip install --upgrade pip
RUN pip3 install redis==3.5.3
cmd ["python", "/app/redisMigrate.py"]
