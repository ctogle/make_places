import make_places.core.fundamental as fu
import make_places.core.scenegraph as sg
import make_places.core.primitives as pr
import make_places.core.blueprints as mbp

import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv

import pdb

class portal(mbp.blueprint):

    def __init__(self,z = 1.0,w = 0.5,h = 2.0,gap = None,wall = None):
        mbp.blueprint.__init__(self)
        self.z = z
        self.w = w
        self.h = h
        self.gap = gap
        self.wall = wall

    def _build(self):
        w,h,z,wg,wl = self.w,self.h,self.z,self.gap,self.wall
        if wl:wh = wl.h
        else:wh = z+h+1
        wnorm = wl.wnorm.copy()

        hh = z
        bh1,bh2 = wg[0].copy(),wg[1].copy()
        if hh > 0.0:self._build_header(bh1,bh2,wnorm,hh)

        hh = wl.h - z - h
        th1,th2 = wg[0].copy(),wg[1].copy()
        th1.translate_z(z+h)
        th2.translate_z(z+h)
        if hh > 0.0:self._build_header(th1,th2,wnorm,hh)

        bh1.translate_z(z)
        bh2.translate_z(z)
        wloop = [bh1,bh2,th2,th1]
        self._build_frame(wloop,wnorm)

    def _build_frame(self,floop,wnorm):
        l1 = [f.copy() for f in floop]
        l2 = [f.copy() for f in floop]
        [l.translate(wnorm) for l in l1]
        wnorm.flip()
        [l.translate(wnorm) for l in l2]
        l2.reverse()
        self._quad(*l1,m = 'glass')
        self._quad(*l2,m = 'glass')

    def _build_header(self,v1,v2,wnorm,h):
        b1 = v1.copy().translate(wnorm.flip())
        b2 = v2.copy().translate(wnorm)
        b3 = v2.copy().translate(wnorm.flip())
        b4 = v1.copy().translate(wnorm)
        t1 = b1.copy().translate_z(h)
        t2 = b2.copy().translate_z(h)
        t3 = b3.copy().translate_z(h)
        t4 = b4.copy().translate_z(h)

        bs = [b1,b2,b3,b4,b1]
        ts = [t1,t2,t3,t4,t1]
        nfs = self._bridge(bs,ts,m = self.wall.m)
        #nfs = self._bridge(ts,bs,m = self.wall.m)
        #self._project_uv_flat(nfs)

class door(portal):
    def __init__(self,z = 1.0,w = 0.5,h = 2.0,
            m = 'cement1',gap = None,wall = None):
        portal.__init__(self,z,w,h,gap,wall)
        self.m = m

    def _build_frame(self,floop,wnorm):
        framemat = self.m
        mbp.inflate(floop,-0.05)
        wnorm.scale_u(1.25)
        l1 = [f.copy() for f in floop]
        l2 = [f.copy() for f in floop]
        [l.translate(wnorm) for l in l1]
        wnorm.flip()
        [l.translate(wnorm) for l in l2]
        l3 = [l.copy() for l in l2]
        mbp.inflate(l3,0.2)
        l4 = [l.copy() for l in l1]
        mbp.inflate(l4,0.2)
        l1.append(l1[0].copy())
        l2.append(l2[0].copy())
        l3.append(l3[0].copy())
        l4.append(l4[0].copy())
        nfs = []
        nfs.extend(self._bridge(l2,l1,m = framemat))
        nfs.extend(self._bridge(l3,l2,m = framemat))
        nfs.extend(self._bridge(l1,l4,m = framemat))
        nfs.extend(self._bridge(l4,l3,m = framemat))
        #self._project_uv_flat(nfs)
        #self._flip_faces(nfs)

class window(portal):
    def __init__(self,z = 1.0,w = 0.5,h = 2.0,
            m = 'cement1',gap = None,wall = None):
        portal.__init__(self,z,w,h,gap,wall)
        self.m = m

    def _build_frame(self,floop,wnorm):
        m = self.m
        mbp.inflate(floop,-0.05)
        #wnorm.scale_u(2.0)
        wnorm.scale_u(1.25)
        l1 = [f.copy() for f in floop]
        l2 = [f.copy() for f in floop]
        #l1.append(l1[0].copy())
        #l2.append(l2[0].copy())
        [l.translate(wnorm) for l in l1]
        wnorm.flip()
        [l.translate(wnorm) for l in l2]
        l3 = [l.copy() for l in l2]
        mbp.inflate(l3,0.2)
        l4 = [l.copy() for l in l1]
        mbp.inflate(l4,0.2)
        l1.append(l1[0].copy())
        l2.append(l2[0].copy())
        l3.append(l3[0].copy())
        l4.append(l4[0].copy())
        nfs = []
        nfs.extend(self._bridge(l2,l1,m = m))
        nfs.extend(self._bridge(l3,l2,m = m))
        nfs.extend(self._bridge(l1,l4,m = m))
        nfs.extend(self._bridge(l4,l3,m = m))
        #self._project_uv_flat(nfs)
        #self._flip_faces(nfs)

#portal_factory = portal()
#portal_factory._build()
def build_portal(**opts):
    portal_factory = portal(**opts)
    portal_factory._build()
    #portal_factory._rebuild(**opts)
    return portal_factory._primitive_from_slice()






