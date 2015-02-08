import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv

import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.scenegraph as sg
import make_places.blueprints as mbp
import make_places.roads as rds
import make_places.pkler as pk

import os, pdb
import numpy as np
import random as rm
from math import sqrt
from math import cos
from math import sin
from math import tan

import matplotlib.pyplot as plt



road_batch_count = 0
class road_plan(mbp.blueprint):

    def terrain_points(self):
        rppts = []
        for cdx in range(len(self.corners)):
            corns = self.corners[cdx]
            ntpts = [c.copy() for c in corns]
            cv.translate_coords_z(ntpts,-1)
            if self.segment_styles[cdx] == 'raised':
                cv.translate_coords_z(ntpts,-15)
            rppts.extend(ntpts)
        return rppts

    def __init__(self, *args, **kwargs):
        self.road_prim_type = rds.road_segment_primitive
        self.road_type = 'road'

        self._default_('control_points',[],**kwargs)
        self._default_('leg_positions',[],**kwargs)

        self.road_width = 20
        self.road_height = 2
        kwargs['plot'] = False
        self.svargs = {
            'topology':None, 
            'enp':kwargs['end'], 
            'stp':kwargs['start'], 
            'dirs':kwargs['directions'],
                }
        self.calculate()
        #self.segment_styles = ['default']*self.segment_count
        mbp.blueprint.__init__(self, *args, **kwargs)

    def calculate(self):
        self.segment_vertices(**self.svargs)
        self.set_corners(self.segmented_vertices)
        self.set_bbox()

    def plot(self, verts = None, marker = None, 
            color = 'black', number = True, show = False):
        if verts is None:verts = self.segmented_vertices

        fig = plt.gcf()
        ax = fig.gca()
        ax.grid(True)

        mark = 0
        for vdx in range(len(verts)):
            v = verts[vdx]
            mark = 1 if mark % 2 == 0 else 0
            altmark = 'o' if mark else 'x'
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

        if hasattr(self,'bbox'):
            xybb = self.bbox
            c1,c2,c3,c4 = xybb.corners
            ax.axis([c1.x,c2.x,c1.y,c4.y])
            xybb.plot()

        if show: plt.show()

    def get_cardinal_normals(self, dirs):
        cardnorms = road_system_new.cardinal_normals
        print dirs
        dnorms = [cardnorms[dirs[0]],cardnorms[dirs[1]]]
        return dnorms

    #def segment_vertices(self, *args, **kwargs):
    def segment_vertices(self,topology = None,
            stp = None,enp = None,
            dirs = None,plot = False):
        def bend(vs):
            tips = vs
            cox = [t.x for t in tips]
            coy = [t.y for t in tips]
            coz = [t.z for t in tips]
            tim = [0.0,1.0,2.0,3.0]
            alpha = 1.0/2.0
            mpu.parameterize_time(tips,tim,alpha)
            scnt = self.pick_seg_count(tips[1:-1])
            cox = mpu.catmull_rom(cox,tim,scnt)
            coy = mpu.catmull_rom(coy,tim,scnt)
            coz = mpu.catmull_rom(coz,tim,scnt)
            new = [cv.vector(*i) for i in zip(cox,coy,coz)]
            return new
          
        if not topology is None:
            stp, enp = self.info_from_topology(*args, **kwargs)
        self.start = stp
        self.end = enp

        norms = self.get_cardinal_normals(dirs)
        self.stnorm = norms[0].copy()
        self.ednorm = norms[1].copy().flip()

        verts = [stp,enp]
        verts = self.clip_tips(verts,norms[0],norms[1])
        verts = self.add_tips(verts,norms[0],norms[1])
        verts = self.control_tips(verts,norms[0],norms[1])

        final_verts = []
        for dx in range(1,len(verts)-2):
            tips = [verts[dx-1],verts[dx],verts[dx+1],verts[dx+2]]
            final_verts.extend(bend(tips)[1:-1])
            if not dx == len(verts) - 3: final_verts.pop(-1)
            
            #self.plot(final_verts,color = 'purple')
            #self.plot(tips,number = False,marker = '*',color = 'orange')
            #plt.show() 

        if plot:
            self.plot(final_verts,color = 'purple')
            self.plot(verts,number = False,marker = 's',color = 'red')
            self.plot(tips,number = False,marker = '*',color = 'orange')
            plt.show() 

        self.segment_count = len(final_verts)
        self.segmented_vertices = final_verts
        self.segment_styles = ['default']*self.segment_count
        self.segment_lanes = [2]*self.segment_count
        return verts

    def pick_seg_count(self, vs):
        ds = cv.distance(vs[0],vs[-1])
        seglen = 15
        return int(ds/seglen)

    def add_tips(self,verts,n1,n2):
        clip = 15
        v1 = verts[0].copy()
        v2 = verts[-1].copy()
        cl1,cl2 = clip,clip
        v1.translate(n1.copy().scale_u(cl1))
        v2.translate(n2.copy().scale_u(cl2))
        verts.extend([v1, v2])
        verts.append(verts.pop(-3))
        return verts

    def clip_tips(self,verts,n1,n2):
        cl = 15
        v1 = verts[0].copy().translate(n1.copy().scale_u(cl))
        v2 = verts[-1].copy().translate(n2.copy().scale_u(cl))
        verts[0] = v1
        verts[-1] = v2
        return verts

    def control_tips(self,verts,n1,n2):
        for cp in self.control_points:
            verts.insert(2,cp)
        return verts

    def add_control_point(self,cp):
        st = self.start
        en = self.end

        cdists = [cv.distance_xy(st,c) for c in self.control_points]
        ncdist = cv.distance_xy(st,cp)
        for cdx in range(len(cdists)): 
            cd = cdists[cdx]
            if cd > ncdist:
                new_cdx = cdx
                break
            else: new_cdx = cdx + 1

        if cv.distance(cp,self.control_points[new_cdx]) < 100:
            self.control_points.pop(new_cdx)
        self.control_points.insert(new_cdx,cp)

    def set_corners(self, verts, plot = False):
        corners = []
        vcnt = len(verts)
        for sgdx in range(1,vcnt):            
            p1,p2 = verts[sgdx-1],verts[sgdx]
            corns = self.make_corners(p1,p2)

            if plot:
                self.plot([p1,p2],show = False)
                self.plot(corns,marker = 's',color = 'blue')

            corners.append(corns)
        self.corners = corners

    def make_corners(self, p1, p2):
        widt = self.road_width
        
        p1_p2 = cv.v1_v2(p1,p2).normalize()
        leng = cv.distance_xy(p1,p2)
        
        ang_z = cv.angle_from_xaxis_xy(p1_p2)
        #cpos = p1.copy().translate(p1_p2.scale_u(leng/2.0))
        cpos = p1.copy()
        corns = mpu.make_corners(cv.zero(),leng,widt,0)
        cv.translate_coords(corns,cv.vector(leng/2.0,0,0))
        cv.rotate_z_coords(corns,ang_z)
        cv.translate_coords(corns,cpos)
        cv.translate_coords_z(corns[1:3],p2.z-p1.z)
        return corns

    def set_bbox(self):
        bboxes = []
        for cdx in range(len(self.corners)):
            if self.segment_styles[cdx] == 'raised': continue
            corns = self.corners[cdx]
            bboxes.append(mpbb.xy_bbox(corns))
            bboxes[-1].segment_id = cdx
        xybb = mpbb.xy_bbox(children = bboxes)
        self.bbox = xybb
        return xybb

    def build(self):
        #print 'BUILD ROAD!'
        segs = self.build_segments()
        segs = self.batch_segments(segs)
        return segs

    def build_segments(self):
        verts = self.segmented_vertices
        rw = self.road_width
        rh = self.road_height
        segments = []
        vcnt = len(verts)
        tangs = [self.stnorm.copy().xy().normalize()]
        angs = []
        for sgdx in range(1,vcnt):            
            p1,p2 = verts[sgdx-1],verts[sgdx]
            tangs.append(cv.v1_v2(p1,p2).xy().normalize())
        tangs.append(self.ednorm.copy().xy().normalize())
        for tgdx in range(1,vcnt+1):
            t1,t2 = tangs[tgdx-1],tangs[tgdx]
            a12 = cv.angle_between_xy(t1,t2)
            sign = 0.0 if a12 == 0.0 else a12/abs(a12)
            if abs(a12) > np.pi/2:
                a12 = 0.0
            angs.append(sign * abs(a12))
        legs = [True]*vcnt
        legs[1::2] = [False]*(int(vcnt/2))
        for sgdx in range(1,vcnt):            
            a1,a2 = angs[sgdx-1],angs[sgdx]
            p1,p2 = verts[sgdx-1],verts[sgdx]

            segstyle = self.segment_styles[sgdx-1]
            if segstyle == 'default':
                self.road_prim_type = rds.road_segment_primitive
                lanes = self.lanes[sgdx]
                strips = self.build_segment(p1,p2,rw,rh,a1,a2,False,lanes)
            if segstyle == 'raised':
                self.road_prim_type = rds.highway_segment_primitive
                legup = self.legs[sgdx]
                lanes = self.lanes[sgdx]
                strips = self.build_segment(p1,p2,rw,rh,a1,a2,legup,lanes)
            elif segstyle is None:
                strips = []

            segments.extend(strips)
        return segments

    def build_segment(self, p1, p2, widt, depth, a1, a2, leg, lanes):
        leng = cv.distance_xy(p1,p2)
        p1_p2 = cv.v1_v2(p1,p2).xy().normalize()
        zdiff = p2.z - p1.z
        ang_z = cv.angle_from_xaxis_xy(p1_p2)
        strip = self.road_prim_type()
        strip.scale(cv.vector(leng,widt,depth))
        strip.scale_uvs(cv.vector(leng/widt,1,1))
        strip.translate(cv.vector(leng/2.0,0,-depth))
        strip.rotate_z(ang_z)
        theta1 = -1.0*a1/2.0
        theta2 =      a2/2.0
        strip.rotate_z_face(theta1, 'left')
        strip.translate_face(cv.vector(0,0,zdiff), 'right')
        strip.rotate_z_face(theta2, 'right')
        strip.translate(p1)
        if leg:
            alpha = cv.angle_from_xaxis_xy(cv.v1_v2(p1,p2))
            leg = self.build_leg(p1,alpha)
            return [strip,leg]
        else: return [strip]

    def build_leg(self, v, alpha):
        leg = pr.ucube()
        leg_leng = 20
        leg.scale(cv.vector(5,5,leg_leng))
        leg_pos = v.copy().translate_z(-leg_leng-2.0)
        #leg_pos = [v[0],v[1],v[2]-leg_leng-2.0]
        leg.rotate_z(alpha)
        leg.translate(leg_pos)
        self.leg_positions.append(leg_pos)
        return leg

    def batch_name(self):
        global road_batch_count
        name = '_road_segment_batch_' + str(road_batch_count)
        road_batch_count += 1
        return name

    def batch_segments(self, segs):
        stcnt = len(segs)
        if stcnt == 1: return segs

        batch_number = int(mpu.clamp(20,1,len(segs)))
        #batch_number = 10
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




