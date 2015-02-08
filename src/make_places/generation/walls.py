import make_places.fundamental as fu
import make_places.scenegraph as sg
import make_places.blueprints as mbp
import make_places.primitives as pr
import make_places.portals as po
import make_places.gritty as gritgeo

import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv

import matplotlib.pyplot as plt
import numpy as np
import random as rm

import pdb

class newwall(mbp.blueprint):

    def _plot(self,color = None):
        vs = [self.v1,self.v2]
        if color is None:
            if self.sort == 'interior':col = 'blue'
            else:col = 'red'
        else:col = color
        mbp.plot(vs,number = False,color = col,marker = 'o')

    def __init__(self,v1 = cv.zero(),v2 = cv.one(),
            h = 5.0,fh = 0.0,w = 0.5,m = 'brick2',
            sort = 'exterior',sector = None,
            unswitchable = False,solid = False,
            cap = False,cornered = None):
        mbp.blueprint.__init__(self)
        if cornered is None:
            if sort == 'exterior':cornered = True
            else:cornered = False
        self.unswitchable = unswitchable
        self.solid = solid
        self.cap = cap
        self.cornered = cornered

        self.v1 = v1
        self.v2 = v2
        self.h = h
        self.fh = fh
        self.w = w
        self.m = m
        self.sort = sort
        self.sector = sector
        self._update_endpoints()

        self._extra_primitives = []
        self._gaps = []
        self._portals = []

    def _rebuild(self,**opts):
        mbp.blueprint._rebuild(self,**opts)
        okeys = opts.keys()
        if 'v1' in okeys or 'v2' in okeys:
            self._update_endpoints()

    def _update_endpoints(self):
        v1,v2 = self.v1,self.v2
        self.l = cv.distance(v1,v2)
        self.center = cv.midpoint(v1,v2)
        self.tangent = cv.v1_v2(v1,v2).normalize()
        self.normal = self.tangent.copy()
        self.normal.rotate_z(fu.to_rad(90)).normalize()

        self._face_away()

    def _distance_to_border(self,border):

        def distance_to_edge(pt,e1,e2,norm):
            eproj = mpbb.project([e1,e2],norm)
            pproj = mpbb.project([pt],norm)
            return abs(eproj.x - pproj.x)

        edgenorms = mpbb.get_norms(border)
        pt = self.center 
        dists = []
        for edx in range(len(border)):
            e1 = border[edx-1]
            e2 = border[edx]
            norm = edgenorms[edx-1]
            dists.append(distance_to_edge(pt,e1,e2,norm))
            #dists.append(mpbb.distance_to_edge(pt,e1,e2))
        dists.append(dists.pop(0))
        distance = min(dists)
        return distance

    def _face_away(self,intpt = None):
        if intpt is None:
            if self.sector is None:return
            intpt = self.sector.center.copy()
        midpt = self.center.copy()
        tstpt = midpt.copy().translate(self.normal)
        if cv.distance(intpt,midpt) > cv.distance(intpt,tstpt):
            self.normal.flip()

        certain_tangent = cv.zhat.cross(self.normal)
        tstpt = midpt.copy().translate(certain_tangent)
        if cv.distance(self.v1,midpt) > cv.distance(self.v1,tstpt):
            v1 = self.v1
            self.v1 = self.v2
            self.v2 = v1
            self.v1v2 = cv.v1_v2(self.v1,self.v2)
            self.tangent = self.v1v2.copy().normalize()

    def _build(self):
        self._extra_primitives = []
        self._gaps = []
        self._portals = []

        if self.sort == 'exterior':self._build_exterior()
        elif self.sort == 'interior':self._build_interior()

        spts = []
        spts.append(self.v1)
        for g in self._gaps:spts.extend(g)
        spts.append(self.v2)

        self._build_segments(spts)
        self._build_portals()
        if self.cap:self._build_cap()
        if self.cornered:
            self._build_corner(self.v1)
            self._build_corner(self.v2)

    def _build_exterior(self):
        if self.solid or self.l < 6 or self.h < 3.0:return
        fh = self.fh
        if self.unswitchable:self._door_gap(0.5,self.fh)
        else:
            wlen = float(self.l)
            winw = 1.5
            gcnt = int(wlen/(winw*3))
            if gcnt % 2 != 0: gcnt -= 1
            if gcnt > 0: gspa = wlen/gcnt
            for gn in range(gcnt):
                #gp = (gn + 0.5)*gspa - winw/2.0
                gp = gn*gspa
                self._window_gap(gp/wlen,fh)

    def _build_interior(self):
        if self.solid or self.l < 6 or self.h < 3.0:return
        fh = self.fh
        self._door_gap(0.5,fh)

    def _gap(self,gx,gw):
        l,w = self.l,self.w
        t = self.tangent.copy().scale_u(gx*l)
        c = self.v1.copy().translate(t)
        tw = self.tangent.copy().scale_u(-0.5*gw)
        p1 = c.copy().translate(tw)
        p2 = c.copy().translate(tw.flip())
        gapped = self._add_gap(p1,p2)
        return gapped

    def _add_gap(self,g1,g2):
        def inside(x1,x2,x3):
            d12 = cv.distance(x1,x2)
            d13 = cv.distance(x1,x3)
            d23 = cv.distance(x2,x3)
            if d13 <= d12 and d23 <= d12:return True
            else:return False

        g1d = min([cv.distance(g1,self.v1),cv.distance(g1,self.v2)])
        g2d = min([cv.distance(g2,self.v1),cv.distance(g2,self.v2)])
        if g1d < 2 or g2d < 2: return None

        for g in self._gaps:
            og1,og2 = g
            if inside(og1,og2,g1) or inside(og1,og2,g2):
                return None
        
        self._gaps.append((g1,g2))
        return g1,g2

    def _window_gap(self,dx,fh):
        wh,winh = self.h,0.5*self.h
        dw,dh,dz = 0.75*winh,winh,max([(wh-winh)/2.0,fh+0.5])
        wpts = self._gap(dx,dw)
        if wpts is None:return
        wkws = {'z':dz,'w':dw,'h':dh,'gap':wpts,'wall':self}
        self._portals.append(po.window(**wkws))

    def _door_gap(self,dx,fh):
        wh,ch = self.h,self.fh
        dw,dh,dz = 1.5,mpu.clamp(0.8*(wh-fh-ch),2,3),fh
        dpts = self._gap(dx,dw)
        if dpts is None:return
        dkws = {'z':dz,'w':dw,'h':dh,'gap':dpts,'wall':self}
        self._portals.append(po.door(**dkws))

    def _build_portals(self):
        for p in self._portals:
            p._build()
            self._extra_primitives.append(p._primitive_from_slice())

    def _build_segments(self,spts):
        w = self.w
        scnt = len(spts)
        self.wnorm = self.normal.copy().scale_u(abs(w*0.5))
        for s in range(scnt)[::2]:
            s1,s2 = spts[s],spts[s+1]
            self._build_segment(s1,s2)

    def _build_segment(self,v1,v2):
        h,m,wnorm = self.h,self.m,self.wnorm.copy()
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

        #wcw = mbp.clockwise(bs)
        #if not wcw:
        #    bs.reverse()
        #    ts.reverse()
        #print 'w cw ness',wcw

        #mbp.plot(bs)
        #plt.show()

        nfs = self._bridge(bs,ts,m = m)
        #nfs = self._bridge(ts,bs,m = m)
        #self._flip_faces(nfs)
        self._project_uv_flat(nfs)

    def _build_corner(self,v):
        #cw,wh,m = abs(self.w*1.5),self.h,'concrete1'
        cw,wh,m = self.w*1.5,self.h,'concrete1'
        #cw,wh,m = w*1.5,self.h,self.m
        bl = mbp.ucube(m = m)
        bump = 0.5 if self.cap else 0.0
        bl.scale(cv.vector(cw,cw,wh+bump))
        #bl.calculate_normals()
        bl.translate(v)
        self._extra_primitives.append(bl)

    def _build_cap(self):
        h,m,wnorm = self.h,self.m,self.wnorm.copy().scale_u(1.25)
        v1,v2 = self.v1.copy().translate_z(h),self.v2.copy().translate_z(h)
        b1 = v1.copy().translate(wnorm.flip())
        b2 = v2.copy().translate(wnorm)
        b3 = v2.copy().translate(wnorm.flip())
        b4 = v1.copy().translate(wnorm)
        caph = 0.25
        t1 = b1.copy().translate_z(caph)
        t2 = b2.copy().translate_z(caph)
        t3 = b3.copy().translate_z(caph)
        t4 = b4.copy().translate_z(caph)
        bs = [b2,b3,t3,t2,b2]
        ts = [b1,b4,t4,t1,b1]
        nfs = self._bridge(ts,bs,m = 'concrete1')
        #nfs = self._bridge(ts,bs,m = m)
        #self._flip_faces(nfs)
        self._project_uv_flat(nfs)

