#include <Python.h>

#include "tophat/api/common.h"

#pragma once

PyObject *create_enable_command() {
    PyObject *digital_switch_module_pyobj = get_module("tophat.devices.digital_switch");
    if (digital_switch_module_pyobj == NULL) return NULL;

    PyObject *enable_command_pyobj = PyObject_CallMethod(digital_switch_module_pyobj,
                                                         "EnableCommand",
                                                         "()");
    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
    }
    Py_DECREF(digital_switch_module_pyobj);
    return enable_command_pyobj;
}

PyObject *create_disable_command() {
    PyObject *digital_switch_module_pyobj = get_module("tophat.devices.digital_switch");
    if (digital_switch_module_pyobj == NULL) return NULL;

    PyObject *disable_command_pyobj = PyObject_CallMethod(digital_switch_module_pyobj,
                                                          "DisableCommand",
                                                          "()");
    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
    }
    Py_DECREF(digital_switch_module_pyobj);
    return disable_command_pyobj;
}

PyObject *create_toggle_command() {
    PyObject *digital_switch_module_pyobj = get_module("tophat.devices.digital_switch");
    if (digital_switch_module_pyobj == NULL) return NULL;

    PyObject *toggle_command_pyobj = PyObject_CallMethod(digital_switch_module_pyobj,
                                                         "ToggleCommand",
                                                         "()");
    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
    }
    Py_DECREF(digital_switch_module_pyobj);
    return toggle_command_pyobj;
}