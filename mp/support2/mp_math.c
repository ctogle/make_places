

#include <Python.h>

struct vector
{
    float x;
    float y;
    float z;
};

static PyMethodDef mp_mathMethods[] = {
    /* {"system",  spam_system, METH_VARARGS, */
    /* "Execute a shell command."}, */
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initmp_math(void)
{
      PyObject *m;

      m = Py_InitModule("mp_math", mp_mathMethods);
      if (m == NULL)
          return;
}


