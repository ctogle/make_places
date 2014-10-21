import make_places.fundamental as fu
from make_places.fundamental import element
from make_places.floors import floor
from make_places.primitives import ucube
from make_places.primitives import uoctagon
#from make_places.primitives import unit_cube

import numpy as np
import random as rm
from math import sqrt
from math import cos
from math import sin
from math import tan
from copy import deepcopy as dcopy

cardinal_directions = [
    'north', 'northeast', 
    'east', 'southeast', 
    'south', 'southwest', 
    'west', 'northwest']
cardinal_norms = [
    [0,1,0],fu.normalize([1,1,0]),
    [1,0,0],fu.normalize([1,-1,0]), 
    [0,-1,0],fu.normalize([-1,-1,0]), 
    [-1,0,0],fu.normalize([-1,1,0])]

class intersection(element):

    def __init__(self, *args, **kwargs):
        kweys = kwargs.keys()
        if 'road_width' in kweys: rw = kwargs['road_width']
        else: rw = 20
        self.road_width = rw
        if 'road_height' in kweys: rh = kwargs['road_height']
        else: rh = 2
        self.road_height = rh
        segs = self.make_segments(*args, **kwargs)
        kwargs['primitives'] = segs
        element.__init__(self, *args, **kwargs)

    def make_segments(self, *args, **kwargs):
        segs = []
        rw = self.road_width
        rh = self.road_height
        uo = uoctagon()
        uo.scale([rw,rw,rh])
        segs.append(uo)
        return segs
        
    def get_bbox(self):
        corners = [[0,0,0],[50,0,0],[50,50,0],[0,50,0]]
        #fu.rotate_z_coords(corners,theta)
        x,y,z = self.position
        fu.translate_coords(corners,[x-25,y-25,z])
        bboxes = [fu.bbox(position = self.position, 
            corners = corners)]
        return bboxes

'''#
class ______intersection(element):
    # each intersection is essentially an octagon
    # when a direction and its opposite are None
    #  the octagon can hide these outlets
    # a road can hook up to the intersection at at orientation
    #  defined by angle between road tangent and outlet normal
    def __init__(self, *args, **kwargs):
        self.clip_length = 25
        self.outlets = kwargs['topology'][kwargs['topodex']]
        #for card in cardinal_directions:
        #    self.outlets[card] = None
        kwargs['primitives'] = self.make_segments(*args, **kwargs)
        #kwargs['children'] = self.make_segments(*args, **kwargs)
        element.__init__(self, *args, **kwargs)

    def get_bbox(self):
        corners = [[0,0,0],[50,0,0],[50,50,0],[0,50,0]]
        #fu.rotate_z_coords(corners,theta)
        x,y,z = self.position
        fu.translate_coords(corners,[x-25,y-25,z])
        bboxes = [fu.bbox(position = self.position, 
            corners = corners)]
        return bboxes

    def make_segments2(self, *args, **kwargs):
        seg = unit_cube()
        seg.scale([50,50,2])
        seg.translate([-25,-25,-2])
        segs.append(seg)
        print('outlets',kwargs['position'],corners)
        return segs

    def make_segments(self, *args, **kwargs):
        cl = self.clip_length
        cls2 = float(cl)/sqrt(2.0)
        card_corners = {
            'north' : [0,cl,0], 
            'northeast' : [cls2,cls2,0],  
            'east' : [cl,0,0], 
            'southeast' : [cls2,-1*cls2,0], 
            'south' : [0,-1*cl,0], 
            'southwest' : [-1*cls2,-1*cls2,0], 
            'west' : [-1*cl,0,0], 
            'northwest' : [-1*cls2,cls2,0], 
                }
        corners = []
        for card in cardinal_directions:
            if not self.outlets[card] is None:
                corners.append((card,card_corners[card]))
        self.corners = corners

        w = 30.0
        segs = []
        for corn in corners:
            ca = corn[0]
            co = corn[1]
            seg = unit_cube()
            seg.scale([2,w,10])
            cardx = cardinal_directions.index(ca)
            cardn = cardinal_norms[cardx]
            zhat = [0,0,1]
            nnorm = fu.normalize(fu.cross(cardn,zhat))
            ang_z = fu.angle_from_xaxis_xy(cardn)
            seg.translate([
                0.0, 
                #-1.0*nnorm[0]*w/2.0,
                -1.0*nnorm[1]*w/2.0,0])
            seg.rotate_z(ang_z)
            seg.translate(co)
            segs.append(seg)

        seg = unit_cube()
        seg.scale([50,50,2])
        seg.translate([-25,-25,-2])
        segs.append(seg)
        print('outlets',kwargs['position'],corners)
        return segs
'''#

