




import mp_vector as cv
import mp_utils as mpu
import mp_bboxes as mpbb
import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.scenegraph as sg
import make_places.blueprints as mbp

import make_places.newterrain as mpt

import make_places.gritty as gritgeo

import matplotlib.pyplot as plt
import numpy as np
import random as rm
from math import sqrt
import time
import pdb





segment_number = 0
class segment(mbp.blueprint):
    def get_segment_number(self):
        global segment_number
        num = str(segment_number)
        segment_number += 1
        return num

    materials = ['cubemat','concrete']
    phys_materials = ['/common/pmat/Stone']
    def __init__(self,p1,p2,a1,a2,lanecnt,rwidth,swwidth,swheight,uvguide):
        self.lanes = lanecnt
        self.lane_width = rwidth
        self.sidewalk_width = swwidth
        self.sidewalk_height = swheight

        self.start = p1
        self.end = p2
        self.angle1 = a1
        self.angle2 = a2
        self.uvguide = uvguide
        tangent = cv.v1_v2(self.start,self.end)
        self.length = tangent.magnitude()
        self.tangent = tangent.normalize()
        self.normal = self.tangent.copy().xy().rotate_z(fu.to_rad(90)).normalize()

        self.startnormal = self.normal.copy().rotate_z(-1*self.angle1).normalize()
        self.endnormal = self.normal.copy().rotate_z(self.angle2).normalize()

    def build_lane(self,lane,vs,nvs,nus,nfs,fms,pfms,lane_width,lh = 0,rh = 0):
        lanetrans1 = self.startnormal.copy().scale_u(lane)
        lanetrans2 = self.endnormal.copy().scale_u(lane)
        trans = self.normal.copy().scale_u(lane_width/2.0)
        v1 = self.start.copy().translate(lanetrans1).translate(trans)
        v2 = self.start.copy().translate(lanetrans1).translate(trans.flip())
        v3 = self.end.copy().translate(lanetrans2).translate(trans)
        v4 = self.end.copy().translate(lanetrans2).translate(trans.flip())
        v1.translate_z(lh)
        v2.translate_z(rh)
        v3.translate_z(rh)
        v4.translate_z(lh)
        mbp.rotate_pair([v1,v2],-1*self.angle1)
        mbp.rotate_pair([v3,v4],self.angle2)

        self.add_quad(vs,nvs,nus,nfs,fms,pfms,v1,v2,v3,v4)

    def build_road(self,vs,nvs,nus,nfs,fms,pfms):
        lc = self.lanes
        lanes = [x-(lc-1)/2.0 for x in range(lc)]
        for lan in lanes:
            lanw = lan*self.lane_width
            self.build_lane(lanw,vs,nvs,nus,nfs,fms,pfms,self.lane_width)

    def build_sidewalks(self,vs,nvs,nus,nfs,fms,pfms):
        lc = self.lanes
        swh = self.sidewalk_height
        lanes = [x-(lc-1)/2.0 for x in range(lc)]
        swleft = (lanes[0] - 0.5)*self.lane_width - 0.5*self.sidewalk_width
        swright = (lanes[-1] + 0.5)*self.lane_width + 0.5*self.sidewalk_width
        self.build_lane(swleft,vs,nvs,nus,nfs,fms,pfms,self.sidewalk_width,swh,swh)
        self.build_lane(swright,vs,nvs,nus,nfs,fms,pfms,self.sidewalk_width,swh,swh)
        swvs = vs[-8:]
        dx1 = 3
        dx2 = 0
        swleft = [
            swvs[dx1].copy(),swvs[dx1].copy().translate_z(-swh), 
            swvs[dx2].copy().translate_z(-swh),swvs[dx2].copy()]
        self.add_quad(vs,nvs,nus,nfs,fms,pfms,
            swleft[0],swleft[1],swleft[2],swleft[3])
        dx1 = 5
        dx2 = 6
        swright = [
            swvs[dx1].copy(),swvs[dx1].copy().translate_z(-swh),
            swvs[dx2].copy().translate_z(-swh),swvs[dx2].copy()]
        self.add_quad(vs,nvs,nus,nfs,fms,pfms,
            swright[0],swright[1],swright[2],swright[3])

    def quaddata(self):
        dmethods = [self.build_road,self.build_sidewalks]
        return mbp.blueprint.quaddata(self,dmethods)

    def build(self):
        xmlfile = '.'.join(['road_segment',
            self.get_segment_number(),'mesh','xml'])

        #self.road_faces = range(0,len(faces)-8)
        
        return mbp.blueprint.build(self,xmlfile,False,False)