wall_factory = newwall()
wall_factory._build()
def build_wall(**opts):
    wall_factory._rebuild(**opts)
    wp = wall_factory._primitive_from_slice()
    for p in wall_factory._extra_primitives:wp.consume(p)
    return wp

def test_wall_factory():
    bopts = {'v1':cv.vector(10,10,0),'v2':cv.vector(50,30,0),'h':10}
    wprim = build_wall(**bopts)
    gritgeo.create_primitive(wprim)
    print 'wall test'

def test_wall_speed(many = 20000):
    def newway(x):
        bopts = {
            'v1':v1.copy().translate_z(4*x),
            'v2':v2.copy().translate_z(4*x).rotate_z(fu.to_rad(15*x)),
            'h':4,'w':1}
        wprim = build_wall(**bopts)
        gritgeo.create_primitive(wprim)

    def oldway(x):
        c1 = v1.copy().translate_z(4*x)
        c2 = v2.copy().translate_z(4*x).rotate_z(fu.to_rad(15*x))
        nw = wall_plan(c1,c2, 
            sort = 'interior', 
            wall_height = 4,wall_width = 1)
        built = nw.build(solid = True)
        gritgeo.create_element(built)

    gritgeo.reset_world_scripts()

    v1 = cv.zero()
    v2 = v1.copy().translate_x(100)

    for x in range(many):
        newway(x)
        #oldway(x)

    gritgeo.output_world_scripts()




