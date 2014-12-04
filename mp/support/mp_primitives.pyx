import mp_utils as mpu
import mp_vector as cv
cimport mp_vector as cv

#from libc.math cimport sqrt

#import time
#import random as rm

stuff = 'hi'

cdef class vertex:
    def __cinit__(self,cv.vector position,cv.vector normal,cv.vector2d uv):
        self.position = position
        self.normal = normal
        self.uv = uv

    def __str__(self):
        strdata = [
            self.position.__str__(),
            self.normal.__str__(),
            self.uv.__str__()]
        strr = '\tvertex\n' + '\n\t'.join(strdata)
        return strr

cdef list vertices_from_data_c(list coords, list ncoords, list ucoords):
    cdef int ccnt = len(coords)
    cdef list vertices = []
    for vdx in range(ccnt):
        #newpos = cv.vector(*<list>coords[vdx])
        #newnorm = cv.vector(*<list>ncoords[vdx])
        #newuv = cv.vector2d(*<list>ucoords[vdx])
        newpos = <cv.vector>coords[vdx]
        newnorm = <cv.vector>ncoords[vdx]
        newuv = <cv.vector2d>ucoords[vdx]
        new = vertex(newpos,newnorm,newuv)
        vertices.append(new)
    return vertices

cpdef list vertices_from_data(list coords, list ncoords, list ucoords):
    cdef list new = vertices_from_data_c(coords,ncoords,ucoords)
    return new





cdef class face:
    cdef public list indices
    cdef public int material
    cdef public int phys_material

cdef class mesh:
    cdef public list vertices
    cdef public list faces

    def __init__(self):
        self.vertices = []
        self.faces = []
        self.materials = []

    def __str__(self):
        strr = '\tmesh\n' + '\n\t'.join([v.__str__() for v in self.vertices])
        return strr

    cpdef add_data(self, object data):
        datakeys = data.keys()

        #def default(key,defv):
        #    return data[key] if key in datakeys else defv

        #coords  = default( 'verts',[])
        #ncoords = default('nverts',[])
        #ucoords = default(   'uvs',[])
        #self.faces = kwargs['faces']

        #fcnt = len(self.faces)
        #zero = [0]*fcnt
        #self._default_('materials',['cubemat'],**kwargs)
        #self._default_('phys_materials',['/common/pmat/Stone'],**kwargs)
        #self._default_('phys_face_materials',zero,**kwargs)
        #self._default_('face_materials',zero[:],**kwargs)
        #self.face_materials = kwargs['face_materials']

    cpdef add_verts(self, list verts):
        self.vertices.extend(verts)




cpdef test():
    me = mesh()
    print 'mesh!'
    print me
    p1 = cv.vector(0,0,0)
    p2 = cv.vector(1,0,0)
    p3 = cv.vector(0,1,0)
    n1 = cv.vector(0,0,1)
    n2 = cv.vector(0,0,1)
    n3 = cv.vector(0,0,1)
    u1 = cv.vector2d(0,0)
    u2 = cv.vector2d(1,0)
    u3 = cv.vector2d(0,1)
    v1 = vertex(p1,n1,u1)
    v2 = vertex(p2,n2,u2)
    v3 = vertex(p3,n3,u3)
    me.vertices.extend([v1,v2,v3])
    print 'me again!'
    print me