road_batch_count = 0
class road_plan(mbp.blueprint):

    def batch_name(self):
        global road_batch_count
        name = '_road_segment_batch_' + str(road_batch_count)
        road_batch_count += 1
        return name

    def batch(self, segs):
        stcnt = len(segs)
        if stcnt == 1: return segs

        batch_number = int(mpu.clamp(20,1,len(segs)))
        batches = []
        dex0 = 0
        while dex0 < stcnt:
            sts_left = stcnt - dex0
            if sts_left >= batch_number: 
                sts_this_round = batch_number
            else: sts_this_round = sts_left % batch_number
            this_batchs = segs[dex0:dex0+sts_this_round]
            dex0 += sts_this_round

            batch = sg.node(name = self.batch_name(), 
                grit_renderingdistance = 500, 
                primitives = this_batchs,
                consumes_children = True)
            batches.append(batch)

        return batches

    def xy_bbox(self):
        bboxes = []
        for cdx in range(len(self.corners)):
            corns = self.corners[cdx]
            bboxes.append(mpbb.xy_bbox(corns))
            bboxes[-1].segment_id = cdx
        self.xybb = mpbb.xy_bbox(children = bboxes,owner = self)
        return self.xybb

    def spawn_point(self):
        # should this appeal to self.safe_vertices?
        cdxes = []
        vcnt = len(self.vertices)
        ccnt = len(self.controls)
        for vdx in range(vcnt):
            vpt = self.vertices[vdx]
            for cdx in range(ccnt):
                cpt = self.controls[cdx]
                if cv.near(cpt,vpt):
                    cdxes.append(vdx)
        rngs = [cdxes[x]-cdxes[x-1] for x in range(1,len(cdxes))]
        bgst = rngs.index(max(rngs))
        sdex = int((cdxes[bgst] + cdxes[bgst+1])/2.0)
        return (self.vertices[sdex].copy(),self.tangents[sdex].copy())

    def midway_point(self):
        vdx = len(self.vertices)/2
        return (self.vertices[vdx].copy(),self.tangents[vdx].copy())

    def nearest_point(self,point):
        ndists = [cv.distance(v,point) for v in self.vertices]
        nwhich = ndists.index(min(ndists))
        return (self.vertices[nwhich].copy(),self.tangents[nwhich].copy())

    def add_control(self,cpoint):
        cdists = [cv.distance(c,cpoint) for c in self.controls]
        if min(cdists) < 25:
            print 'could not add control'
            return

        crange = range(len(cdists))
        cwhich = zip(*sorted(zip(cdists,crange)))[1][1]
        self.controls.insert(cwhich,cpoint)
        self.calculate()

    style_keys = ['feeder','generic','street','highway','interstate']
    styles = {
        'generic':{
                'lanes':2, 
                'sidewalk_height':0.25, 
                'sidewalk_width':3, 
                'lane_width':4, 
                'plot_color':'black', 
                    }, 
        'interstate':{
                'lanes':4, 
                'sidewalk_height':0.25, 
                'sidewalk_width':5, 
                'lane_width':6, 
                'plot_color':'blue', 
                    }, 
        'highway':{
                'lanes':3, 
                'sidewalk_height':0.25, 
                'sidewalk_width':4, 
                'lane_width':6, 
                'plot_color':'green', 
                    }, 
        'street':{
                'lanes':2, 
                'sidewalk_height':0.25, 
                'sidewalk_width':3, 
                'lane_width':5, 
                'plot_color':'red', 
                    }, 
        'feeder':{
                'lanes':1, 
                'sidewalk_height':0.1, 
                'sidewalk_width':2, 
                'lane_width':4, 
                'plot_color':'brown', 
                    }, 
            }
    def __init__(self,start,end,tip,tail,controls = None,style = None, 
                    lanes = 3,swheight = 0.25,swwidth = 3,lnwidth = 5):
        if not style is None:
            lanes = self.styles[style]['lanes']
            swheight = self.styles[style]['sidewalk_height']
            swwidth = self.styles[style]['sidewalk_width']
            lnwidth = self.styles[style]['lane_width']
        else: style = 'generic'
        self.style = style
        self.lane_count = lanes
        self.road_width = lnwidth
        self.sidewalk_width = swwidth
        self.sidewalk_height = swheight
        self.total_width = self.road_width*self.lane_count +\
                                      self.sidewalk_width*2.0

        self.calculate(start,end,tip,tail,controls)

    def terrain_points(self):
        tpts = [v.copy().translate_z(-0.25) for v in self.vertices]
        return tpts

    def terrain_holes(self):
        hpts = []
        for corns in self.corners:
            hpts.append([c.copy() for c in corns])
        return hpts

    def calculate(self,start = None,end = None,tip = None,tail = None,controls = None):
        if controls == None: controls = []
        if not start is None: self.start = start
        if not end is None: self.end = end
        if not tip is None: self.tip = tip.normalize()
        if not tail is None: self.tail = tail.normalize()
        self.tipnormal = self.tip.copy().flip().xy().rotate_z(fu.to_rad(-90)).normalize()
        self.tailnormal = self.tail.copy().xy().rotate_z(fu.to_rad(90)).normalize()
        self.controls = [self.start.copy(),self.end.copy()]
        self.extrude_tips(controls)
        self.place_vertices()
        self.xy_bbox()

    def extrude_tips(self,controls):
        eleng = 5.0
        start_tip = self.start.copy().translate(
                self.tail.copy().scale_u(eleng))
        end_tip = self.end.copy().translate(
            self.tip.copy().flip().scale_u(eleng))
        self.controls.insert(1,end_tip)
        for cont in controls: self.controls.insert(1,cont)
        self.controls.insert(1,start_tip)
        #mbp.plot(self.controls)
        #plt.show()

    def pick_seg_count(self,v1,v2):
        ds = cv.distance(v1,v2)
        seglen = 4
        self.lastsegcnt = int(ds/seglen)
        return self.lastsegcnt

    def place_vertices(self):
        verts = [self.start.copy()]
        for dx in range(len(self.controls)-3):
            if len(verts) > 1:
                verts.pop(-1)
            v1 = self.controls[dx]
            v2 = self.controls[dx+1]
            v3 = self.controls[dx+2]
            v4 = self.controls[dx+3]
            scnt = self.pick_seg_count(v2,v3)
            verts.extend(cv.spline(v1,v2,v3,v4,scnt))
        verts.append(self.end.copy())
        self.vertices = verts
        self.set_tangents(verts)
        self.set_angles(self.tangents)
        self.set_corners()
        self.total_length = self.set_arc_length()
        self.set_safe_vertices()
        #mbp.plot(self.vertices)

    def set_safe_vertices(self):
        margin = 75
        safe = []
        vcnt = len(self.vertices)
        for vdx in range(vcnt):
            arc = self.arc_lengths[vdx]
            above = arc > margin
            below = arc < self.total_length - margin
            if above and below: safe.append(self.vertices[vdx])
        self.safe_vertices = safe 

    def set_arc_length(self):
        arc = 0.0
        self.arc_lengths = [arc]
        vcnt = len(self.vertices)
        for vdx in range(1,vcnt):
            v1 = self.vertices[vdx-1]
            v2 = self.vertices[vdx]
            arc += cv.distance(v1,v2)
            self.arc_lengths.append(arc)
        self.total_length = arc
        return arc

    def set_corners(self):
        def make_corners(p1,p2,a1,a2,tngnt):
            normal = tngnt.copy().xy().rotate_z(fu.to_rad(90)).normalize()
            startnormal = normal.copy().rotate_z(-1*a1).normalize()
            endnormal = normal.copy().rotate_z(a2).normalize()

            lane = self.total_width/2.0
            #lane = self.road_width*self.lane_count/2.0
            lanetrans1 = startnormal.copy().scale_u(lane)
            lanetrans2 = endnormal.copy().scale_u(lane)

            v1 = p1.copy().translate(lanetrans1)
            v2 = p1.copy().translate(lanetrans1.flip())
            v3 = p2.copy().translate(lanetrans2.flip())
            v4 = p2.copy().translate(lanetrans2.flip())
            
            return [v1,v2,v3,v4]

        corners = []
        verts = self.vertices
        vcnt = len(verts)
        for sgdx in range(1,vcnt):
            a1,a2 = self.angles[sgdx-1],self.angles[sgdx]
            p1,p2 = verts[sgdx-1],verts[sgdx]
            tngnt = self.tangents[sgdx-1]
            corners.append(make_corners(p1,p2,a1,a2,tngnt))
        self.corners = corners

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

            #a12 = clamp_periodic(a12,0,fu.PI)

            if fu.to_deg(a12) > 90:
                print 'angle is off?', fu.to_deg(a12)
                a12 = 0.0
                #pdb.set_trace()
            sign = 0.0 if a12 == 0.0 else a12/abs(a12)
            angs.append(sign * abs(a12) * 0.5)
        angs.append(0.0)
        self.angles = angs

    def split(self):
        # should return info to start a ramp
        pass

    def merge(self,other):
        # should return info to merge a ramp
        pass

    def connect(self,other):
        # pick a subset of self.vertices
        # pick a subset of other.vertices
        # extrude selfs subset towards other
        # extrude others subset towards self
        # use tangents as tip and tail to make new road
        smidx = len(self.vertices)/2
        omidx = len(other.vertices)/2
        smid = self.vertices[smidx].copy()
        omid = other.vertices[omidx].copy()
        sang = self.angles[smidx]
        oang = other.angles[omidx]
        stng = self.tangents[smidx].copy().flip()
        otng = self.tangents[omidx].copy().flip()
        snrm = stng.copy().flip().xy().rotate_z(fu.to_rad(-90)).normalize()
        onrm = otng.copy().xy().rotate_z(fu.to_rad(90)).normalize()

        smid.translate(snrm.scale_u(-5))
        omid.translate(onrm.scale_u(5))

        connection = road_plan(smid,omid,stng,otng,lanes = 1)

        #mbp.plot(self.vertices)
        #mbp.plot(other.vertices)
        #mbp.plot(connection.vertices)
        #plt.show()

        return connection

    def build(self):
        rw = self.road_width
        sww = self.sidewalk_width
        swh = self.sidewalk_height
        lcnt = self.lane_count

        verts = self.vertices
        vcnt = len(verts)
        segments = []
        for sgdx in range(1,vcnt):
            a1,a2 = self.angles[sgdx-1],self.angles[sgdx]
            p1,p2 = verts[sgdx-1],verts[sgdx]
            if segments:uvguide = segments[-1].uv_coords[2]
            else:uvguide = cv.vector2d(0,0)
            strip = segment(p1,p2,a1,a2,lcnt,rw,sww,swh,uvguide)
            segments.append(strip.build())
        segments = self.batch(segments)
        return segments

    def build_lod(self):
        return []