class road_system_new(sg.node):
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
    cardinal_normals = {
        'west':cv.xhat.copy().flip(), 
        'southwest':cv.one().flip(), 
        'south':cv.yhat.copy().flip(), 
        'southeast':cv.vector(1,-1,0), 
        'east':cv.xhat.copy(), 
        'northeast':cv.one(), 
        'north':cv.yhat.copy(), 
        'northwest':cv.vector(-1,1,0), 
            }
    cardinals = [
        'north', 'northeast', 
        'east', 'southeast', 
        'south', 'southwest', 
        'west', 'northwest']

    def plot_cardinal_info(self, show = False):
        for key in self.cardinals:
            card = self.cardinal_normals[key]
            x = [0,card.x]
            y = [0,card.y]
            plt.plot(x,y,marker = 'o',color = 'green')
        if show: plt.show()

    def pick_sea_level(self, vals):
        maxval = max(vals)
        minval = min(vals)
        rng = maxval - minval
        return minval + rng/10.0

    def get_bbox(self):
        bboxes = []
        roads = self.tform.children
        for rdtf in roads:
            rdboxes = rdtf.owner.get_bbox()
            bboxes.extend(rdboxes)
        return bboxes

    def terrain_points(self):
        pts = []
        for rp in self.iroad_plans:
            pts.extend(rp.terrain_points())
        print 'tptcnt', len(pts)
        return pts
      
    def terrain_holes(self):
        pts = []
        for ch in self.tform.children:
            ntps = cv.translate_coords(
                [c.copy() for c in ch.owner.corners], cv.zhat)
            pts.append(ntps)#ch.owner.corners)
        return pts

    def __init__(self, *args, **kwargs):
        self._default_('name','road_system',**kwargs)

        self._default_('seeds',[0,45,180,270],**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)

        self.iroad_plans = self.istate_network(*args,**kwargs)

        sg.node.__init__(self,*args,**kwargs)

    def istate_network(self,*args,**kwargs):

        def ang_wobble(ang):
            rand = rm.choice([-1,1])
            aoff = rand * rm.choice([15,30,45,60,75])
            return ang + aoff

        def cardinal(deg):
            lo = -22.5
            hi = 337.5
            if deg >= hi: deg -= 360
            elif deg < lo: deg += 360
            for ke in self.deg_bins.keys():
                if mpu.in_range(deg,self.deg_bins[ke]):
                    return ke
            pdb.set_trace()

        def nodeoffset():
            return rm.choice([x-20 for x in range(40)])

        # first generate the interstates
        # each seed creates an interstate
        # each interstate is reachable from the others via a beltway
        interlinkdist = 1000
        intercitynodes = []
        interstates = []
        for se in self.seeds:
            newnode = cv.zero()
            antiang = ang_wobble(180.0)
            newnode.translate_x(interlinkdist).rotate_z(fu.to_rad(se))
            antinode = newnode.copy().rotate_z(fu.to_rad(antiang))
            #newnode.translate_z(nodeoffset())
            #antinode.translate_z(nodeoffset())
            ndir = cardinal(se)
            andir = cardinal(se + antiang)
            intercitynodes.append((newnode,antinode))

            cp = cv.midpoint(newnode,antinode)
            cp.translate(cp.copy().flip().scale_u(0.75))
            cpts = [cp]

            hway = rm.random() < 0.5
            rarg = {
                'control_points':cpts, 
                'start':newnode, 
                'end':antinode, 
                'directions':[ndir,andir],
                'road_height':2, 
                'road_width':20, 
                    }
            interstates.append(road_plan(**rarg))
            #if hway: interstates.append(highway(**rarg))
            #else: interstates.append(road(**rarg))

        return self.resolve_iroads(interstates)

    def resolve_iroads(self, interstates):

        fig = plt.gcf()
        ax = fig.gca()
        ax.grid(True)

        tries = 1000
        trycnt = 0
        state = False
        while not state and not trycnt > tries:
            interstates,state = self.resolve_round(interstates)
            trycnt += 1
            print 'istate state', state, trycnt > tries
        print 'istate state', state, trycnt > tries
        return interstates

    def resolve_round(self,interstates):
        state = True

        remove = []
        icnt = len(interstates)
        for idx1 in range(icnt - 1):

            if not state: break

            i1 = interstates[idx1]
            i1.set_bbox()
            ibb1 = i1.bbox

            for idx2 in range(idx1 + 1,icnt):
                i2 = interstates[idx2]
                i2.set_bbox()
                ibb2 = i2.bbox
                isect = ibb1.intersect_xy(ibb2)
                if not isect is None:
                    
                    remove.append(i2)
                    state = False

                    '''#
                    #i1.plot()
                    #i2.plot()

                    selfids = []
                    for me in isect['self members']:
                        sid = me.segment_id
                        selfids.append(sid)
                        if me.parent is ibb1: me.plot(colors = ['blue'])
                    selfids.insert(0,min(selfids)-1)
                    selfids.append(max(selfids)+1)
                    for sid in selfids:
                        i1.segment_styles[sid] = 'raised'

                    otherids = []
                    for me in isect['other members']:
                        sid = me.segment_id
                        otherids.append(sid)
                        if me.parent is ibb2: me.plot(colors = ['green'])
                    otherids.insert(0,min(otherids)-1)
                    otherids.append(max(otherids)+1)
                    for sid in otherids:
                        i2.segment_styles[sid] = None

                    ncp = isect['center'].copy()
                    i2.add_control_point(ncp)
                    i1.add_control_point(ncp.copy().translate_z(-15))

                    i1.plot()
                    i2.plot()
                    plt.show()

                    i1.calculate()
                    i2.calculate()
                    
                    i1.plot()
                    i2.plot()
                    plt.show()

                    state = False
                    break

                    #c1,c2,c3,c4 = mpbb.inscribe([ibb1,ibb2])
                    #ax.axis([c1.x,c2.x,c1.y,c4.y])
                    '''#
        for rm in remove: interstates.remove(rm)
        return interstates,state

    def hway_network(self,*args,**kwargs):
        # place some major roads which have stop
        # light intersections and ramps to interstates
        # these roads should be able to grow feeder roads
        pass

    def build(self):
        children = []
        for rp in self.iroad_plans: children.extend(rp.build())

        #children = self.network(*args,**kwargs)
        self.add_child(*children)

        plt.show()






