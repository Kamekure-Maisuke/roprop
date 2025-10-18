FROM postgres:18-bookworm

WORKDIR /tmp

RUN apt-get update -yqq && \
    apt-get install -y -V --no-install-recommends \
    ca-certificates lsb-release wget && \
    wget https://packages.groonga.org/debian/groonga-apt-source-latest-$(lsb_release --codename --short).deb && \
    apt-get install -y -V ./groonga-apt-source-latest-$(lsb_release --codename --short).deb && \
    rm -f ./groonga-apt-source-latest-*.deb && \
    apt-get update -yqq && \
    apt-get install -y -V --no-install-recommends postgresql-18-pgdg-pgroonga && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*