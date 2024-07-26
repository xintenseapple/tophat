#include <Python.h>

#include "tophat/api/common.h"

#pragma once

PyObject *create_color(const char red, const char green, const char blue) {
    return PyObject_Build("(B, B, B)", red, green, blue);
}

PyObject *create_solid_color_command(PyObject *color) {
    PyObject *neopixel_module_pyobj = get_module("tophat.devices.neopixel");
    PyObject *solid_color_command_pyobj = PyObject_CallMethod(neopixel_module_pyobj,
                                                              "SolidColorCommand",
                                                              "(O)",
                                                              color);
    Py_DECREF(neopixel_module_pyobj);
    return solid_color_command_pyobj;
}

PyObject *create_blink_command(const long duration, PyObject *color, const long frequency) {
    PyObject *neopixel_module_pyobj = get_module("tophat.devices.neopixel");
    PyObject *blink_command_pyobj = PyObject_CallMethod(neopixel_module_pyobj,
                                                        "BlinkCommand",
                                                        "(k, O, k)",
                                                        duration, color, frequency);
    Py_DECREF(neopixel_module_pyobj);
    return blink_command_pyobj;
}

PyObject *create_pulse_command(const unsigned long duration,
                               PyObject *color,
                               const unsigned long frequency,
                               const unsigned long blanks) {
    PyObject *neopixel_module_pyobj = get_module("tophat.devices.neopixel");
    PyObject *pulse_command_pyobj = PyObject_CallMethod(neopixel_module_pyobj,
                                                        "PulseCommand",
                                                        "(k, O, k, k)",
                                                        duration, color, frequency, blanks);
    Py_DECREF(neopixel_module_pyobj);
    return pulse_command_pyobj;
}

PyObject *create_rainbow_command(const unsigned long duration,
                                 const unsigned long frequency) {
    PyObject *neopixel_module_pyobj = get_module("tophat.devices.neopixel");
    PyObject *rainbow_command_pyobj = PyObject_CallMethod(neopixel_module_pyobj,
                                                        "RainbowCommand",
                                                        "(k, k)",
                                                        duration, frequency);
    Py_DECREF(neopixel_module_pyobj);
    return rainbow_command_pyobj;
}

PyObject *create_rainbow_wave_command(const unsigned long duration,
                                      const unsigned long frequency) {
    PyObject *neopixel_module_pyobj = get_module("tophat.devices.neopixel");
    PyObject *rainbow_wave_command_pyobj = PyObject_CallMethod(neopixel_module_pyobj,
                                                        "RainbowWaveCommand",
                                                        "(k, k)",
                                                        duration, frequency);
    Py_DECREF(neopixel_module_pyobj);
    return rainbow_wave_command_pyobj;
}