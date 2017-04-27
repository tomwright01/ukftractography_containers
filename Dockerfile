From ubuntu:xenial
Label maintainer "Thomas.Wright"

RUN apt-get update \
  && apt-get install --no-install-recommends -y \
    tar \
    wget \
    vim-tiny \
    coreutils \
    build-essential \
    cmake \
    git \
    ca-certificates \
  && rm -rf /var/lib/apt/lists

# configure git
RUN git config --global url."https://".insteadOf git://

# Get ukftractography
WORKDIR /opt
RUN git clone -b local_build https://github.com/tomwright01/ukftractography.git
WORKDIR /opt/ukftractography
RUN mkdir build
WORKDIR /opt/ukftractography/build
RUN cmake ..
RUN make
