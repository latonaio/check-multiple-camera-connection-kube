FROM latonaio/l4t:latest

# Definition of a Device & Service
ENV POSITION=Runtime \
    SERVICE=check-multiple-camera-connection \
    AION_HOME=/var/lib/aion

# Setup Directoties
RUN mkdir -p /${AION_HOME}/$POSITION/$SERVICE

WORKDIR /${AION_HOME}/$POSITION/$SERVICE

RUN apt-get update && apt-get install -y \
    v4l-utils \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ADD . .
RUN python3 setup.py install

CMD ["python3", "-m", "chkcamera"]
