#include <Python.h>

#include "tophat/api/client.h"
#include "tophat/devices/printer.h"
#include "tophat/devices/neopixel.h"


int main() {
    Py_Initialize();

    PyGILState_STATE py_state = PyGILState_Ensure();

    PyObject *client_pyobj = get_client("/srv/tophat/test.socket");

    PyObject *print_command_pyobj = create_print_command("HELLO WORLD");
    PyObject *result = send_command(client_pyobj, 0x1, print_command_pyobj);

    if (result == NULL) {
        printf("Received None!\n");
    } else {
        printf("Received something else...\n");
        Py_DECREF(result);
    }

    Py_DECREF(client_pyobj);
    Py_DECREF(print_command_pyobj);

    PyGILState_Release(py_state);

    Py_Finalize();

    return 0;
}