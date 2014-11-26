

stuff = 'hi'

cdef class vector:
    cdef public float x    
    cdef public float y
    cdef public float z
    #cdef float x    
    #cdef float y
    #cdef float z
    cpdef scale(self, vector sv)
    cpdef translate(self, vector sv)
    cpdef normalize(self)
    cpdef float magnitude(self)
    cpdef list to_list(self)