class road(element):
    def __init__(self, *args, **kwargs):
        kweys = kwargs.keys()
        if 'road_width' in kweys: rw = kwargs['road_width']
        else: rw = 10
        self.road_width = rw
        if 'road_height' in kweys: rh = kwargs['road_height']
        else: rh = 2
        self.road_height = rh
        self.clip_length = 25
        self.set_segmented_vertices(*args, **kwargs)
        segs = self.make_segments(*args, **kwargs)
        kwargs['primitives'] = segs
        element.__init__(self, *args, **kwargs)

    def get_bbox(self):
        def make_corners(p1, p2):
            widt = self.road_width
            leng = fu.distance(p1,p2)
            p1_p2 = fu.normalize(fu.v1_v2(p1,p2))
            ang_z = fu.angle_from_xaxis(p1_p2)
            corns = [[0,0,0],[leng,0,0],[leng,widt,0],[0,widt,0]]
            fu.translate_coords(corns,[0,-widt/2.0,0])
            fu.rotate_z_coords(corns,ang_z)
            fu.translate_coords(corns,p1)
            return corns
        verts = self.segmented_vertices
        bboxes = []
        vcnt = len(verts)
        for sgdx in range(1,vcnt):            
            p1,p2 = verts[sgdx-1],verts[sgdx]
            corns = make_corners(p1,p2)
            bboxes.append(fu.bbox(corners = corns))
        return bboxes

    def get_cardinal_normals(self, dirs):
        def getcardnorm(dx):
            cardx = cardinal_directions.index(dirs[dx])
            cardn = cardinal_norms[cardx]
            return cardn
        norms = [getcardnorm(x) for x in range(2)]
        return norms

    def info_from_topology(self, *args, **kwargs):
        topol = kwargs['topology']
        nodes = kwargs['nodes']
        st,en = topol[nodes[0]],topol[nodes[1]]
        stp = st['inter']['position']
        enp = en['inter']['position']
        return stp, enp

    def set_segmented_vertices(self, *args, **kwargs):
        kweys = kwargs.keys()
        if 'topology' in kweys:
            stp, enp = self.info_from_topology(*args, **kwargs)
        else:
            stp = kwargs['start']
            enp = kwargs['end']
        dirs = kwargs['directions']
        norms = self.get_cardinal_normals(dirs)
        self.stnorm = norms[0]
        self.ednorm = fu.flip(norms[1])

        segdices = 3
        verts = [stp,enp]
        #verts = self.clip_tips(verts,norms[0],norms[1])
        #verts = self.add_tips(verts,norms[0],norms[1])
        #verts = self.add_tips_OLD(verts,norms[0],norms[1])
        pitch = 0
        pitch_to_go = -1.0*fu.angle_between_xy(norms[0],fu.flip(norms[1]))
        zhat = [0,0,1]
        rdnorm = fu.cross(fu.normalize(fu.v1_v2(stp,enp)),zhat)
        def gauss(x, alpha = 1.0, sigma = 1.0, xbarr = 0.0):
            return alpha * np.exp(-1*((x - xbarr)**2/(2*sigma**2)))

        def sine_clip(x, alpha, ang, dxrng):
            sign = ang/abs(ang)
            ang = sign * (ang % np.pi) if not ang == np.pi else np.pi
            #print('ptg', fu.to_deg(ang))
            dx = dxrng[1] - dxrng[0]
            xd = (0.5 + x - dxrng[0])/dx
            xrad = 2 * ang * xd
            return sign * alpha * sin(xrad)# + self.road_width/2.0

        def bend(vs):
            inner = vs[1+1:-1-1]
            icnt = len(inner)
            #xbar = icnt/2.0
            #sig = icnt/(1.5)
            #ndists = [x + 0.5 for x in range(icnt)]
            #ndists = [gauss(x, 30, sig, xbar) for x in ndists]
            seglen = fu.distance_xy(vs[-2],vs[1])/2.0
            maxo = 0.4 * seglen * tan(pitch_to_go/2.0)
            ndists = [sine_clip(x,maxo,pitch_to_go,[0,icnt]) 
                                  for x in range(0,icnt)]
            offsets = [fu.flip(rdnorm[:]) for v in inner]
            [fu.scale_vector(off,[nd,nd,nd]) for 
                off,nd in zip(offsets,ndists)]
            for off,inn in zip(offsets,inner):
                fu.translate_vector(inn,off)

        for sgdx in range(segdices):
            vcnt = len(verts)
            newvs = verts[:]
            for vdx in range(1+1,vcnt-1):
                f,b = verts[vdx-1],verts[vdx]
                newv = fu.midpoint(f,b)
                newvs.insert(vdx+(len(newvs)-len(verts)),newv)
            verts = newvs[:]
        #if segdices > 0: bend(verts)
        self.segmented_vertices = verts
        return verts

    def add_tips_OLD(self,verts,n1,n2):
        clip = 25
        v1 = verts[0][:]
        v2 = verts[1][:]
        cl1,cl2 = clip,clip
        fu.translate_vector(v1,fu.scale_vector(n1[:],[cl1,cl1,cl1]))
        fu.translate_vector(v2,fu.scale_vector(n2[:],[cl2,cl2,cl2]))
        verts.extend([v1, v2])
        verts.append(verts.pop(-3))
        return verts

    def add_tips(self,verts,no1,no2):
        clip = 25
        n1 = no1[:]
        n2 = no2[:]
        v1 = verts[0][:]
        v2 = verts[1][:]
        print('n1n2',n1,n2)
        if not n1 == fu.flip(n2):
            v1_v2 = fu.v1_v2(v1,v2)
            d = fu.magnitude(v1_v2)
            alpha = abs(fu.angle_between_xy(v1_v2,n1))
            gamma = abs(fu.angle_between_xy(fu.flip(v1_v2),n2))
            print('alphgam',fu.to_deg(alpha),fu.to_deg(gamma))
            eta = np.pi/2 - alpha - gamma
            h = d * sin(alpha)
            epsilon = d * cos(alpha) - h * tan(eta)
            isect = fu.translate_vector(v1[:],
                fu.scale_vector(n1[:],
                    [epsilon,epsilon,epsilon]))
        else: isect = fu.center_of_mass([v1,v2])
        #isect = [0,100,0]
        d1 = fu.distance_xy(v1,isect)
        d2 = fu.distance_xy(v2,isect)
        if d1 > d2:
            cl1 = clip + d1 - d2
            cl2 = clip
        elif d2 > d1:
            cl1 = clip
            cl2 = clip + d2 - d1
        else: cl1,cl2 = clip,clip
        print('isect',isect)
        print('cl1cl2',cl1,cl2,d1,d2)
        print('v1v2',v1, v2)
        fu.translate_vector(v1,fu.scale_vector(
            fu.normalize(n1),[cl1,cl1,cl1]))
        fu.translate_vector(v2,fu.scale_vector(
            fu.normalize(n2),[cl2,cl2,cl2]))
        verts.extend([v1, v2])
        verts.append(verts.pop(-3))
        print('verrrts')
        for v in verts: print('vvv',v)
        print('n1n2again',n1,n2)
        return verts

    def clip_tips(self,verts,n1,n2):
        cl = self.clip_length
        v1 = fu.translate_vector(verts[0][:],
            fu.scale_vector(n1[:],[cl,cl,cl]))
        v2 = fu.translate_vector(verts[-1][:],
            fu.scale_vector(n2[:],[cl,cl,cl]))
        verts[0] = v1
        verts[1] = v2
        return verts

    def make_segments(self, *args, **kwargs):
        verts = self.segmented_vertices
        rw = self.road_width
        rh = self.road_height
        segments = []
        vcnt = len(verts)
        tangs = [self.stnorm]
        angs = []
        for sgdx in range(1,vcnt):            
            p1,p2 = verts[sgdx-1],verts[sgdx]
            #tangs.append(fu.normalize(fu.v1_v2(p1,p2)))
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dz = p2[2] - p1[2]
            tangs.append(fu.normalize([dx,dy,dz]))
        tangs.append(self.ednorm)
        for tgdx in range(1,vcnt+1):
            t1,t2 = tangs[tgdx-1],tangs[tgdx]
            a12 = fu.angle_between_xy(t1,t2)
            sign = 0.0 if a12 == 0.0 else a12/abs(a12)
            if abs(a12) > np.pi/2:
                a12 = 0.0
            angs.append(sign * abs(a12))
            #angs.append(sign * (abs(a12)%(np.pi/2.0)))

        for sgdx in range(1,vcnt):            
            #t1,t2,t3 = tangs[sgdx-1],tangs[sgdx],tangs[sgdx+1]
            a1,a2 = angs[sgdx-1],angs[sgdx]
            p1,p2 = verts[sgdx-1],verts[sgdx]
            strip = self.make_segment(p1,p2,rw,rh,a1,a2)#t1,t2,t3)
            #strip = self.make_segment(p1,p2,rw,rh,t1,t2,t3)
            segments.append(strip)
        return segments

    def make_segment(self, p1, p2, widt, depth, a1, a2):#t1, t2, t3):
    #def make_segment(self, p1, p2, widt, depth, t1, t2, t3):
        leng = fu.distance_xy(p1,p2)
        p1_p2 = fu.normalize(fu.v1_v2(p1,p2))
        zdiff = p2[2] - p1[2]
        ang_z = fu.angle_from_xaxis_xy(p1_p2)

        strip = ucube()
        strip.scale([leng,widt,depth])
        strip.translate([leng/2.0,0,-depth])
        strip.rotate_z(ang_z)
        #theta1 = -1*fu.angle_between_xy(t1,t2)/2.0
        #theta2 =    fu.angle_between_xy(t2,t3)/2.0
        theta1 = -1.0*a1/2.0
        theta2 =      a2/2.0
        strip.rotate_z_face(theta1, 'left')
        strip.translate_face([0,0,zdiff], 'right')
        strip.rotate_z_face(theta2, 'right')
        #print('th1th2', fu.to_deg(theta1), fu.to_deg(theta2))
        strip.translate(p1)
        return strip

