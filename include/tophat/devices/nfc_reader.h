#include <Python.h>

#include "tophat/api/common.h"

#pragma once

PyObject *create_read_data_command(float timeout) {
    PyObject *nfc_reader_module_pyobj = get_module("tophat.devices.nfc_reader");
    if (nfc_reader_module_pyobj == NULL) return NULL;

    PyObject *read_data_command_pyobj = PyObject_CallMethod(nfc_reader_module_pyobj,
                                                            "ReadDataCommand",
                                                            "(f)",
                                                            timeout);
    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
    }
    Py_DECREF(nfc_reader_module_pyobj);
    return read_data_command_pyobj;
}
