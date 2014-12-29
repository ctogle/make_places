




import mp_vector as cv
import mp_utils as mpu
import mp_bboxes as mpbb
import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.scenegraph as sg
import make_places.blueprints as mbp

import make_places.gritty as gritgeo

import matplotlib.pyplot as plt
import numpy as np
import random as rm
from math import sqrt
import time
import pdb




def rotate_pair(pair,ang):
            mp = cv.midpoint(*pair)
            cv.translate_coords(pair,mp.flip())
            cv.rotate_z_coords(pair,ang)
            cv.translate_coords(pair,mp.flip())

segment_number = 0
class segment(mbp.blueprint):
    def get_segment_number(self):
        global segment_number
        num = str(segment_number)
        segment_number += 1
        return num

    #def __init__(self,p1,p2,sp1,sp2,a1,a2,rwidth,swwidth,uvguide):
    def __init__(self,p1,p2,a1,a2,rwidth,swwidth,uvguide):
        #self.swalkstart = sp1
        #self.swalkend = sp2

        self.road_width = rwidth
        self.sidewalk_width = swwidth

        self.start = p1
        self.end = p2
        self.angle1 = a1
        self.angle2 = a2
        self.uvguide = uvguide
        tangent = cv.v1_v2(self.start,self.end)
        self.length = tangent.magnitude()
        self.tangent = tangent.normalize()
        self.normal = self.tangent.copy().xy().rotate_z(fu.to_rad(90)).normalize()

    def build_sidewalk(self):
        trans = self.normal.copy().scale_u(self.sidewalk_width/2.0)
        v1 = self.swalkstart.copy().translate(trans)
        v2 = self.swalkstart.copy().translate(trans.flip())
        v3 = self.swalkend.copy().translate(trans)
        v4 = self.swalkend.copy().translate(trans.flip())
        cv.translate_coords([v1,v2,v3,v4],cv.vector(0,0,1))
        rotate_pair([v1,v2],-1*self.angle1)
        rotate_pair([v3,v4],self.angle2)
        n = cv.v1_v2(v1,v2).cross(cv.v1_v2(v2,v3)).normalize()
        v5 = v2.copy()
        v6 = v2.copy().translate_z(-1)
        v7 = v3.copy().translate_z(-1)
        v8 = v3.copy()
        sn = cv.v1_v2(v6,v7).xy().rotate_z(fu.to_rad(-90)).normalize()

        vs = [v1,v2,v3,v4,v5,v6,v7,v8]
        nvs = [n,n,n,n,sn,sn,sn,sn]

        #sidevs = [v5,v6,v7,v8]
        #sidenvs = [sn,sn,sn,sn]
        #topvs = [v1,v2,v3,v4]
        #cv.translate_coords(topvs,cv.vector(0,0,1))
        #topnvs = [n,n,n,n]
        #nus = [cv.vector2d(0,1),cv.vector2d(0,0),
        #      cv.vector2d(1,0),cv.vector2d(1,1)]

        nus = [cv.vector2d(0,1),cv.vector2d(0,0),
                cv.vector2d(1,0),cv.vector2d(1,1), 
                cv.vector2d(0,1),cv.vector2d(0,0),
                cv.vector2d(1,0),cv.vector2d(1,1)]
        cv.scale_coords2d(nus,cv.vector2d(self.length,self.sidewalk_width))
        cv.translate_coords2d(nus,self.uvguide)
        nfs = [[0,1,3],[1,2,3],[4,5,7],[5,6,7]]
        #nfs = [[0,1,5],[1,4,5],[1,2,3],[3,4,1]]

        ms = ['cubemat']
        pms = ['/common/pmat/Stone']
        fms = [0,0,0,0]
        pfms = [0,0,0,0]

        #vs = topvs
        #nvs = topnvs
        #vs.extend(sidevs)
        #nvs.extend(sidenvs)
        return vs,nvs,nus,nfs,ms,pms,fms,pfms

    def build_road(self):
        trans = self.normal.copy().scale_u(self.road_width/2.0)
        v1 = self.start.copy().translate(trans)
        v2 = self.start.copy().translate(trans.flip())
        v3 = self.end.copy().translate(trans)
        v4 = self.end.copy().translate(trans.flip())
        rotate_pair([v1,v2],-1*self.angle1)
        rotate_pair([v3,v4],self.angle2)
        n = cv.v1_v2(v1,v2).cross(cv.v1_v2(v2,v3)).normalize()
        vs = [v1,v2,v3,v4]         
        nvs = [n,n,n,n]
        nus = [cv.vector2d(0,1),cv.vector2d(0,0),
              cv.vector2d(1,0),cv.vector2d(1,1)]
        cv.scale_coords2d(nus,cv.vector2d(self.length,self.road_width))
        cv.translate_coords2d(nus,self.uvguide)
        nfs = [[0,1,3],[1,2,3]]
        ms = ['cubemat']
        pms = ['/common/pmat/Stone']
        fms = [0,0]
        pfms = [0,0]
        return vs,nvs,nus,nfs,ms,pms,fms,pfms

    def quaddata(self):
        vs,nvs,nus,nfs,ms,pms,fms,pfms = self.build_road()
        '''#
        swvs,swnvs,swnus,swnfs,swms,swpms,swfms,swpfms = self.build_sidewalk()
        mpu.offset_faces(swnfs,len(vs))
        vs.extend(swvs)
        nvs.extend(swnvs)
        nus.extend(swnus)
        nfs.extend(swnfs)
        #ms.extend(swms)
        #pms.extend(swpms)
        fms.extend(swfms)
        pfms.extend(swpfms)
        '''#
        return vs,nvs,nus,nfs,ms,pms,fms,pfms

    def build(self):
        vdat = self.quaddata()
        newverts,newnorml,newuvs,newfaces,mats,pmats,fmats,pfmats = vdat
        xmlfile = '.'.join(['road_segment',
            self.get_segment_number(),'mesh','xml'])
        lod = False
        pwargs = {
            'verts' : newverts, 
            'nverts' : newnorml, 
            'uvs' : newuvs, 
            'faces' : newfaces, 
            'materials' : mats, 
            'face_materials' : fmats, 
            'phys_materials' : pmats, 
            'phys_face_materials' : pfmats, 
            'xmlfilename' : xmlfile, 
            'force_normal_calc' : True, 
            'prevent_normal_calc' : False, 
            'smooth_normals' : True, 
            'is_lod' : lod, 
            'has_lod' : False,
            #'has_lod' : not lod, 
                }
        mesh = pr.arbitrary_primitive(**pwargs)
        return mesh

    def build_lod(self):
        scubes = [pr.ucube()]
        return scubes