intersection_number = 0
class intersection_plan(mbp.blueprint):
    def get_segment_number(self):
        global intersection_number
        num = str(intersection_number)
        intersection_number += 1
        return num

    materials = ['cubemat']
    phys_materials = ['/common/pmat/Stone']

    def __init__(self,position,roads):
        self.position = position
        self.roadplans = roads

        self.reposition_roads(roads)
        self.xy_bbox()

    def xy_bbox(self):
        bboxes = []
        swconvex = [self.sidewalk_border]
        for cdx in range(len(swconvex)):
            corns = swconvex[cdx]
            bboxes.append(mpbb.xy_bbox(corns))
            bboxes[-1].segment_id = cdx
        self.xybb = mpbb.xy_bbox(children = bboxes,owner = self)
        return self.xybb

    def terrain_points(self):
        tpts = [self.position.copy()]
        return tpts

    def terrain_holes(self):
        hpts = [[c.copy() for c in self.sidewalk_border]]
        return hpts

    def reposition_roads(self,rplans):
        def find_tip(rplan,ileng):
            stdist = cv.distance(self.position,rplan.start)
            endist = cv.distance(self.position,rplan.end)
            if stdist < endist:
                p = rplan.start
                t = rplan.tail
                rplan.tail = rplan.tail.xy()
            else:
                p = rplan.end
                t = rplan.tip.copy().flip()
                rplan.tip = rplan.tip.xy()
            return p,t.xy().scale_u(ileng)

        rdwidths = [rp.total_width for rp in rplans]
        #infllngs = [2.0*rw for rw in rdwidths]
        #infllngs = [(sqrt(3.0)/2.0)*rw for rw in rdwidths]
        mxrw = max(rdwidths)
        infllngs = [(sqrt(3.0)/2.0)*mxrw for rw in rdwidths]
        rtips = [find_tip(rp,infl) for rp,infl in zip(rplans,infllngs)]
        for rtip in rtips:rtip[0].translate(rtip[1])
        for rp in rplans:rp.calculate()
        self.road_tips = [t[0] for t in rtips]

        rdpts = []
        swpts = []
        for rp in self.roadplans:
            tw = rp.road_width*rp.lane_count
            rdpts.extend(self.find_tips(rp,tw))
            #rdpts.extend(self.find_tips(rp,rp.total_width))
        for rp in self.roadplans:
            swpts.extend(self.find_tips(rp,rp.total_width))
            #swpts.extend(self.find_tips(rp,rp.total_width+2*rp.sidewalk_width))
        rdconvex = mpu.pts_to_convex_xy(rdpts)
        swconvex = mpu.pts_to_convex_xy(swpts)

        self.road_border = rdconvex
        self.sidewalk_border = swconvex

    def quaddata(self):
        dmethods = [self.build_flat]
        return mbp.blueprint.quaddata(self,dmethods)

    def build(self):
        xmlfile = '.'.join(['intersection',
            self.get_segment_number(),'mesh','xml'])
        iprim = mbp.blueprint.build(self,xmlfile,False,False)
        return [sg.node(primitives = [iprim])]
        
    def find_tips(self,rplan,width):
            stdist = cv.distance(self.position,rplan.start)
            endist = cv.distance(self.position,rplan.end)
            if stdist < endist:
                p1 = rplan.vertices[0].copy()
                p2 = p1.copy()
                p1.translate(rplan.tailnormal.copy().scale_u(-width/2.0))
                p2.translate(rplan.tailnormal.copy().scale_u(width/2.0))
            else:
                p1 = rplan.vertices[-1].copy()
                p2 = p1.copy()
                p1.translate(rplan.tipnormal.copy().scale_u(-width/2.0))
                p2.translate(rplan.tipnormal.copy().scale_u(width/2.0))
            return [p1,p2]

    def build_flat(self,vs,nvs,nus,nfs,fms,pfms):
        rdconvex = self.road_border
        swconvex = self.sidewalk_border

        swheights = []
        for rp in self.roadplans:swheights.extend([rp.sidewalk_height]*2)
        com = cv.center_of_mass(rdconvex)
        
        innerloop = [c.copy() for c in rdconvex]
        for ic in innerloop: ic.translate(cv.v1_v2(ic,com).scale_u(0.5))
        for swdx in range(len(rdconvex)):
            rc1 = rdconvex[swdx-1]
            rc2 = rdconvex[swdx]
            tiptest = True
            for rtip in self.road_tips:
                if cv.near_xy(cv.midpoint(rc1,rc2),rtip):
                    tiptest = False
                    break
            if not tiptest: continue
            h1 = swheights[swdx-1]
            h2 = swheights[swdx]
            v1 = rdconvex[swdx-1].copy().translate_z(h1)
            v2 = swconvex[swdx-1].copy().translate_z(h1)
            v3 = swconvex[swdx].copy().translate_z(h2)
            v4 = rdconvex[swdx].copy().translate_z(h2)
            v5 = v4.copy()
            v6 = v4.copy().translate_z(-h1)
            v7 = v1.copy().translate_z(-h2)
            v8 = v1.copy()
            self.add_quad(vs,nvs,nus,nfs,fms,pfms,v1,v2,v3,v4)
            self.add_quad(vs,nvs,nus,nfs,fms,pfms,v5,v6,v7,v8)

        innerloop.append(innerloop[0])
        rdconvex.append(rdconvex[0])
        self.bridge(vs,nvs,nus,nfs,fms,pfms,innerloop,rdconvex)
        self.tripie(vs,nvs,nus,nfs,fms,pfms,innerloop)



