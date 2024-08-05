#include <Python.h>

#include "tophat/api/common.h"

#pragma once

PyObject *create_print_command(const char *str) {
    PyObject *printer_module_pyobj = get_module("tophat.devices.printer");
    if (printer_module_pyobj == NULL) return NULL;

    PyObject *print_command_pyobj = PyObject_CallMethod(printer_module_pyobj, "PrintCommand", "(s)", str);
    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
    }
    Py_DECREF(printer_module_pyobj);
    return print_command_pyobj;
}