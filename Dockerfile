FROM ubuntu:jammy

# Update
USER root
RUN apt update && \
    apt upgrade -qy && \
    apt autoremove -qy

# Install Python
USER root
RUN apt install -qy python3 python3-pip python3-dev
RUN python3 -m pip install --upgrade pip

# Create new user
RUN useradd --create-home --user-group --shell /bin/bash hatman

# Create volume for hatbox socket
VOLUME /var/run/hatbox.socket

# Add and install tophat Python package
USER hatman
RUN mkdir /home/hatman/tophat/
ADD pyproject.toml /home/hatman/tophat/pyproject.toml
ADD README.md /home/hatman/tophat/README.md
ADD requirements.txt /home/hatman/tophat/requirements.txt
ADD tophat/ /home/hatman/tophat/tophat/
RUN ls /home/hatman/tophat/
RUN python3 -m pip install /home/hatman/tophat/

USER root
RUN chown -R root:hatman /home/hatman/tophat/
RUN chmod -R 550 /home/hatman/tophat/

USER hatman
RUN cd ~