# i need several functions to build with
#
# it is generally safe to end one of two intersecting roads
# at the intersection
#
# after each fix, find the next issue and fix it, until no issue remain
#
# given two roads that intersect
#  at point of intersection make an intersection
#  end one of those roads at the intersection
#   this can be done in place on two road plans
#   but must return iplan as well, so output must be arbitrary list
#
#ROADS
# there are several types of roads:
#
# interstates
#  if theres a north, there must be a south, etc
#  there must be space between north/south, etc
#  no stoplights or intersections are allowed
#  must provide ramps for north and south, etc
#  can be raised on pillars
#
# highways
#  if theres a north, theres a south, etc
#  there can be a median or double yellow line between north/south, etc
#  intersections with other highways or roads require stoplights
#  access to other roads requires an exit lane
#  must have access to north and south
#
# roads
#  can be one-way
#  can form bridges for geography, not for overpassing
#  intersections require stop signs or stoplights
#
#INTERSECTIONS
# there are types of intersections depending on road types:
#
# when an interstate intersects another, the following are allowed
#  force one to bend and merge into the other
#  force one to underpass the other, providing ramps
#
# when a highway intersects a highway, an intersection with
# stoplights, crosswalks, possibly medians is created
#
# when a road intersects a road, simple intersection with stop signs
#  will suffice

