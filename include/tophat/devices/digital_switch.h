#include <Python.h>

#include "tophat/api/common.h"

#pragma once

PyObject *create_enable_command() {
    PyObject *digital_switch_module_pyobj = get_module("tophat.devices.digital_switch");
    PyObject *enable_command_pyobj = PyObject_CallMethod(digital_switch_module_pyobj,
                                                         "EnableCommand",
                                                         "()");
    Py_DECREF(digital_switch_module_pyobj);
    return enable_command_pyobj;
}

PyObject *create_disable_command() {
    PyObject *digital_switch_module_pyobj = get_module("tophat.devices.digital_switch");
    PyObject *disable_command_pyobj = PyObject_CallMethod(digital_switch_module_pyobj,
                                                          "DisableCommand",
                                                          "()");
    Py_DECREF(digital_switch_module_pyobj);
    return disable_command_pyobj;
}

PyObject *create_toggle_command() {
    PyObject *digital_switch_module_pyobj = get_module("tophat.devices.digital_switch");
    PyObject *toggle_command_pyobj = PyObject_CallMethod(digital_switch_module_pyobj,
                                                         "ToggleCommand",
                                                         "()");
    Py_DECREF(digital_switch_module_pyobj);
    return toggle_command_pyobj;
}