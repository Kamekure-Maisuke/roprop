FROM postgres:18-bookworm

RUN apt update -yqq && \
    apt install -y -V --no-install-recommends \
    ca-certificates lsb-release wget && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

RUN wget https://packages.groonga.org/debian/groonga-apt-source-latest-$(lsb_release --codename --short).deb && \
    apt install -y -V ./groonga-apt-source-latest-$(lsb_release --codename --short).deb && \
    apt update -yqq && \
    apt install -y -V --no-install-recommends postgresql-18-pgdg-pgroonga && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*