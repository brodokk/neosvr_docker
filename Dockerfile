FROM ubuntu:18.04

# Id of the user (buildtime)
ARG UID
ENV UID ${UID:-1000}
# Id of the user's group (buildtime)
ARG GID
ENV GID ${GROUP:-1000}
# Ids of the apps steamcmd will install. Ex 4020,232330
ARG INSTALL_APPS
ENV INSTALL_APPS ${INSTALL_APPS:-"740250"}
# Id of the app who will be launched
ARG STEAM_LAUNCH_APP
ENV STEAM_LAUNCH_APP ${STEAM_LAUNCH_APP:-"740250"}

# Steam credentials
ENV STEAM_USER ${STEAM_USER:-"anonymous"}
ENV STEAM_PWD ${STEAM_PWD:-""}
# Beta keys
ENV STEAM_BETA_NAME ${STEAM_BETA_NAME:-"headless-client"}
ENV STEAM_BETA_KEY ${STEAM_BETA_KEY:-""}

RUN echo steam steam/question select "I AGREE" | debconf-set-selections && \
    echo steam steam/license note '' | debconf-set-selections

ARG DEBIAN_FRONTEND=noninteractive

RUN dpkg --add-architecture i386 && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends ca-certificates locales steamcmd lib32tinfo5 tmux jq moreutils && \
    apt-get install -y gpg && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF &&\
    echo "deb https://download.mono-project.com/repo/ubuntu stable-bionic main" | tee /etc/apt/sources.list.d/mono-official-stable.list && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends mono-complete && \
    rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
ENV LANG 'en_US.UTF-8'
ENV LANGUAGE 'en_US:en'

RUN ln -s /usr/games/steamcmd /usr/bin/steamcmd

COPY config.json_base /config.json_base

ADD entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

RUN mkdir /steam

RUN steamcmd +quit

ARG DEBIAN_FRONTEND=

ENTRYPOINT ["/entrypoint.sh"]
