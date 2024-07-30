PYTHON_CFLAGS := $(shell python3-config --cflags --embed)
PYTHON_LDFLAGS := $(shell python3-config --ldflags --embed)

nfc_wrangler: nfc_wrangler.c
	gcc -O0 $? $(PYTHON_CFLAGS) $(INCLUDES) -o $@ $(PYTHON_LDFLAGS)