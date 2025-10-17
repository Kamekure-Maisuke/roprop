FROM postgres:18-bookworm

RUN apt-get update -yqq && \
    apt-get install -y -V --no-install-recommends \
    ca-certificates lsb-release wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

RUN wget https://packages.groonga.org/debian/groonga-apt-source-latest-$(lsb_release --codename --short).deb && \
    apt-get install -y -V ./groonga-apt-source-latest-$(lsb_release --codename --short).deb && \
    apt-get update -yqq && \
    apt-get install -y -V --no-install-recommends postgresql-18-pgdg-pgroonga && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*