cimport mp_vector as cv


cdef class terrain_point:
    cdef public cv.vector position
    cdef public cv.vector weights
    cdef public list neighbors
    cdef public str _str

cdef float relax(terrain_point tpt)



