# SOURCE: https://gist.github.com/runeb/ed1a64859a7c762d9b6f5d41a8c63521
FROM postgres:16-bullseye
ARG PGVECTOR_VERSION=0.6.1

RUN apt-get update
RUN apt-get install -y \
            git \
            build-essential \
            postgresql-server-dev-16

# Clone and install pgvector
RUN git clone --branch v${PGVECTOR_VERSION} https://github.com/pgvector/pgvector.git
RUN cd pgvector && \
    make && \
    make install

# Clean up
RUN apt-get remove -y git build-essential postgresql-server-dev-16 && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set environment variables
ENV POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=postgres \
    POSTGRES_DB=lexy \
    POSTGRES_TEST_DB=lexy_tests

# Copy init script
COPY ./docker/postgres/init-db.sh /docker-entrypoint-initdb.d/init-db.sh