def connect_points(P):
    for j in range( 1, len(P)-2 ):  # skip the ends
        for t in range( 10 ):  # t: 0 .1 .2 .. .9
            p = spline_4p( t/10, P[j-1], P[j], P[j+1], P[j+2] )
    print('splinee!',p)

def spline_4p( t, p_1, p0, p1, p2 ):
    """ Catmull-Rom
        (Ps can be numpy vectors or arrays too: colors, curves ...)
    """
    # wikipedia Catmull-Rom -> Cubic_Hermite_spline
    # 0 -> p0,  1 -> p1,  1/2 -> (- p_1 + 9 p0 + 9 p1 - p2) / 16
    # assert 0 <= t <= 1
    return (
          t*((2-t)*t - 1)   * p_1
        + (t*t*(3*t - 5) + 2) * p0
        + t*((4 - 3*t)*t + 1) * p1
        + (t-1)*t*t         * p2 ) / 2

class road_system(element):
    def __init__(self, *args, **kwargs):
        try: self.linkmin = kwargs['linkmin']
        except KeyError: self.linkmin = 200
        try: self.linkmax = kwargs['linkmax']
        except KeyError: self.linkmax = 400
        try: self.angs = kwargs['linkangles']
        except KeyError: self.angs = [90*x for x in range(4)]
        try: self.growth_tips = kwargs['growth_tips']
        except KeyError: self.growth_tips = 5
        try: self.region_bounds = kwargs['region_bounds']
        except KeyError: self.region_bounds = [(0,1000),(0,1000)]
        try: self.seeds = kwargs['seeds']
        except KeyError: self.seeds = [[0,0,0],[1000,1000,0]]
        try: self.intercnt = kwargs['intersection_count']
        except KeyError: self.intercnt = 20
        if 'interargs' in kwargs.keys():
            interargs = kwargs['interargs']
            kwargs['children'] =\
                self.make_system_from_intersections(interargs)
        else:kwargs['children'] = self.make_primitives_web(*args, **kwargs)
        kwargs['materials'] = ['imgtex']
        element.__init__(self, *args, **kwargs)

    def make_primitives_web(self, *args, **kwargs):
        def good_dir(tip, ang):
            link = rm.choice(range(linkmin,linkmax,50))
            #link = rm.randrange(linkmin,linkmax)
            tippos = tip['position'][:]
            angrad = (np.pi/180.0)*ang
            z_off_min = -50
            z_off_max =  50
            z_offset = rm.randrange(z_off_min, z_off_max)
            offset = [link*cos(angrad),link*sin(angrad),z_offset]
            newtip = fu.translate_vector(tippos, offset)
            if not fu.in_region(region_bounds, newtip):
                return False,None
            for ipos in [i['position'] for i in interargs]:
                d = fu.distance(newtip, ipos)
                if d < linkmin: return False,None
            return True,newtip

        def get_angle(tip):
            nodes = [i['position'] for i in interargs]
            cmass = [np.mean([s[0] for s in nodes]), np.mean([s[1]
                for s in nodes]), np.mean([s[2] for s in nodes])]
            #cmass = [0,0,0]
            cmass_ang = fu.to_deg(fu.angle_from_xaxis(
                fu.v1_v2(tip['position'],cmass)))
            tangs = angs[:]
            angdists = [abs(x-cmass_ang) for x in tangs]
            closestang = tangs[angdists.index(min(angdists))]
            tangs.extend([closestang]*20)
            while len(tangs) > 0:
                angdx = rm.randrange(len(tangs))
                ang = tangs.pop(angdx)
                passes,newpos = good_dir(tip, ang)
                if passes:
                    return ang,newpos
            return None,None

        def place_inter(tip):
            ang,newpos = get_angle(tip)
            if ang is None: return
            return newpos

        growth_tips = self.growth_tips
        region_bounds = self.region_bounds
        linkmin, linkmax = self.linkmin,self.linkmax
        seeds = self.seeds
        angs = self.angs
        intercnt = self.intercnt
        seedcnt = len(seeds)
        branches = []
        for idx in range(seedcnt):
            branches.append([{
                'position' : seeds[idx],   
                    }])
        interargs = [br[0] for br in branches]
        for idx in range(intercnt):
            tips = [br[-min([len(interargs),growth_tips]):] 
                    for br in branches]
            bdx = rm.randrange(seedcnt)
            tip = rm.choice(tips[bdx])
            newpos = place_inter(tip)
            if not newpos is None:
                interargs.append({
                    'position' : newpos, 
                        })
                branches[bdx].append(interargs[-1])
            else: print('cant place intersection!!')
        return self.make_system_from_intersections(interargs)

    def make_system_from_intersections(self, interargs):
        elements = []
        topology = [{} for inter in interargs]
        for inter, topo in zip(interargs, topology):
            for card in cardinal_directions:
                topo[card] = None
            topo['inter'] = inter
            topo['roads'] = []
            topo['linkcnt'] = 0

        self.roads = []
        for tdx, topo in enumerate(topology):
            topology[tdx] = find_neighbors(topology,topo)
        rdbbs = []
        for tdx, topo in enumerate(topology):
            inter = topo['inter']
            inter['topology'] = topology
            inter['topodex'] = tdx
            elements.append(intersection(**inter))
            for rarg in topo['roads']:
                newrd = road(**rarg)
                newbb = newrd.get_bbox()
                if not fu.bbox.intersects(newbb[0],rdbbs,newbb):
                    rdbbs.extend(newbb)
                    self.roads.append(newrd)
                    elements.append(newrd)
                else:
                    print('topology mistake from road intersection!')
        self.topology = topology
        return elements

    def make_primitives_from_blocks(self, *args, **kwargs):
        prims = []
        # given a list of blocks, determine a set of roads which bounds them
        # assume them do not overlap, and that a road should bound each
        # determine locations of intersections as all corners of every block
        # determine the width, length, and position of each road connecting
        # intersections
        # also assume that intersections will never intersect by construction
        #  that is the blocks are sized/positioned to prevent strange
        #  intersections
        # create the kwargs which includes them all
        def get_inter_length():
            return 40
        def get_inter_width():
            return 40
        blocks = args[0]
        used_bcorners = []
        corner_signs = [(-1,-1), (0, -1), (0, 0), (-1, 0)]
        interargs = []
        for bl in blocks:
            corn = bl.corners
            c1, c2, c3, c4 = corn
            for c_, signs in zip(corn, corner_signs):
                ilength = get_inter_length()
                iwidth = get_inter_width()
                ipos = fu.translate_vector(c_[:], 
                    [signs[0]*ilength,signs[1]*iwidth,0]), 
                if not ipos in used_bcorners:
                    used_bcorners.append(ipos)
                    interargs.append({
                        'name' : 'intersection_' + str(len(used_bcorners)), 
                        'position' : fu.translate_vector(
                            c_[:],[signs[0]*ilength,signs[1]*iwidth,0]), 
                        'length' : ilength, 
                        'width' : iwidth, 
                        'floor_height' : 1.0})
        return self.make_system_from_intersections(interargs)

    def get_bbox(self):
        bboxes = []
        roads = self.children
        for rd in roads:
            rdboxes = rd.get_bbox()
            bboxes.extend(rdboxes)
        return bboxes