def road_map(iplans,rplans):
    for ip in iplans: mbp.plot([ip.position],number = False)
    for rp in rplans: mbp.plot(rp.vertices,number = False)

def ang_wobble(ang,wobbles = [0,15,30,45,60,75]):
    rand = rm.choice([-1,1])
    aoff = rand * rm.choice(wobbles)
    return ang + aoff

def breakup(iplans,rplans,rdplan,breakpt,breaktangent):
    break1 = road_plan(
        rdplan.start.copy(),breakpt.copy(),
        breaktangent.copy(),rdplan.tail.copy(),
        style = rdplan.style)
    break2 = road_plan(
        breakpt.copy(),rdplan.end.copy(),
        rdplan.tip.copy(),breaktangent.copy(),
        style = rdplan.style)
    if rdplan in rplans:rplans.remove(rdplan)
    rplans.append(break1)
    rplans.append(break2)
    return iplans,rplans

def clamp_periodic(val,floor,ceiling):
    period = ceiling - floor
    while val < floor: val += period
    while val > ceiling: val -= period
    return val

def in_cone(pt,apex,normal,alpha,min_distance = None,max_distance = None):
    proxy = pt.copy()
    proxy.translate(apex.copy().flip())
    proxyangle = cv.angle_from_xaxis_xy(proxy)
    normalangle = cv.angle_from_xaxis_xy(normal)
    minalpha = clamp_periodic(normalangle - alpha,0,2*fu.PI)
    maxalpha = clamp_periodic(normalangle + alpha,0,2*fu.PI)
    if proxyangle < minalpha or proxyangle > maxalpha: return False
    else:
        apexdistance = cv.distance(apex,pt)
        if not max_distance is None and min_distance is None:
            if apexdistance > max_distance: return False
        elif max_distance is None and not min_distance is None:
            if apexdistance < min_distance: return False
        elif not max_distance is None and not min_distance is None:
            if apexdistance < min_distance or\
                apexdistance > max_distance: return False
        return True

