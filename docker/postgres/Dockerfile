# SOURCE: https://gist.github.com/runeb/ed1a64859a7c762d9b6f5d41a8c63521
FROM postgres:15.4-bullseye

RUN apt-get update && \
    apt-get upgrade -y
RUN apt-get install -y git build-essential postgresql-server-dev-15

# Clone and install pg_embedding
RUN git clone https://github.com/neondatabase/pg_embedding.git
RUN cd pg_embedding && \
    make && \
    make install

# Clean up
RUN apt-get remove -y git build-essential postgresql-server-dev-15 && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy init script
COPY ./docker/postgres/init-db.sh /docker-entrypoint-initdb.d/init-db.sh
