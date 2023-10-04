# SOURCE: https://gist.github.com/runeb/ed1a64859a7c762d9b6f5d41a8c63521
FROM postgres:15.4-bullseye

RUN apt-get update
RUN apt-get install -y git build-essential postgresql-server-dev-15

# Clone and install pg_embedding
# Make the operation idempotent to avoid issues when Docker reuses partial images
RUN if [ ! -d "pg_embedding/.git" ]; then git clone https://github.com/neondatabase/pg_embedding.git && echo "Repo cloned"; else echo "Repo exists"; fi
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