def find_owner(iplans,rplans,point):
    for rp in rplans:
        for rv in rp.vertices:
            if cv.distance_xy(point,rv) < 3.0: return rp
    for ip in iplans:
        if cv.distance_xy(point,ip.position) < 3.0: return ip
    pdb.set_trace()

def safe_z_offset(safeleng,max_slope = 0.1):
    max_offset = mpu.clamp(int(safeleng*max_slope),20,1000)
    return rm.randrange(max_offset)

def safe_ending(iplans,rplans,safe_start,safe_tail):
    visible = []
    for rp in rplans:
        for rv in rp.safe_vertices:
            if in_cone(rv,safe_start,safe_tail,fu.to_rad(45),min_distance = 100):
                if not cv.near(rv,safe_start):visible.append(rv)

    if not visible:
        safeleng = 1000
        safe_end = safe_start.copy().translate(safe_tail.copy().scale_u(safeleng))
        safe_end.z += safe_z_offset(safeleng,max_slope = 0.1)
        #safe_tip = safe_tail.copy().rotate_z(fu.to_rad(ang_wobble(0))).normalize()
        safe_tip = safe_tail.copy().normalize()
        safe_owner = None
    else: 
        which = cv.find_closest_xy(safe_start,visible,len(visible),0.0)
        safepoint = visible[which]
        saferoad = find_owner(iplans,rplans,safepoint)
        safepair = saferoad.nearest_point(safepoint)
        safe_end = safepair[0]
        safe_tip = safepair[1].rotate_z(fu.to_rad(90))
        
        tip_check = safe_end.copy().translate(safe_tip.copy().scale_u(20.0))
        tsd = cv.distance_xy(tip_check,safe_start)
        ssd = cv.distance_xy(safe_start,safe_end)
        if tsd < ssd:safe_tip.flip()
        safe_owner = saferoad

        #road_map(iplans,rplans)
        #mbp.plot(visible,number = False,color = 'green')
        #mbp.plot([safe_start],number = True,marker = 's',color = 'blue')
        #plt.show()

    return safe_end,safe_tip,safe_owner

def safe_check(iplans,rplans,newrp):
    isections = []
    nbb = newrp.xybb
    all_plans = iplans + rplans
    for erd in all_plans:
        ebb = erd.xybb
        isect = nbb.intersect_xy(ebb)
        if not isect is None:
            icenter = isect['center']
            nearend = cv.distance_xy(newrp.end,icenter) < 10.0
            nearstart = cv.distance_xy(newrp.start,icenter) < 10.0
            if not nearend and not nearstart:
                isections.append(isect)
    print 'safecheck',len(isections)
    if isections: return False
    else: return True

def pick_ordered(val,options):
    for op in options:
        if op[0] < val:
            return op[1]

