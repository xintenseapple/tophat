PYTHON_CFLAGS := $(shell python3-config --cflags --embed)
PYTHON_LDFLAGS := $(shell python3-config --ldflags --embed)
INCLUDES = -I../../../include/

nfc_wrangler: src/nfc_wrangler.c
	gcc -O0 src/nfc_wrangler.c $(PYTHON_CFLAGS) $(INCLUDES) -o nfc_wrangler $(PYTHON_LDFLAGS)