def pick_closest(pots,ndists):
    if pots:
        ndx = ndists.index(min(ndists))
        return pots[ndx]
    return None,None

def select_outlet(outlets,ordered):
    for ord_ in ordered:
        if ord_ in outlets:
            return ord_

def north_check(topology,topo,seek_fov,linkmax):
    antidirs = ['west','southwest','south','southeast','east']
    tpos = topo['inter']['position']
    potentials = []
    ndists = []
    tthresh = 50
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos[1] < pnpos[1]:
                ndist = float(pnpos[1] - tpos[1])
                if ndist < linkmax:
                    tdist = float(pnpos[0] - tpos[0])
                    pn_fov_theta = fu.to_deg(np.arctan(abs(tdist)/ndist))
                    if pn_fov_theta < seek_fov/2.0:
                        if abs(tdist) <= tthresh:
                            order = ['south','southeast','southwest']
                        elif tdist < -tthresh:
                            order = ['southeast','south','east']
                        elif tdist > tthresh:
                            order = ['southwest','south','west']
                        dir_ = select_outlet(outlets,order)
                        if not dir_ is None:
                            potentials.append((pntopo,dir_))
                            ndists.append(ndist)
    return pick_closest(potentials,ndists)

def south_check(topology,topo,seek_fov,linkmax):
    antidirs = ['west','northwest','north','northeast','east']
    tpos = topo['inter']['position']
    potentials = []
    ndists = []
    tthresh = 50
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos[1] > pnpos[1]:
                ndist = -1*float(pnpos[1] - tpos[1])
                if ndist < linkmax:
                    tdist = float(pnpos[0] - tpos[0])
                    pn_fov_theta = fu.to_deg(np.arctan(abs(tdist)/ndist))
                    if pn_fov_theta < seek_fov/2.0:
                        if abs(tdist) <= tthresh:
                            order = ['north','northeast','northwest']
                        elif tdist < -tthresh:
                            order = ['northeast','north','east']
                        elif tdist > tthresh:
                            order = ['northwest','north','west']
                        dir_ = select_outlet(outlets,order)
                        if not dir_ is None:
                            potentials.append((pntopo,dir_))
                            ndists.append(ndist)
    return pick_closest(potentials,ndists)