def determine_style(rd1,rd2,st,en):
    options = [
        (900,'interstate'),(400,'highway'),
        (25,'street'),(0,'feeder')]
    style_guess = pick_ordered(cv.distance(st,en),options)
    skeys = road_plan.style_keys
    sdx1 = skeys.index(rd1.style)
    sdx2 = skeys.index(rd2.style)
    sdx3 = skeys.index(style_guess)
    style = skeys[sdx3]
    #style = skeys[min([sdx1,sdx2,sdx3])]
    return style

def grow(iplans,rplans,gtip,gstep):
    growths = rm.choice([1,2])
    growth_angles = [-90,90]
    grown = []

    spawn = gtip.spawn_point()
    spawnpt = spawn[0]
    spawntn = spawn[1]
    for gdx in range(growths):
        gangle = growth_angles.pop(rm.randrange(len(growth_angles)))
        gangle = clamp_periodic(gangle,0,360)
        spawnstart = spawnpt.copy()
        spawntail = spawntn.copy().xy().rotate_z(fu.to_rad(gangle)).normalize()
        spawnend,spawntip,target = safe_ending(iplans,rplans,spawnstart,spawntail)
        if target is None:gstyle = 'highway'
        else:gstyle = determine_style(gtip,target,spawnstart,spawnend)
        growth = road_plan(spawnstart,spawnend,spawntip,spawntail,style = gstyle)
        if safe_check(iplans,rplans,growth):
            if not target is None:
                endtarg = target
                endinfo = endtarg.nearest_point(spawnend)
                iplans,rplans = breakup(iplans,rplans,endtarg,endinfo[0],endinfo[1])
                intersecting = rplans[-2:] + [growth]
                iplan = intersection_plan(spawnend.copy(),intersecting)
                iplans.append(iplan)
            grown.append(growth)
        
    if grown:
        iplans,rplans = breakup(iplans,rplans,gtip,spawnpt,spawntn)
        intersecting = rplans[-2:] + grown
        iplan = intersection_plan(spawnpt.copy(),intersecting)
        iplans.append(iplan)
        rplans.extend(grown)
    return iplans,rplans

def fractate(steps = 30):
    seedst = cv.vector(-500,-500,0)
    seeden = cv.vector( 500, 500,0)
    seedtp = cv.vector(   0,   1,0)
    seedtl = cv.vector(   1,   0,0)

    rplans = [road_plan(seedst,seeden,seedtp,seedtl,style = 'interstate')]
    iplans = []

    steplookup = ['interstate']*4 + ['highway']*8 + ['street']*12 + ['feeder']*6

    mingrowlength = 200
    for step in range(steps):
        gtip = rm.choice(rplans)
        if gtip.total_length < mingrowlength:
            print 'tip is too short to grow!'
            continue
        #stepstyle = steplookup[step]
        stepstyle = 'generic'
        iplans,rplans = grow(iplans,rplans,gtip,stepstyle)
    return iplans,rplans

def generate_maps(iplans,rplans):
    def plot(iplans,rplans):
        for ip in iplans:
            col = 'purple'
            mbp.plot([ip.position],color = col,marker = 's',number = False)
        for rp in rplans:
            col = road_plan.styles[rp.style]['plot_color']
            mbp.plot(rp.vertices,color = col,number = False)
    plot(iplans,rplans)





class road_system_plan(mbp.blueprint):
    dang = 22.5
    deg_rngs = [((dx*45.0)-dang,(dx*45.0)+dang) for dx in range(8)]
    deg_bins = {
        'west':deg_rngs[0], 
        'southwest':deg_rngs[1], 
        'south':deg_rngs[2], 
        'southeast':deg_rngs[3], 
        'east':deg_rngs[4], 
        'northeast':deg_rngs[5], 
        'north':deg_rngs[6], 
        'northwest':deg_rngs[7], 
            }
    cardinals = {
        'west':cv.vector(-1,0,0),
        'southwest':cv.vector(-1,-1,0),
        'south':cv.vector(0,-1,0),
        'southeast':cv.vector(1,-1,0),
        'east':cv.vector(1,0,0),
        'northeast':cv.vector(1,1,0),
        'north':cv.vector(0,1,0),
        'northwest':cv.vector(-1,1,0),
            }

    def __init__(self,steps):
        self.steps = steps
        self.name = 'road_system'
        self.seeds = [0,45,180,270]

        self.road_plans = self.network()

    def terrain_points(self):
        tpts = []
        return tpts

    def network(self):

        def ang_wobble(ang):
            rand = rm.choice([-1,1])
            aoff = rand * rm.choice([15,30,45,60,75])
            return ang + aoff

        def cardinal(deg):
            if deg >= 360: deg -= 360
            elif deg < 0: deg += 360
            for ke in self.deg_bins.keys():
                if mpu.in_range(deg,self.deg_bins[ke]):
                    return ke

        def nodeoffset():
            return rm.choice([x-20 for x in range(40)])

        interlinkdist = 1000
        intercitynodes = []
        interstates = []

        self.seeds = [rm.choice(self.seeds)]
        for se in self.seeds:
            se = rm.choice(self.seeds)
            newnode = cv.zero()
            antiang = ang_wobble(180.0)
            newnode.translate_x(interlinkdist).rotate_z(fu.to_rad(se))
            antinode = newnode.copy().rotate_z(fu.to_rad(antiang))
            newnode.translate_z(nodeoffset())
            antinode.translate_z(nodeoffset())
            ndir = cardinal(se)
            andir = cardinal(se + antiang)
            intercitynodes.append((newnode,antinode))
            interstates.append(road_plan(newnode,antinode,
                self.cardinals[andir].copy().flip(),
                self.cardinals[ndir].copy(),lanes = 4))
        
        interstates.append(spawn_interstate(
            interstates,interstates[-1],fu.to_rad(60)))
        interstates.append(spawn_interstate(
            interstates,interstates[-1],fu.to_rad(60)))
        interstates.append(spawn_interstate(
            interstates,interstates[-1],fu.to_rad(60)))

        return interstates

    def build(self):
        built = []
        for istate in self.road_plans: built.extend(istate.build())
        return built

