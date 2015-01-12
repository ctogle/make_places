import make_places.scenegraph as sg
import make_places.fundamental as fu
import make_places.primitives as pr
#import make_places.walls as wa
#import make_places.floors as fl
#import make_places.stairs as st
import make_places.gritty as gritgeo
import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv

from math import cos
from math import sin
from math import tan
from math import sqrt
import numpy as np
import random as rm
import matplotlib.pyplot as plt

import pdb

def plot(verts,number = True,color = 'black',marker = None):
    fig = plt.gcf()
    ax = fig.gca()
    ax.grid(True)

    mark = 0
    for vdx in range(len(verts)):
        v = verts[vdx]
        mark = 1 if mark % 2 == 0 else 0
        altmark = '+' if mark else 'x'
        vmark = altmark if marker is None else marker
        vplt = v.plot_xy()
        x = [vplt[0][0]]
        y = [vplt[0][1]]
        label = str(vdx+1)
        plt.plot(x,y,markersize = 10,marker = vmark,color = color)
        if number:
            plt.annotate(label,xy = (x[0],y[0]),xytext = (-20, 20),
                textcoords = 'offset points', ha = 'right', va = 'bottom',
                #bbox = dict(boxstyle = 'round,pad=0.5',fc = 'yellow', alpha = 0.5),
                arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))
        
def rotate_pair(pair,ang):
    mp = cv.midpoint(*pair)
    cv.translate_coords(pair,mp.flip())
    cv.rotate_z_coords(pair,ang)
    cv.translate_coords(pair,mp.flip())

def extrude_edge(c1,c2,length,direction):
    c1c2n = direction.normalize().scale_u(length)
    c3 = c2.copy().translate(c1c2n)
    c4 = c1.copy().translate(c1c2n)
    return c3,c4

def extrude_edge_normal(c1,c2,length):
    c1c2 = cv.v1_v2(c1,c2)
    c1c2n = cv.cross(cv.zhat,c1c2)
    return extrude_edge(c1,c2,length,c1c2n)

def point_line(s,e,l,n):
    line = [s.copy()]
    tn = cv.v1_v2(s,e).normalize()
    tn.scale_u(float(l)/n)
    for x in range(n):
        line.append(line[-1].copy().translate(tn))
    return line

def point_ring(r,n):
    st = cv.zero().translate_x(r)
    alpha = fu.PI*(2.0/n)
    points = []
    for x in range(n):
        points.append(st.copy().rotate_z(x*alpha))
    return points

def normal(c1,c2,c3):
    c1c2 = cv.v1_v2(c1,c2).normalize()
    c2c3 = cv.v1_v2(c2,c3).normalize()
    cn = c1c2.cross(c2c3).normalize()
    return cn