class wall_plan(mbp.blueprint):
    def __init__(self,v1,v2,sector = None,sort = 'exterior',**kwargs):
        self.sort = sort
        self.sector = sector
        self._default_('wall_width',0.5,**kwargs)
        self._default_('wall_height',4.0,**kwargs)
        self._default_('unswitchable',False,**kwargs)
        self.v1 = v1
        self.v2 = v2
        self.v1v2 = cv.v1_v2(v1,v2)
        self.center = cv.midpoint(v1,v2)
        self.lead_tip_rot = 0.0
        self.rear_tip_rot = 0.0
        self.length = self.v1v2.magnitude()
        self.normal = cv.cross(self.v1v2,cv.zhat).normalize()
        self.tangent = self.v1v2.copy().normalize()

    def distance_to_border(self, border):

        def distance_to_edge(pt,e1,e2,norm):
            eproj = mpbb.project([e1,e2],norm)
            pproj = mpbb.project([pt],norm)
            return abs(eproj.x - pproj.x)

        edgenorms = mpbb.get_norms(border)
        pt = self.center 
        dists = []
        for edx in range(len(border)):
            e1 = border[edx-1]
            e2 = border[edx]
            norm = edgenorms[edx-1]
            dists.append(distance_to_edge(pt,e1,e2,norm))
            #dists.append(mpbb.distance_to_edge(pt,e1,e2))
        dists.append(dists.pop(0))
        distance = min(dists)
        return distance

    def face_away(self):
        intpt = self.sector.position.copy()
        midpt = cv.midpoint(self.v1,self.v2)
        tstpt = midpt.copy().translate(self.normal)
        if cv.distance(intpt,midpt) > cv.distance(intpt,tstpt):
            self.normal.flip()

        certain_tangent = cv.zhat.cross(self.normal)
        tstpt = midpt.copy().translate(certain_tangent)
        if cv.distance(self.v1,midpt) > cv.distance(self.v1,tstpt):
            v1 = self.v1
            self.v1 = self.v2
            self.v2 = v1
            self.v1v2 = cv.v1_v2(self.v1,self.v2)
            self.tangent = self.v1v2.copy().normalize()

    def fill_windows(self, windows):
        filled = []
        for wo in windows:
            w1off = self.tangent.copy().scale_u(wo[0])
            w1 = self.v1.copy().translate(w1off)
            w2off = self.tangent.copy().scale_u(wo[1])
            w2 = w1.copy().translate(w2off)

            wheight = mpu.clamp(int(0.5*self.wall_height),2.0,5.0)
            woff = wheight/2.0 + 1.0

            bheight = woff - wheight/2.0
            bottom = wall(w1.copy(),w2.copy(),wall_height = bheight, 
                wall_width = self.wall_width,gaped = False,
                rid_top_bottom = False)

            hoff = woff + wheight/2.0
            hheight = self.wall_height - hoff
            w1.z += hoff 
            w2.z += hoff
            head = wall(w1,w2,wall_height = hheight,
                wall_width = self.wall_width,
                gaped = False,rid_top_bottom = False)

            filled.append(head)
            filled.append(bottom)
        return filled

    def fill_doors(self, doors):
        filled = []
        for do in doors:
            d1off = self.tangent.copy().scale_u(do[0])
            d1 = self.v1.copy().translate(d1off)
            d2off = self.tangent.copy().scale_u(do[1])
            d2 = d1.copy().translate(d2off)

            dheight = mpu.clamp(int(0.75*self.wall_height),3.0,5.0)
            hheight = self.wall_height - dheight
            hoff = dheight
            d1.z += hoff
            d2.z += hoff
            head = wall(d1,d2,wall_height = hheight,
                wall_width = self.wall_width, 
                rid_top_bottom = False,gaped = False)
            filled.append(head)
        return filled

    def build(self, solid = False, skirt = False, flh = 0.0, clh = 0.0):
        #print 'BUILD WALL!'

        wargs = {
            'rid_top_bottom':False,
            'wall_width':self.wall_width, 
            'wall_height':self.wall_height + flh + clh,
            'gaped':False, 
                }

        doorwidth = 3.0
        windowwidth = 3.0

        if solid:
            doors = []
            windows = []
        else:
            if self.sort == 'interior':
                if self.length > 2.0*doorwidth:
                    dpfa = rm.choice([0.25,0.5,0.75])
                    dpos = dpfa*self.length - doorwidth/2.0
                    doors = [[dpos,doorwidth]]
                else: doors = []
                windows = []
                doors.extend(windows)

            else:
                doors = []

                wlen = float(self.length)
                gcnt = int(wlen/(windowwidth*3))
                if gcnt % 2 != 0: gcnt -= 1
                windows = []
                if gcnt > 0: gspa = wlen/gcnt
                for gn in range(gcnt):
                    gp = (gn + 0.5)*gspa - windowwidth/2.0
                    windows.append((gp,windowwidth))
                doors.extend(windows)

            if self.unswitchable:
                doorwidth = 3.0
                dpos = 0.5*self.length - doorwidth/2.0
                doors.insert(gcnt/2,[dpos,doorwidth])

        wargs['gaps'] = doors
        v1 = self.v1.copy().translate_z(-flh)
        v2 = self.v2.copy().translate_z(-flh)

        pieces = [wall(v1,v2,**wargs)]
        pieces.extend(self.fill_doors(doors))
        pieces.extend(self.fill_windows(windows))
        if skirt:
            swargs = {
                'rid_top_bottom':False,
                'wall_width':self.wall_width, 
                'wall_height' : flh + clh, 
                'gaped': False, 
                    }
            sv1 = v1.copy().translate_z(-flh-clh)
            sv2 = v2.copy().translate_z(-flh-clh)
            pieces.append(wall(sv1,sv2,**swargs))
        return pieces