def demonstrate(many = 5):
    for m in range(many):
        iplans,rplans = fractate()

        plt.figure(m+1)
        #plt.subplot(many,1,m)
        generate_maps(iplans,rplans)

    plt.title('road system demo')
    plt.show()

def generate_region_points(iplans,rplans):
    pts = []
    for ip in iplans: pts.append(ip.position.copy())
    for rp in rplans:
        pts.append(rp.start.copy())
        pts.append(rp.end.copy())
    return pts

def make_road_system_plans(steps = 20):
    iplans,rplans = fractate(steps)
    generate_maps(iplans,rplans)
    plt.show()
    return iplans,rplans







def test_road():
    c1 = cv.vector(0,0,0)
    c2 = cv.vector(150,60,20)
    tip = cv.vector(0,1,0)
    tail = cv.vector(1,0,0)
    rplan1 = road_plan(c1,c2,tip,tail)

    c1 = cv.vector(0,0,0)
    c2 = cv.vector(-175,-100,40)
    tip = cv.vector(-1,0,0)
    tail = cv.vector(-1,0,0)
    rplan2 = road_plan(c1,c2,tip,tail)

    c1 = cv.vector(0,0,0)
    c2 = cv.vector(125,85,-20)
    tip = cv.vector(1,0,0)
    tail = cv.vector(0,1,0)
    cp = cv.vector(0,50,0)
    rplan3 = road_plan(c1,c2,tip,tail,controls = [cp],lanes = 2)

    c1 = cv.vector(0,0,0)
    c2 = cv.vector(-200,-200,-30)
    tip = cv.vector(-1,0,0)
    tail = cv.vector(0,-1,0)
    rplan4 = road_plan(c1,c2,tip,tail)

    #rplan4.start.translate(cv.vector(0,-10,-2))
    #rplan4.calculate()
    #rplan4.calculate(c1.copy().translate(cv.vector(0,-5,-1)),c2.copy(),tip,tail)
    #rplan4 = rplan1.connect(rplan3)

    iplan1 = intersection_plan(cv.vector(0,0,0),[rplan1,rplan2,rplan4,rplan3])

    rplans = [rplan1,rplan2,rplan3,rplan4,iplan1]
    rnodes = [sg.node(primitives = rp.build()) for rp in rplans]
    return rnodes

def test():
    gritgeo.reset_world_scripts()

    iplans,rplans = fractate()
    generate_maps(iplans,rplans)
    plt.show()

    rsysplans = iplans[:]
    rsysplans.extend(rplans)
    rsys = []
    fpts = []
    hpts = []
    for rp in rsysplans:
        rsys.extend(rp.build())
        fpts.extend(rp.terrain_points())
        hpts.extend(rp.terrain_holes())

    rpts = mpu.make_corners(cv.zero(),2000,2000,0)
    targs = {
        'fixed_pts':fpts, 
        'hole_pts':hpts, 
        'region_pts':rpts, 
        'polygon_edge_length':20, 
        'primitive_edge_length':200, 
            }
    terr = mpt.make_terrain(**targs)
    gritgeo.create_element(rsys,terr)
    gritgeo.output_world_scripts()