blueprint_count = 0
class blueprint(fu.base):
    # a blueprint is a proxy object to design 
    #  and then build a component of a city
    # it has a build method which returns nodes
    # it contains vertex data from which to build a mesh

    # provide an xml filename unique to this blueprint
    def _xmlfilename(self):
        xfile = '.'.join(['xblueprint',str(self.bp_index),'mesh','xml'])
        return xfile

    # provide the index of a material
    def _lookup_mat(self,m):
        if m is None: m = 0
        else:
            if m in self.mats:
                m = self.mats.index(m)
            else:
                self.mats.append(m)
                m = len(self.mats) - 1
        return m

    # provide the index of a physics material
    def _lookup_pmat(self,pm):
        if pm is None: pm = 0
        else:
            if pm in self.pmats:
                pm = self.pmats.index(pm)
            else:
                self.pmats.append(pm)
                pm = len(self.pmats) - 1
        return pm

    def _assign_material(self,m,rng):
        m = self._lookup_mat(m)
        for dx in rng:
            self.face_mats[dx] = m

    def _reset_data(self):
        self.pcoords = []
        self.ncoords = []
        self.ucoords = []
        self.faces = []
        self.face_mats = []
        self.face_pmats = []

    def _build(self):pass

    def _rebuild(self,**opts):
        bflag = False
        for oke in opts.keys():
            oval = opts[oke]
            if not self.__dict__[oke] == oval:
                bflag = True
                self.__dict__[oke] = oval
        if bflag:
            self._reset_data()
            self._build()

    def __init__(self):
        global blueprint_count
        blueprint_count += 1
        self.bp_index = blueprint_count

        self.pcoords = []
        self.ncoords = []
        self.ucoords = []
        self.faces = []
        self.face_mats = []
        self.face_pmats = []

        self.mats = ['cubemat']
        self.pmats = ['/common/pmat/Stone']

    def _trifan(self,apex,blade,ns = None,us = None,m = None,pm = None):
        tcnt = len(blade) - 1
        for trdx in range(tcnt):
            c2dx = trdx
            c3dx = trdx+1
            c1 = apex.copy()
            c2 = blade[c2dx].copy()
            c3 = blade[c3dx].copy()
            self._triangle(c1,c2,c3,ns,us,m,pm)

    # given two loops of equal length, bridge with quads
    def _tripie(self,loop,ns = None,us = None,m = None,pm = None):
        lcom = cv.center_of_mass(loop)
        tcnt = len(loop)
        for trdx in range(tcnt):
            c2dx = trdx
            c3dx = trdx+1
            if c3dx == tcnt: c3dx = 0
            c1 = lcom.copy()
            c2 = loop[c2dx].copy()
            c3 = loop[c3dx].copy()
            self._triangle(c1,c2,c3,ns,us,m,pm)

    # given two loops of equal length, bridge with quads
    def _bridge(self,loop1,loop2,ns = None,us = None,m = None,pm = None):
        if not len(loop1) == len(loop2): raise ValueError
        lcnt = len(loop1)
        for ldx in range(1,lcnt):
            v1 = loop1[ldx-1]
            v2 = loop2[ldx-1]
            v3 = loop2[ldx]
            v4 = loop1[ldx]
            self._quad(v1,v2,v3,v4,ns,us,m,pm)

    # given two loops of possibly nonequal length, bridge with quads/tris
    def _bridge_asymmetric(self,loop1,loop2,ns = None,us = None,m = None,pm = None):

        pdb.set_trace()

        if not len(loop1) == len(loop2): raise ValueError
        lcnt = len(loop1)
        for ldx in range(1,lcnt):
            v1 = loop1[ldx-1]
            v2 = loop2[ldx-1]
            v3 = loop2[ldx]
            v4 = loop1[ldx]
            self._quad(v1,v2,v3,v4,ns,us,m,pm)

    # given a line of points make n faces between angles a1 and a2
    def _revolve_z(self,loop,a1,a2,n,ns = None,us = None,m = None,pm = None):
        rotstep = (a2-a1)/float(n)
        for step in range(n):
            ta1 = a1+step*rotstep
            ta2 = a1+(step+1)*rotstep
            loop1 = [p.copy().rotate_z(ta1) for p in loop]
            loop2 = [p.copy().rotate_z(ta2) for p in loop]
            self._bridge(loop1,loop2,ns = ns,us = us,m = m,pm = pm)

    # given a curve of points make faces to extrude loop along the curve
    def _extrude(self,loop,curve,ns = None,us = None,m = None,pm = None):
        tailloop = [l.copy() for l in loop]
        n = len(curve)
        for step in range(1,n):
            tn = cv.v1_v2(curve[step-1],curve[step])
            tiploop = [l.copy().translate(tn) for l in tailloop]
            # i want to rotate tiploop according to tangents - need quat
            # rotation...
            self._bridge(tailloop,tiploop)
            tailloop = [l.copy() for l in tiploop]

    # given four points, add two new triangle faces
    def _quad(self,v1,v2,v3,v4,ns = None,us = None,m = None,pm = None):
        if us is None:
            us1 = [cv.vector2d(0,1),cv.vector2d(0,0),cv.vector2d(1,0)]
            us2 = [cv.vector2d(0,1),cv.vector2d(1,0),cv.vector2d(1,1)]
        else:
            us1 = [us[0],us[1],us[2]]
            us2 = [us[0],us[2],us[3]]
        if ns is None:
            ns1 = None
            ns2 = None
        else:
            ns1 = [ns[0],ns[1],ns[2]]
            ns2 = [ns[0],ns[2],ns[3]]
        self._triangle(v1,v2,v3,ns = ns1,us = us1,m = m,pm = pm)
        self._triangle(v1,v3,v4,ns = ns2,us = us2,m = m,pm = pm)

    # given three points, add new triangle face
    def _triangle(self,v1,v2,v3,ns = None,us = None,m = None,pm = None):
        nps = [v1.copy(),v2.copy(),v3.copy()]
        if ns is None:
            n = normal(*nps)
            nns = [n,n,n]
        else: nss = ns
        if us is None:
            nus = [cv.vector2d(0,1),cv.vector2d(0,0),cv.vector2d(1,0)]
        else: nus = us
        self._add_vdata(nps,nns,nus)

        foffset = len(self.pcoords) - len(nps)
        nfs = mpu.offset_faces([[0,1,2]],foffset)

        m = self._lookup_mat(m)
        pm = self._lookup_pmat(pm)

        nfms = [m]
        nfpms = [pm]

        self._add_fdata(nfs,nfms,nfpms)

    def _add_vdata(self,ps,ns,us):
        self.pcoords.extend(ps)
        self.ncoords.extend(ns)
        self.ucoords.extend(us)

    def _add_fdata(self,fs,fms,fpms):
        self.faces.extend(fs)
        self.face_mats.extend(fms)
        self.face_pmats.extend(fpms)

    def _primitive_from_slice(self,dslice = slice(None),
            xmlfile = None,hlod = False,ilod = False):
        if xmlfile is None: xmlfile = self._xmlfilename()
        vs = self.pcoords[dslice]
        ns = self.ncoords[dslice]
        us = self.ucoords[dslice]
        fs = self.faces[dslice]
        fms = self.face_mats[dslice]
        fpms = self.face_pmats[dslice]
        pwargs = {
            'verts':[v.copy() for v in vs], 
            'nverts':[n.copy() for n in ns], 
            'uvs':[u.copy() for u in us], 
            'faces':[f[:] for f in fs], 
            'materials' : self.mats[:], 
            'face_materials' : fms[:], 
            'phys_materials' : self.pmats[:], 
            'phys_face_materials' : fpms[:], 
            'xmlfilename' : xmlfile, 

            'force_normal_calc' : False, 
            'prevent_normal_calc' : True, 
            'smooth_normals' : False, 

            'is_lod' : ilod, 
            'has_lod' : hlod,
                }
        mesh = pr.arbitrary_primitive(**pwargs)
        #mesh._scale_uvs_ = True
        return mesh
        






    def tripie(self,vs,nvs,nus,nfs,fms,pfms,convex):
        convex.insert(0,cv.center_of_mass(convex))
        tcnt = len(convex) - 1
        for trdx in range(tcnt):
            c2dx = trdx+1
            c3dx = trdx+2
            if c3dx == tcnt + 1: c3dx = 1
            c1 = convex[0].copy()
            c2 = convex[c2dx].copy()
            c3 = convex[c3dx].copy()
            self.add_tri(vs,nvs,nus,nfs,fms,pfms,c1,c2,c3)
        #plot(convex)
        #plt.show()

    def quadrafy(convex):
        pdb.set_trace()

    def bridge(self,vs,nvs,nus,nfs,fms,pfms,loop1,loop2):
        if not len(loop1) == len(loop2): raise ValueError
        lcnt = len(loop1)
        for ldx in range(1,lcnt):
            v1 = loop1[ldx-1].copy()
            v2 = loop2[ldx-1].copy()
            v3 = loop2[ldx].copy()
            v4 = loop1[ldx].copy()
            self.add_quad(vs,nvs,nus,nfs,fms,pfms,v1,v2,v3,v4)

    def add_tri(self,vs,nvs,nus,nfs,fms,pfms,v1,v2,v3):
        foffset = len(vs)
        n = cv.v1_v2(v1,v2).cross(cv.v1_v2(v2,v3)).normalize()
        vs.extend([v1,v2,v3])       
        nvs.extend([n,n,n])
        nus.extend([cv.vector2d(0,1),
            cv.vector2d(0,0),cv.vector2d(1,0)])
        uvlength = cv.distance(v2,v3)
        #cv.scale_coords2d(nus,cv.vector2d(uvlength,self.lane_width))
        #cv.translate_coords2d(nus,self.uvguide)
        nfs.extend(mpu.offset_faces([[0,1,2]],foffset))
        fms.extend([0])
        pfms.extend([0])

    def add_quad(self,vs,nvs,nus,nfs,fms,pfms,v1,v2,v3,v4):
        foffset = len(vs)
        n = cv.v1_v2(v1,v2).cross(cv.v1_v2(v2,v3)).normalize()
        vs.extend([v1,v2,v3,v4])       
        nvs.extend([n,n,n,n])
        nus.extend([cv.vector2d(0,1),cv.vector2d(0,0),
                  cv.vector2d(1,0),cv.vector2d(1,1)])
        uvlength = cv.distance(v2,v3)
        #cv.scale_coords2d(nus,cv.vector2d(uvlength,self.lane_width))
        #cv.translate_coords2d(nus,self.uvguide)
        nfs.extend(mpu.offset_faces([[0,1,3],[1,2,3]],foffset))
        fms.extend([0,0])
        pfms.extend([0,0])

    def quaddata(self,data_methods = []):
        vs = []
        nvs = []
        nus = []
        nfs = []
        fms = []
        pfms = []
        for dm in data_methods:
            dm(vs,nvs,nus,nfs,fms,pfms)
        return vs,nvs,nus,nfs,fms,pfms

    def build(self,xmlfile,ilod,hlod):
        vdat = self.quaddata()
        newverts,newnorml,newuvs,newfaces,fmats,pfmats = vdat
        pwargs = {
            'verts' : newverts, 
            'nverts' : newnorml, 
            'uvs' : newuvs, 
            'faces' : newfaces, 
            'materials' : self.materials[:], 
            'face_materials' : fmats, 
            'phys_materials' : self.phys_materials[:], 
            'phys_face_materials' : pfmats, 
            'xmlfilename' : xmlfile, 
            'force_normal_calc' : True, 
            'prevent_normal_calc' : False, 
            'smooth_normals' : False, 
            'is_lod' : ilod, 
            'has_lod' : hlod,
                }
        mesh = pr.arbitrary_primitive(**pwargs)
        return mesh

    def build_lod(self):
        scubes = [ucube()]
        return scubes



