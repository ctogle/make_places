import make_places.fundamental as fu
import mp_utils as mpu
import mp_bboxes as mpbb
import mp_terrain as mpt
import mp_vector as cv
from make_places.scenegraph import node
from make_places.primitives import arbitrary_primitive
import make_places.profiler as prf
import make_places.veg as veg

from math import sqrt
from copy import deepcopy as dcopy
import numpy as np
import random as rm
import pdb, time

class terrain(node):
    def __init__(self, *args, **kwargs):
        kwargs['uv_scales'] = cv.one().scale_u(0.1)
        self._default_('sea_level',0.0,**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)
        self._default_('grit_renderingdistance',500,**kwargs)
        self._default_('grit_lod_renderingdistance',2000,**kwargs)
        self._default_('pts_of_interest',[],**kwargs)
        self._default_('splits',3,**kwargs)
        self._default_('smooths',25,**kwargs)
        self._default_('region_bounds',[(0,1000),(0,1000)],**kwargs)
        self._default_('bboxes',[],**kwargs)
    
        rb = self.region_bounds
        t1 = cv.vector(rb[0][0],rb[1][0],0)
        t2 = cv.vector(rb[0][1],rb[1][0],0)
        t3 = cv.vector(rb[0][0],rb[1][1],0)
        t4 = cv.vector(rb[0][1],rb[1][1],0)

        hexagonal = True
        #hexagonal = False
        if hexagonal:
            xrng,yrng = rb[0][1]-rb[0][0],rb[1][1]-rb[1][0]
            mrng = max([xrng,yrng])
            hrad = mrng
            center = cv.center_of_mass([t1,t2,t3,t4])
            hverts = []
            for ang in [0,60,120,180,240,300]:
                pt = cv.vector(hrad,0,0)
                pt.rotate_z(fu.to_rad(ang))
                hverts.append(pt)
            cv.translate_coords(hverts,center)
            hverts.insert(0,center)
            pieces = []
            ptlocs = []
            bounds = []
            for trdx in range(6):
                c2dx = trdx+1
                c3dx = trdx+2
                if c3dx == 7: c3dx = 1
                c1 = hverts[0]
                c2 = hverts[c2dx]
                c3 = hverts[c3dx]
                terr,locs,locs_str = mpt.make_terrain((c1,c2,c3),
                    self.splits,self.smooths,self.pts_of_interest,
                    self.sea_level)
                self.pts_of_interest.extend(
                    [v.position for v in terr.boundary_points])
                pieces.append(terr)
                ptlocs.append(locs)
        
            self.primitives, self.lod_primitives = self.stitch(pieces,ptlocs)

        else:
            print 'square terrain is broken!'
            pdb.set_trace()
            #r = 1000
            #t1 = [-r,0,0]
            #t3 = [r,0,0]
            #y = (4*r)/sqrt(3)
            #t2 = [0,-y,0]
            #fu.translate_coords([t1,t2,t3],[250,250,0])
            cv.translate_coords([t1],[-50,-50,0])
            cv.translate_coords([t2],[ 50,-50,0])
            cv.translate_coords([t3],[ 50, 50,0])
            cv.translate_coords([t4],[-50, 50,0])
            terr1,locs1,locs1str = mpt.make_terrain((t1,t2,t3),self.splits,
                        self.smooths,self.pts_of_interest,self.sea_level)
            terr2,locs2,locs2str = mpt.make_terrain((t2,t4,t3),self.splits,
                        self.smooths,self.pts_of_interest,self.sea_level)
            #terr1,locs1 = make_terrain((t1,t2,t3),self.splits,self.smooths,self.pts_of_interest)
            #terr2,locs2 = make_terrain((t2,t4,t3),self.splits,self.smooths,self.pts_of_interest)
            pieces = [terr1,terr2]
            ptlocs = [locs1,locs2]
            
            #self.use_mpt = use_mpt
            #self.use_mpt = True
            self.primitives, self.lod_primitives = self.stitch(pieces,ptlocs)

        #vegetate = True
        vegetate = False
        if vegetate:
            children = prf.measure_time('vegetate',self.vegetate,pieces)
            self.add_child(*children)
        node.__init__(self, *args, **kwargs)
        self.assign_material('grass2', propagate = False)
        #self.assign_material('ground')

    def vegetate(self, terras):
        vchildren = []
        bboxes = self.bboxes
        for ter in terras:
            fdat = ter.face_data()
            vcargs = []
            fcnt = len(fdat)
            for fdx in range(fcnt):
                if rm.choice([0,1,1,1]):
                    verts = [v.position for v in fdat[fdx]]
                    vegbox = mpbb.bbox(corners = verts)
                    if not mpbb.intersects(bboxes, vegbox):
                    #if not vegbox.intersects(bboxes, vegbox):
                        nvcarg = (verts,None,[fdx])
                        vcargs.append(nvcarg)

            # stitch the nvcargs together based on how contiguous they are
            dx = 0
            vccnt = len(vcargs)
            vcmax = 4
            fewer = []
            while dx < vccnt:
                left = vccnt - dx
                if left >= vcmax: vc_this_round = vcmax
                else: vc_this_round = left % vcmax
                relev = vcargs[dx:dx+vc_this_round]
                reverts = [r[0] for r in relev]
                refaces = range(vc_this_round)
                fewer.append((reverts,[],refaces))
                dx += vc_this_round

            for varg in fewer:
                vchild = veg.vegetate(*varg)
                vchildren.append(vchild)

        return vchildren

    def stitch(self, pieces, locs):
        if len(pieces) == 6:
            p1,p2,p3,p4,p5,p6 = pieces
            pairs = [(p1,p2),(p2,p3),(p3,p4),(p4,p5),(p5,p6),(p6,p1)]
        elif len(pieces) == 2:
            p1,p2 = pieces
            pairs = [(p1,p2),(p2,p1)]

        all_pieces = []
        for p1,p2 in pairs:
            print('stitching')#,p1,p2)
            b1,b2 = p1.boundary_points,p2.boundary_points
            for bp1 in b1:
                for bp2 in b2:
                    if bp1._str == bp2._str:
                        midz = (bp1.position.z+bp2.position.z)/2.0
                        bp1.position.z = midz
                        bp2.position.z = midz
                        bp1.weights.z = 0.0
                        bp2.weights.z = 0.0
            pieces = [p1,p2]
            [pc.smooth(100,lc) for pc,lc in zip(pieces,locs)]
            all_pieces.append(pieces[0])

        meshpieces = []
        lod_meshpieces = []
        [meshpieces.extend(p.meshes()) for p in all_pieces]
        [lod_meshpieces.extend(p.meshes(lod = True)) for p in all_pieces]
    
        meshpieces = [arbitrary_primitive(**pwg) for pwg in meshpieces]
        lod_meshpieces = [arbitrary_primitive(**lpwg) for lpwg in lod_meshpieces]

        return meshpieces, lod_meshpieces
    





