FROM ubuntu:jammy

# Update
USER root
RUN apt update && \
    apt upgrade -qy && \
    apt autoremove -qy

# Install Python
USER root
RUN apt install -qy --no-install-recommends python3 python3-pip python3-dev
RUN python3 -m pip install --upgrade pip

# Create new user
RUN useradd --create-home --user-group --shell /bin/bash hatman

# Create volume for tophat socket
VOLUME /var/run/tophat/

# Add and install tophat Python package
RUN mkdir /home/hatman/tophat/
ADD pyproject.toml README.md requirements.txt src /home/hatman/tophat/
RUN python3 -m pip install /home/hatman/tophat/
RUN chown -R root:hatman /home/hatman/tophat/
RUN chmod -R 550 /home/hatman/tophat/

# Add includes
ADD include/tophat/ /usr/include/tophat/

USER hatman