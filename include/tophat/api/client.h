#include <Python.h>

#include "tophat/api/common.h"

#pragma once

#define DEFAULT_SOCKET_PATH "/var/run/tophat/tophat.socket"

PyObject *get_client(const char *socket_path_str) {
    PyObject *client_module_pyobj = get_module("tophat.api.client");
    if (client_module_pyobj == NULL) return NULL;

    PyObject *socket_Path_pyobj = get_path(socket_path_str);
    if (socket_Path_pyobj == NULL) {
        Py_DECREF(client_module_pyobj);
        return NULL;
    }

    PyObject *client_pyobj = PyObject_CallMethod(client_module_pyobj,
                                                 "TopHatClient",
                                                 "(O)",
                                                 socket_Path_pyobj);
    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
    }
    Py_DECREF(socket_Path_pyobj);
    Py_DECREF(client_module_pyobj);
    return client_pyobj;
}

PyObject *send_command(PyObject *client_pyobj, const char *device_name, PyObject *command) {
    PyObject *result = PyObject_CallMethod(client_pyobj,
                                           "send_command",
                                           "(s, O)",
                                           device_name, command);

    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
    }
    return result;
}