_wall_count_ = 0
class wall(sg.node):

    def get_name(self):
        global _wall_count_
        nam = 'wall ' + str(_wall_count_)
        _wall_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        self.v1 = args[0]
        self.v2 = args[1]
        v1, v2 = self.v1, self.v2
        #self.v1_v2 = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]
        self.v1_v2 = cv.v1_v2(v1,v2)
        self.angle = cv.angle_from_xaxis_xy(self.v1_v2)
        self._default_('rid_top_bottom',True,**kwargs)
        self._default_('length',cv.distance(v1,v2),**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        self._default_('wall_height',4,**kwargs)
        self._default_('gaps',[],**kwargs)
        try:
            if kwargs['gaped']:
                self.gaps = self.gape_wall()
        except KeyError: pass
        kwargs['primitives'] = self.make_primitives(
            self.v1, self.v1, self.v2, self.gaps)
        pos = self.v1.copy()
        kwargs['position'] = pos
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)
        sg.node.__init__(self, *args, **kwargs)
        wmat = 'brick2' if rm.random() < 0.5 else 'concrete1'
        self.assign_material(wmat)

    def gape_wall(self):
        wlen = float(self.length)
        gwid = 4.0
        gcnt = int(wlen/(gwid*2))
        #gcnt = 1 if wlen > gwid*2 else 0
        gaps = []
        if gcnt > 0: gspa = wlen/gcnt
        for gn in range(gcnt):
            gp = (gn + 0.5)*gspa - gwid/2.0
            gaps.append((gp,gwid))
        return gaps

    def make_wall_segment(self, pos, v1, v2, wall_scales):
        #wall_ = unit_cube()
        wall_ = mbp.ucube()
        if self.rid_top_bottom:
            wall_.remove_face('top','bottom')
        length = cv.distance_xy(v1,v2)
        wall_.scale(cv.vector(length, self.wall_width, self.wall_height))

        #wall_.scale_uvs(cv.one().scale_u(0.01))

        wall_.translate_x(length/2.0)
        wall_.rotate_z(self.angle)
        wall_.translate(pos)
        return wall_

    def make_primitives(self, pos, v1, v2, gaps = []):
        tang = self.v1_v2.copy().normalize()
        segmented = [v1, v2]
        wlength = cv.distance(v1,v2)
        wscls = cv.vector(wlength, self.wall_width, self.wall_height)
        for gap in gaps:
            cent = gap[0]
            #cent = gap[0]*wlength - 0.5*gap[1]

            widt = gap[1]
            nv1 = v1.copy()
            # start here
            nv1.translate(tang.copy().scale_u(cent))
            #cv.translate_vector(nv1, [t*cent for t in tang])
            nv2 = nv1.copy()
            nv2.translate(tang.copy().scale_u(widt))
            #mpu.translate_vector(nv2, [t*widt for t in tang])
            newvs = [nv1, nv2]
            segmented.extend(newvs)
            segmented.append(segmented.pop(-3))

        frnts = segmented[::2]
        backs = segmented[1::2]
        prims = []
        for sgdx in range(len(frnts)):
            fr = frnts[sgdx]
            bk = backs[sgdx]
            spos = cv.v1_v2(v1,fr)
            wall_ = self.make_wall_segment(spos, fr, bk, wscls)
            prims.append(wall_)
        return prims

