#include <Python.h>

#include "tophat/api/common.h"

#pragma once

PyObject *get_client(const char *socket_path_str) {
    PyObject *client_module_pyobj = get_module("tophat.api.client");
    PyObject *socket_Path_pyobj = get_path(socket_path_str);

    PyObject *client_pyobj = PyObject_CallMethod(client_module_pyobj,
                                                 "TopHatClient",
                                                 "(O)",
                                                 socket_Path_pyobj);

    Py_DECREF(socket_Path_pyobj);
    Py_DECREF(client_module_pyobj);

    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
        return NULL;
    } else {
        return client_pyobj;
    }
}

PyObject *send_command(PyObject *client_pyobj, const uint64_t device_id, PyObject *command) {
    PyObject *result = PyObject_CallMethod(client_pyobj,
                                           "send_command",
                                           "(L, O)",
                                           device_id, command);

    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
        return NULL;
    } else {
        return result;
    }


}