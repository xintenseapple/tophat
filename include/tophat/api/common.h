#include <Python.h>

#pragma once

PyObject *get_module(const char* module_name) {
    PyObject *module_pyobj = PyImport_ImportModule(module_name);

    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
        return NULL;
    } else {
        return module_pyobj;
    }
}

PyObject *get_path(const char *path_str) {
    PyObject *pathlib_module_pyobj = get_module("pathlib");
    PyObject *Path_pyobj = PyObject_CallMethod(pathlib_module_pyobj, "Path", "(s)", path_str);
    Py_DECREF(pathlib_module_pyobj);

    if (PyErr_Occurred()) {
        PyErr_Print();
        PyErr_Clear();
        return NULL;
    } else {
        return Path_pyobj;
    }
}