#!/bin/bash

python3 -m tophat.run_server &> tophat_server.log &

sudo python3 -m tophat.devices.neopixel.server 12 38 &> neopixel_server.log &

sleep 2

docker run -v /srv/tophat/tophat.socket:/var/run/tophat/tophat.socket tophat:nfc_wrangler &> nfc_wrangler.log &