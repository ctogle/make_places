import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.scenegraph as sg
import make_places.blueprints as mbp
import make_places.newnewroads as mpr

import make_places.gritty as gritgeo

import mp_vector as cv
import mp_utils as mpu
import mp_bboxes as mpbb

import matplotlib.pyplot as plt
import numpy as np
import random as rm
from math import sqrt
import time
import pdb

'''#
this is a stab at creating dense urban geometry
it should allow for holes/subways/basements

first generate a topology for roads
  this topology is a set of loops; pts and normals
  first grow a set of loops for highways
  cut them into smaller loops using lower level roads

using this arrive at loops of verts 
fill these loops with terrain and structures constituting blocks



'''#

class roadloop():

    def _plot(self):
        mbp.plot(self.pts,color = 'green',marker = 's')
        mbp.plot([self.center],number = False,color = 'red',marker = 's')

    def __init__(self,pts):
        if mbp.clockwise(pts):pts.reverse()
        self.pts = pts
        self.center = cv.center_of_mass(pts)
        self.enms = mpbb.get_norms(pts)
        self.pcnt = len(pts)
        self.prng = range(self.pcnt)
        self.neighbors = [None]*self.pcnt

    def _grow(self,bounds):
        if not self.prng:
            print 'this loop cannot grow!'
            return
        n1 = rm.choice(self.prng)
        if n1 == self.pcnt - 1: n2 = 0
        else: n2 = n1 + 1
        l1 = self.pts[n1]
        l2 = self.pts[n2]
        d = cv.distance(l1,l2)
        enm = self.enms[n1].copy().scale_u(d)
        zoff1 = rm.choice(range(25))
        zoff2 = rm.choice(range(25))
        l3 = l2.copy().translate(enm).translate_z(zoff1)
        l4 = l1.copy().translate(enm).translate_z(zoff2)
        nloop = roadloop([l1,l2,l3,l4])
        self.neighbors[n1] = nloop
        self.prng.remove(n1)
        return nloop

    def _select_plans(self,iplans,rplans):

        def on_border(pt):
            for p in self.pts:
                if cv.distance(pt,p) < 25:
                    return True
            return False

        ips = []
        rps = []
        for ip in iplans:
            if on_border(ip.position):
                ips.append(ip)
        for rp in rplans:
            if on_border(rp.start) and on_border(rp.end):
                rps.append(rp)

        self.rplans = rps
        self.iplans = ips

    def _perimeter(self):
        ppts = []
        for rp in self.rplans:
            ltpd = cv.distance(rp._left_edge[0],self.center)
            rtpd = cv.distance(rp._right_edge[0],self.center)
            if ltpd < rtpd:ppts.extend(rp._left_edge)
            else:ppts.extend(rp._right_edge)
        for ip in self.iplans:
            minedist = cv.distance(ip._edges[0][0],self.center)
            mindex = 0
            for egdx in range(1,len(ip._edges)):
                eg = ip._edges[egdx]
                edist = cv.distance(eg[0],self.center)
                if edist < minedist:
                    minedist = edist
                    mindex = egdx
            ppts.extend(ip._edges[mindex])

        ppts = mpu.theta_order(ppts)

        #mbp.plot(ppts,color = 'blue',marker = 'o')
        #mbp.plot([self.center],color = 'red',marker = 'o')
        #plt.show()

        return ppts

    def _pfill(self):
        fillpts = self._perimeter()
        bp = mbp.blueprint()
        nfs = bp._bridge_patch(fillpts,n = 25,m = 'gridmat')
        bp._project_uv_xy(nfs)
        cube = mbp.ucube(m = 'gridmat')
        cube.scale(cv.one().scale_u(50))
        cube.translate(self.center)
        bp._extra_primitives.append(cube)
        return bp._primitives()
        
    def _edges(self):
        egs = []
        for x in range(self.pcnt):
            p1 = self.pts[x-1]
            p2 = self.pts[x]
            egs.append([p1,p2])
        egs.append(egs.pop(0))
        return egs

