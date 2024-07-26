#include <Python.h>

#include "tophat/api/common.h"

#pragma once

PyObject *create_read_data_command(void) {
    PyObject *nfc_reader_module_pyobj = get_module("tophat.devices.nfc_reader");
    PyObject *read_data_command_pyobj = PyObject_CallMethod(nfc_reader_module_pyobj,
                                                            "ReadDataCommand",
                                                            "(O)",
                                                            Py_None);
    Py_DECREF(nfc_reader_module_pyobj);
    return read_data_command_pyobj;
}