def east_check(topology,topo,seek_fov,linkmax):
    antidirs = ['north','northwest','west','southwest','south']
    tpos = topo['inter']['position']
    potentials = []
    ndists = []
    normdx = 0
    trandx = 1
    tthresh = 50
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos[normdx] < pnpos[normdx]:
                ndist = float(pnpos[normdx] - tpos[normdx])
                if ndist < linkmax:
                    tdist = float(pnpos[trandx] - tpos[trandx])
                    pn_fov_theta = fu.to_deg(np.arctan(abs(tdist)/ndist))
                    if pn_fov_theta < seek_fov/2.0:
                        if abs(tdist) <= tthresh:
                            order = ['west','southwest','northwest']
                        elif tdist < -tthresh:
                            order = ['northwest','west','north']
                        elif tdist > tthresh:
                            order = ['southwest','west','south']
                        dir_ = select_outlet(outlets,order)
                        if not dir_ is None:
                            potentials.append((pntopo,dir_))
                            ndists.append(ndist)
    return pick_closest(potentials,ndists)

def west_check(topology,topo,seek_fov,linkmax):
    antidirs = ['north','northeast','east','southeast','south']
    tpos = topo['inter']['position']
    potentials = []
    ndists = []
    normdx = 0
    trandx = 1
    tthresh = 50
    for pntopo in topology:
        outlets = [ake for ake in antidirs if pntopo[ake] is None]
        if outlets:
            pnpos = pntopo['inter']['position']
            if tpos[normdx] > pnpos[normdx]:
                ndist = -1*float(pnpos[normdx] - tpos[normdx])
                if ndist < linkmax:
                    tdist = float(pnpos[trandx] - tpos[trandx])
                    pn_fov_theta = fu.to_deg(np.arctan(abs(tdist)/ndist))
                    if pn_fov_theta < seek_fov/2.0:
                        if abs(tdist) <= tthresh:
                            order = ['east','southeast','northeast']
                        elif tdist < -tthresh:
                            order = ['northeast','east','north']
                        elif tdist > tthresh:
                            order = ['southeast','east','south']
                        dir_ = select_outlet(outlets,order)
                        if not dir_ is None:
                            potentials.append((pntopo,dir_))
                            ndists.append(ndist)
    return pick_closest(potentials,ndists)

