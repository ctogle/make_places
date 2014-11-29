cimport mp_vector as cv



cdef class vertex:
    cdef public cv.vector position
    cdef public cv.vector normal
    cdef public cv.vector2d uv

cdef list vertices_from_data_c(list coords, list ncoords, list ucoords)
cpdef list vertices_from_data(list coords, list ncoords, list ucoords)