class cylinder(blueprint):

    def __init__(self,r = 10,h = 20):
        blueprint.__init__(self)
        self.r = r
        self.h = h

    def _build(self):
        r,h = self.r,self.h
        bottom = point_ring(r,8)
        top = [bc.copy().translate_z(h) for bc in bottom]
        self._tripie(top)
        top.reverse()
        bottom.reverse()
        self._tripie(bottom,m = 'grass')
        bottom.append(bottom[0])
        top.append(top[0])
        self._bridge(bottom,top,m = 'metal')

class cube(blueprint):

    def __init__(self,l = 1,w = 1,h = 1,a = 0,m = 'cubemat'):
        blueprint.__init__(self)
        self.l = l
        self.w = w
        self.h = h
        self.a = a
        self.m = m

    def _build(self):
        l,w,h,a = self.l,self.w,self.h,self.a
        bcorners = mpu.make_corners(cv.zero(),l,w,fu.to_deg(a))
        tcorners = [bc.copy().translate_z(h) for bc in bcorners]
        bcorners.reverse()
        self._quad(*bcorners,m = self.m)
        self._quad(*tcorners,m = self.m)
        tcorners.reverse()
        bcorners.append(bcorners[0])
        tcorners.append(tcorners[0])
        self._bridge(bcorners,tcorners,m = self.m)

    def _primitive_from_slice(self,*args,**kwargs):
        prim = blueprint._primitive_from_slice(self,*args,**kwargs)
        prim._scale_uvs_ = True
        return prim