neighbor_checks = {
    'north' : north_check, 
    'east' : east_check, 
    'south' : south_check, 
    'west' : west_check, 
        }
def find_neighbors(topology,topo):
    topoid = [t is topo for t in topology].index(True)
    seek_fov = 60
    maxlinks = 4
    linkmax = 1000
    for card in cardinal_directions:
        if topo['linkcnt'] >= maxlinks: return topo
        if not card in neighbor_checks.keys(): continue
        neighb,neighbdir = neighbor_checks[card](
            topology,topo,seek_fov,linkmax)
        if not neighb is None:
            topodx = [n is neighb for n in topology].index(True)
            if neighb['linkcnt'] >= maxlinks: continue
            if topodx in topo.values(): continue
            topo[card] = topodx
            topo['linkcnt'] += 1
            neighb[neighbdir] = topoid
            neighb['linkcnt'] += 1
            topo['roads'].append({
                'topology' : topology, 
                'directions' : (card,neighbdir), 
                'nodes' : (topoid,topodx)})
    return topo

def no_road_intersects(topology,idx1,idx2):
    topo1 = topology[idx1]
    topo2 = topology[idx2]
    s1 = (topo1['inter']['position'],
          topo2['inter']['position'],)
    cardinals = ['north', 'south', 'east', 'west']
    for x in topology:
        links = [x[key] for key in cardinals if not x[key] is None]
        for ldx in links:
            y = topology[ldx]
            s2 = (x['inter']['position'],
                  y['inter']['position'],)
            if fu.segments_intersect(s1,s2): return False
    return True
    




