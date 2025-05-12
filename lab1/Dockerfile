FROM postgres:16

RUN apt-get update && \
    apt-get install -y wget zip make gcc postgresql-server-dev-16 && \
    wget https://github.com/pgbigm/pg_bigm/archive/refs/heads/master.zip -O pg_bigm.zip && \
    unzip pg_bigm.zip && \
    cd pg_bigm-master && \
    make USE_PGXS=1 && \
    make USE_PGXS=1 install && \
    cd .. && \
    rm -rf pg_bigm-master pg_bigm.zip && \
    apt-get purge -y wget zip make gcc postgresql-server-dev-16 && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*