cube_factory = cube()
cube_factory._build()
def ucube(**opts):
    cube_factory._rebuild(**opts)
    return cube_factory._primitive_from_slice()







def test_trifan():
    bpt = blueprint()
    apex = cv.one()
    blade = [apex.copy().translate_x(5)]
    blade.append(blade[-1].copy().translate_y(3))
    blade.append(blade[-1].copy().translate_x(-2))

    bpt._trifan(apex,blade)

    bprim = bpt._primitive_from_slice()
    gritgeo.reset_world_scripts()
    gritgeo.create_primitive(bprim)
    gritgeo.output_world_scripts()

def test_extrude():
    bpt = blueprint()
    pentb = polygon(16)
    pentb.append(pentb[0])
    pentb.reverse()

    curve = [cv.zero()]
    cstep = cv.vector(1,2,6)
    curve.append(curve[-1].copy().translate(cstep))
    cstep = cv.vector(3,2,5)
    curve.append(curve[-1].copy().translate(cstep))
    cstep = cv.vector(1,-1,4)
    curve.append(curve[-1].copy().translate(cstep))

    bpt._extrude(pentb,curve)

    bprim = bpt._primitive_from_slice()
    gritgeo.reset_world_scripts()
    gritgeo.create_primitive(bprim)
    gritgeo.output_world_scripts()

