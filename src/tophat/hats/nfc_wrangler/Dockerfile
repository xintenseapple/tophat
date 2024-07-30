FROM tophat:base

USER root
ADD src/ /root/nfc_wrangler
RUN cd /root/nfc_wrangler && make
RUN mv /root/nfc_wrangler/nfc_wrangler /home/hatman/nfc_wrangler
RUN chmod 611 /home/hatman/nfc_wrangler
RUN ln -s /home/hatman/nfc_wrangler /usr/bin/nfc_wrangler

USER hatman