def make_road_plans(rloops):
    ipts = []
    rpts = []
    for rl in rloops:
        for p in rl.pts:
            if not p in ipts:
                ipts.append(p.copy())
        regs = rl._edges()
        for eg in regs:
            oeg = eg[:]
            oeg.reverse()
            if not oeg in rpts:
                rpts.append(eg)

    #mbp.plot(ipts,color = 'green',marker = 's')
    #for rp in rpts:
    #    mbp.plot(rp,color = 'blue',marker = 'o')
    #plt.show()
        
    iplans = []
    rplans = []
    for rp in rpts:
        r1,r2 = rp
        n1 = cv.v1_v2(r1,r2).normalize()
        n2 = n1.copy()
        rplan = mpr.road_plan(
            r1.copy(),r2.copy(),
            n2,n1,style = 'highway')
        rplans.append(rplan)

    for ip in ipts:
        rps = []
        for rp in rplans:
            if cv.near(rp.start,ip) or cv.near(rp.end,ip):
                rps.append(rp)
        iplan = mpr.intersection_plan(ip.copy(),rps)
        iplans.append(iplan)
        
    return iplans,rplans

def map_roads(iplans,rplans,bounds):
    mpr.generate_maps(iplans,rplans)
    mbp.plot(bounds,color = 'red',marker = 'o')
    plt.show()

def build_road_plans(iplans,rplans):
    for p in iplans:gritgeo.create_element(p.build())
    for p in rplans:gritgeo.create_element(p.build())
    #pass

def outer_boundary(bounds,rloops,iplans,rplans):
    orps = rplans[:]
    for rp in rplans:
        lcnt = 0
        for rl in rloops:
            if rp in rl.rplans:
                lcnt += 1
        if lcnt > 1:
            orps.remove(rp)
    oips = []
    for ip in iplans:
        rcnt = 0
        for rp in orps:
            if rp in ip.roadplans:
                rcnt += 1
        if rcnt > 1:
            oips.append(ip)

    #for rp in orps:
    #    col = mpr.road_plan.styles[rp.style]['plot_color']
    #    mbp.plot(rp.vertices,color = col,number = False)
    #for ip in oips:
    #    col = 'purple'
    #    mbp.plot([ip.position],color = col,marker = 's',number = False)
    #plt.show()
    
    fillpts = [p.copy().translate_z(-1.0) for p in bounds]
    bp = mbp.blueprint()
    #nfs = bp._bridge_patch(fillpts,n = 25,m = 'gridmat')
    nfs = bp._bridge_afm(fillpts,m = 'gridmat')
    bp._project_uv_xy(nfs)
    obprim = bp._primitives()
    gritgeo.create_primitive(obprim,rdist = 2000)





def road_topology(bounds = None):
    if bounds is None:
        bounds = mbp.polygon(8)
        #bounds = mpu.dice_edges(bounds,2)
        s = cv.vector(1000,1000,0)
        cv.scale_coords(bounds,s)

    seeds = mbp.polygon(4)
    cv.scale_coords(seeds,cv.vector(500,500,0))
    rloops = [roadloop(seeds)]
    for g in range(4):
        gloop = rm.choice(rloops)
        growth = gloop._grow(bounds)
        if growth: rloops.append(growth)
        
    #for rl in rloops: rl._plot()
    #mbp.plot(bounds,color = 'red',marker = 'o')
    #plt.show()

    iplans,rplans = make_road_plans(rloops)
    map_roads(iplans,rplans,bounds)
    build_road_plans(iplans,rplans)
    for rl in rloops:
        rl._select_plans(iplans,rplans)
        gritgeo.create_primitive(rl._pfill(),rdist = 2000)

    outer_boundary(bounds,rloops,iplans,rplans)





def test():
    gritgeo.reset_world_scripts()
    road_topology()
    gritgeo.output_world_scripts()