def test_revolve():
    bpt = blueprint()
    pentb = polygon(8)
    cv.translate_coords_x(pentb,5.0)
    cv.rotate_x_coords(pentb,fu.to_rad(90))
    pentb.append(pentb[0])

    bpt._revolve_z(pentb,fu.to_rad(30),fu.to_rad(135),16)

    bprim = bpt._primitive_from_slice()
    gritgeo.reset_world_scripts()
    gritgeo.create_primitive(bprim)
    gritgeo.output_world_scripts()



class floors(blueprint):

    def __init__(self):
        blueprint.__init__(self)

    def _build(self):
        bcorners = mpu.make_corners(cv.zero(),100,100,fu.to_deg(30))
        tcorners = [bc.copy().translate_z(10) for bc in bcorners]
        tcorners.reverse()
        for x in range(3):
            self._quad(*bcorners)
            self._quad(*tcorners)
            thisbump = 12
            cv.translate_coords_z(bcorners,thisbump)
            cv.translate_coords_z(tcorners,thisbump)
        #return self._primitive_from_slice()
      










def test():
    bpt = blueprint()
    pentb = polygon(8)
    pentt = [p.copy().translate_z(5) for p in pentb]
    pentb.reverse()
    bpt._tripie(pentt)
    bpt._tripie(pentb)
    pentb.reverse()
    pentb.append(pentb[0])
    pentt.append(pentt[0])
    bpt._bridge(pentt,pentb)
    bprim = bpt._primitive_from_slice()
    bprim.scale(cv.vector(2,2,10))
    #bpp = cube()
    #bpp = cylinder()
    #bpp._build()
    gritgeo.reset_world_scripts()
    gritgeo.create_primitive(bprim)
    gritgeo.output_world_scripts()

def speed1():
    gritgeo.reset_world_scripts()
    c = cube()
    c._build()
    for z in range(10000):
        #pc = cube()._build()
        pc = c._primitive_from_slice()
        #pc = pr.ucube()

        pc.translate_z(2*z)
        gritgeo.create_primitive(pc)
    gritgeo.output_world_scripts()
















def polygon(sides):
    angle = 360.0/sides
    turns = [x*angle for x in range(sides)]
    poly = [cv.zero()]
    current_angle = 0.0
    for si in range(sides):
        l,t = 1.0,turns[si]
        current_angle = t
        dx = l*cos(fu.to_rad(current_angle))
        dy = l*sin(fu.to_rad(current_angle))
        new = poly[-1].copy().translate_x(dx).translate_y(dy)
        poly.append(new)
    poly.pop()
    cv.translate_coords(poly,cv.center_of_mass(poly).flip())
    return poly

def poly_test():
    for x in range(5):
        poly = polygon(x+3)
        plot(poly)
        plt.show()

        

# walk_line makes an xy outline of a building
def walk_line(corners):
    c1,c2,c3,c4 = corners
    l = c2.x - c1.x
    w = c4.y - c1.y
    steps = rm.choice([4,5,6,8])
    angle = 360.0/steps
    turns = [x*angle for x in range(steps)]
    stepl = 0.8*min([l,w])
    lengs = [stepl]*steps
    start = corners[0].copy()
    start.translate(cv.vector(l/10.0,w/10.0,0))
    outline = [start]
    newz = start.z
    current_angle = 0.0
    for dex in range(steps-1):
        l,t = lengs[dex],turns[dex]
        current_angle = t
        dx = l*cos(fu.to_rad(current_angle))
        dy = l*sin(fu.to_rad(current_angle))
        #quadr = fu.quadrant(fu.to_rad(current_angle))
        #dxsign = 1.0 if quadr in [1,4] else -1.0
        #dysign = 1.0 if quadr in [1,2] else -1.0
        dxsign = 1.0
        dysign = 1.0
        last = outline[-1]
        newx = last.x + dx*dxsign
        newy = last.y + dy*dysign
        new = cv.vector(newx,newy,newz)
        outline.append(new)
    return outline
    #return circumscribe_box(corners,outline)

def outline_test(center):
    c1 = cv.vector(-10,-10,0)
    c2 = cv.vector( 10,-10,0)
    c3 = cv.vector( 10, 10,0)
    c4 = cv.vector(-10, 10,0)
    corners = [c1,c2,c3,c4]
    cv.translate_coords(corners,center)
    outy = walk_line(corners)
    return outy









