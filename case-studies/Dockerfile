FROM case-study:firefox

FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y tzdata ca-certificates wget firefox python3 python3-pip
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz \
    && tar -x geckodriver -zf geckodriver-v0.30.0-linux64.tar.gz -O > /usr/bin/geckodriver \
    && chmod +x /usr/bin/geckodriver
RUN pip install click

COPY --from=0 /nix /nix
COPY --from=0 /bin /nix-bin
ENV PATH="/nix-bin:${PATH}"
RUN ln -s /usr/bin/python3 /usr/bin/python

CMD ["/bin/run-case-study"]