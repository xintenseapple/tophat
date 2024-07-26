#include <Python.h>

#include "tophat/api/common.h"

#pragma once

PyObject *create_print_command(const char *str) {
    PyObject *printer_module_pyobj = get_module("tophat.devices.printer");
    PyObject *print_command_pyobj = PyObject_CallMethod(printer_module_pyobj, "PrintCommand", "(s)", str);
    Py_DECREF(printer_module_pyobj);
    return print_command_pyobj;
}