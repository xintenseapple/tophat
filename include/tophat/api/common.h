#include <Python.h>

#pragma once

PyObject *get_module(const char* module_name) {
    PyObject *module_pyobj = PyImport_ImportModule(module_name);
    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
    }
    return module_pyobj;
}

PyObject *get_path(const char *path_str) {
    PyObject *pathlib_module_pyobj = get_module("pathlib");
    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
    }
    if (pathlib_module_pyobj == NULL) return NULL;

    PyObject *Path_pyobj = PyObject_CallMethod(pathlib_module_pyobj, "Path", "(s)", path_str);

    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
    }
    Py_DECREF(pathlib_module_pyobj);
    return Path_pyobj;
}