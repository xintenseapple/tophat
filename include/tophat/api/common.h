#include <Python.h>

#pragma once

PyObject *get_module(const char* module_name) {
    return PyImport_ImportModule(module_name);
}

PyObject *get_path(const char *path_str) {
    PyObject *pathlib_module_pyobj = get_module("pathlib");
    PyObject *Path_class_pyobj = PyObject_GetAttrString(pathlib_module_pyobj, "Path");
    return PyObject_CallFunction(Path_class_pyobj, "(s)", path_str);
}