_perim_count_ = 0
class perimeter(sg.node):
    
    def get_name(self):
        global _perim_count_
        nam = 'perimeter ' + str(_perim_count_)
        _perim_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        self._default_('name',self.get_name(),**kwargs)
        self._default_('floor',None,**kwargs)
        if self.floor: corns = self.floor.corners
        else: corns = kwargs['corners']
        self._default_('wall_offset',0,**kwargs)
        self._default_('rid_top_bottom_walls',True,**kwargs)
        corns = self.add_corner_offset(corns)
        self._default_('corners',corns,**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)
        self._default_('wall_width', 0.5, **kwargs)
        self._default_('wall_height', 4, **kwargs)
        self._default_('wall_gaps',[[],[],[],[]],**kwargs) 
        self._default_('gaped',True,**kwargs)
        self.gapes = [self.gaped]*len(self.wall_gaps)
        self.add_child(*self.make_walls(self.corners,
            gapes = self.gapes,gaps = self.wall_gaps))
        sg.node.__init__(self, *args, **kwargs)

    def add_corner_offset(self, cns):
        off = -self.wall_offset
        cns[0].x += off
        cns[0].y += off
        cns[1].x -= off
        cns[1].y += off
        cns[2].x -= off
        cns[2].y -= off
        cns[3].x += off
        cns[3].y -= off
        return cns

    def make_walls(self, corners, 
            gapes = [True,True,False,False], 
            gaps = [[],[],[],[]]):
        rid = self.rid_top_bottom_walls
        walls = []

        gcnt = len(gaps)
        ccnt = len(corners)
        if gcnt < ccnt:
            gaps.extend([[]]*(ccnt-gcnt))
            gapes.extend([False]*(ccnt-gcnt))

        ww = self.wall_width
        h = self.wall_height
        for cdx in range(1,ccnt):
            c1,c2 = corners[cdx-1],corners[cdx]
            walls.append(wall(c1, c2, rid_top_bottom = rid, 
                wall_width = ww, wall_height = h, 
                wall_gaps = gaps[cdx-1], gaped = gapes[cdx-1]))

        c1,c2 = corners[-1],corners[0]
        walls.append(wall(c1, c2, rid_top_bottom = rid, 
            wall_width = ww, wall_height = h, 
            wall_gaps = gaps[cdx], gaped = gapes[cdx]))
        return walls


      






