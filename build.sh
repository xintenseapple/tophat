#!/bin/bash

docker image rm -f tophat:base tophat:nfc_wrangler tophat:heap_miner

git pull && git submodule update

sudo python3 -m pip install --force-reinstall --break-system-packages ./

docker build -t tophat:base ./
docker build -t tophat:nfc_wrangler ./src/tophat/hats/nfc_wrangler
docker build -t tophat:heap_miner ./src/tophat/hats/heap_miner