class road_plan(mbp.blueprint):
    def plot(self,verts):

        fig = plt.gcf()
        ax = fig.gca()
        ax.grid(True)

        mark = 0
        marker = None
        number = True
        for vdx in range(len(verts)):
            v = verts[vdx]
            mark = 1 if mark % 2 == 0 else 0
            altmark = 'o' if mark else 'x'
            vmark = altmark if marker is None else marker
            vplt = v.plot_xy()
            x = [vplt[0][0]]
            y = [vplt[0][1]]
            label = str(vdx+1)
            color = 'black'
            plt.plot(x,y,markersize = 10,marker = vmark,color = color)
            if number:
                plt.annotate(label,xy = (x[0],y[0]),xytext = (-20, 20),
                    textcoords = 'offset points', ha = 'right', va = 'bottom',
                    #bbox = dict(boxstyle = 'round,pad=0.5',fc = 'yellow', alpha = 0.5),
                    arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))

        plt.show()

    def __init__(self,start,end,tip,tail):

        self.road_width = 10
        self.sidewalk_width = 5
        self.rslength = self.road_width/2.0 + self.sidewalk_width/2.0

        self.start = start
        self.end = end
        self.tip = tip.normalize()
        self.tail = tail.normalize()
        self.tipnormal = self.tip.copy().flip().xy().rotate_z(fu.to_rad(-90)).normalize()
        self.tailnormal = self.tail.copy().xy().rotate_z(fu.to_rad(90)).normalize()
        #swoff1 = self.tailnormal.copy().scale_u(self.rslength)
        #swoff2 = self.tipnormal.copy().scale_u(self.rslength)
        self.controls = [start.copy(),end.copy()]
        #self.sidewalk_controls = [
        #    start.copy().translate(swoff1),
        #    end.copy().translate(swoff2)]
        self.extrude_tips()
        self.place_vertices()

    def extrude_tips(self):
        #eleng = cv.distance(self.start,self.end)/5.0
        eleng = 5.0
        start_tip = self.start.copy().translate(
                self.tail.copy().scale_u(eleng))
        #swstart_tip = self.sidewalk_controls[0].copy().translate(
        #                        self.tail.copy().scale_u(eleng))
        end_tip = self.end.copy().translate(
            self.tip.copy().flip().scale_u(eleng))
        #swend_tip = self.sidewalk_controls[1].copy().translate(
        #                self.tip.copy().flip().scale_u(eleng))
        mcp = cv.midpoint(start_tip,end_tip)
        trans = cv.midpoint(self.tail,self.tip.copy().flip())
        maxtransleng = cv.distance(start_tip,end_tip)/5.0
        trans.normalize().scale_u(0.5*maxtransleng)
        mcp.translate(trans)
        #swmcpoff = trans.copy().normalize().scale_u(-self.rslength)
        #swmcp = mcp.copy().translate(swmcpoff)
        #swmcp = mcp.copy().translate(trans.copy().normalize().scale_u(-self.rslength))
        self.controls.insert(1,end_tip)
        self.controls.insert(1,mcp)
        self.controls.insert(1,start_tip)

        #self.sidewalk_controls.insert(1,swend_tip)
        #self.sidewalk_controls.insert(1,swmcp)
        #self.sidewalk_controls.insert(1,swstart_tip)
        
        #self.plot(self.controls + self.sidewalk_controls)

    def pick_seg_count(self,v1,v2):
        ds = cv.distance(v1,v2)
        seglen = 2
        self.lastsegcnt = int(ds/seglen)
        return self.lastsegcnt

    def spline(self,c1,c2,c3,c4,scnt = None):
        cox = [c1.x,c2.x,c3.x,c4.x]
        coy = [c1.y,c2.y,c3.y,c4.y]
        coz = [c1.z,c2.z,c3.z,c4.z]
        tim = [0.0,1.0,2.0,3.0]
        alpha = 1.0/2.0
        mpu.parameterize_time([c1,c2,c3,c4],tim,alpha)
        if scnt is None:scnt = self.pick_seg_count(c2,c3)
        cox = mpu.catmull_rom(cox,tim,scnt)[1:-1]
        coy = mpu.catmull_rom(coy,tim,scnt)[1:-1] 
        coz = mpu.catmull_rom(coz,tim,scnt)[1:-1] 
        filled = [cv.vector(*i) for i in zip(cox,coy,coz)]
        return filled

    def place_vertices(self):
        verts = [self.start.copy()]
        #swoffset1 = self.tailnormal.copy().scale_u(
        #    self.sidewalk_width/2.0 + self.road_width/2.0)
        #swoffset2 = self.tipnormal.copy().scale_u(
        #    self.sidewalk_width/2.0 + self.road_width/2.0)
        #swverts = [self.start.copy().translate(swoffset1)]
        for dx in range(len(self.controls)-3):
            if len(verts) > 1:
                verts.pop(-1)
                #swverts.pop(-1)
            v1 = self.controls[dx]
            v2 = self.controls[dx+1]
            v3 = self.controls[dx+2]
            v4 = self.controls[dx+3]
            #sv1 = self.sidewalk_controls[dx]
            #sv2 = self.sidewalk_controls[dx+1]
            #sv3 = self.sidewalk_controls[dx+2]
            #sv4 = self.sidewalk_controls[dx+3]
            verts.extend(self.spline(v1,v2,v3,v4))
            #scnt = self.lastsegcnt
            #swverts.extend(self.spline(sv1,sv2,sv3,sv4,scnt))
        verts.append(self.end.copy())
        #swverts.append(self.end.copy().translate(swoffset2))
        self.vertices = verts
        #self.sidewalk_vertices = swverts
        self.set_tangents(verts)
        self.set_angles(self.tangents)

        #self.plot(self.vertices + self.sidewalk_vertices)

    def set_tangents(self,verts):
        tangs = []
        for sgdx in range(1,len(verts)):            
            p1,p2 = verts[sgdx-1],verts[sgdx]
            tangs.append(cv.v1_v2(p1,p2).normalize())
        tangs.append(self.tip.copy())
        self.tangents = tangs

    def set_angles(self,tangs):
        angs = [0.0]
        for tgdx in range(1,len(tangs)):
            t1,t2 = tangs[tgdx-1],tangs[tgdx]
            a12 = cv.angle_between_xy(t1.copy().xy(),t2.copy().xy())
            sign = 0.0 if a12 == 0.0 else a12/abs(a12)
            angs.append(sign * abs(a12) * 0.5)
        angs.append(0.0)
        self.angles = angs

    def split(self):
        pass

    def merge(self,other):
        pass

    def connect(self,other):
        pass

    def build(self):

        rw = self.road_width
        sww = self.sidewalk_width

        verts = self.vertices
        #swverts = self.sidewalk_vertices
        vcnt = len(verts)
        segments = []
        for sgdx in range(1,vcnt):
            a1,a2 = self.angles[sgdx-1],self.angles[sgdx]
            p1,p2 = verts[sgdx-1],verts[sgdx]
            #sp1,sp2 = swverts[sgdx-1],swverts[sgdx]
            if segments:uvguide = segments[-1].uv_coords[2]
            else:uvguide = cv.vector2d(0,0)
            strip = segment(p1,p2,a1,a2,rw,sww,uvguide)
            #strip = segment(p1,p2,sp1,sp2,a1,a2,rw,sww,uvguide)
            segments.append(strip.build())
        #segments = self.batch(segments)
        return segments

    def build_lod(self):
        return []




def test_road():
    c1 = cv.vector(0,0,0)
    c2 = cv.vector(50,20,10)
    tip = cv.vector(1,1,0)
    tail = cv.vector(1,0,0)

    rplan = road_plan(c1,c2,tip,tail)
    prims,lprims = rplan.build(),rplan.build_lod()

    rnode = sg.node(primitives = prims)#, lod_primitives = lprims)
    return rnode

def test():
    gritgeo.reset_world_scripts()
    gritgeo.create_element(test_road())
    gritgeo.output_world_scripts()









