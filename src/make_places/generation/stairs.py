import make_places.core.fundamental as fu
import make_places.core.primitives as pr
import make_places.core.scenegraph as sg
import make_places.core.blueprints as mbp
import make_places.io.gritty as gritgeo

import make_places.generation.walls as wa
import make_places.generation.floors as fl

import mp_utils as mpu
import mp_vector as cv

from math import sqrt

import pdb



###############################################################################

class stairs(mbp.blueprint):

    def __init__(self,steps = 8,p = None,l = 10,w = 4,h = 8,m = 'gridmat'):
        mbp.blueprint.__init__(self)
        self.steps = steps
        self.p = p
        self.l = l
        self.w = w
        self.h = h
        self.m = m

    def _build(self):
        l,w,h = float(self.l),float(self.w),float(self.h)
        steps = self.steps
        stepheight = h/steps
        steplength = l/steps

        #print 'stepheight',stepheight,h

        if self.p is None:p = cv.zero()
        else:p = self.p.copy()
        line = []
        for sx in range(steps):
            line.append(p.copy())
            p.translate_z(stepheight)
            line.append(p.copy())
            p.translate_y(steplength)
        line.append(p.copy())

        topleft = [pt.copy().translate_x(-w/2.0) for pt in line] 
        topright = [pt.copy().translate_x(w/2.0) for pt in line] 
        blength = sqrt(l**2 + h**2)
        bottom = mbp.point_line(cv.zero(),cv.vector(0,l,h),blength,steps)
        for bdx in range(steps):
            bottom.insert(2*bdx+1,bottom[2*bdx+1].copy())
        cv.translate_coords_z(bottom[1:],-stepheight)
        bottomleft = [pt.copy().translate_x(-w/2.0) for pt in bottom] 
        bottomright = [pt.copy().translate_x(w/2.0) for pt in bottom] 
        nfs = []
        nfs.extend(self._bridge(topleft,topright,m = self.m))
        nfs.extend(self._bridge(bottomleft,topleft,m = self.m))
        nfs.extend(self._bridge(topright,bottomright,m = self.m))
        nfs.extend(self._bridge(bottomright,bottomleft,m = self.m))
        self._project_uv_flat(nfs)

stair_factory = stairs()
stair_factory._build()
def build_stairs(**buildopts):
    stair_factory._rebuild(**buildopts)
    return stair_factory._primitive_from_slice()

def test_stair_factory():
    bopts = {'steps':10,'l':10,'w':4,'h':8}
    sprim1 = build_stairs(**bopts)
    sprim2 = build_stairs(**bopts)
    sprim3 = build_stairs(**bopts)
    sprim2.translate_x(-10.0)
    sprim3.translate_x( 10.0)
    stairnode = sg.node(primitives = [sprim1,sprim2,sprim3])
    gritgeo.create_element(stairnode)
    print 'stair test'

###############################################################################

class shaft(mbp.blueprint):

    def _rebuild(self,**opts):
        mbp.blueprint._rebuild(self,**opts)
        extra = self.floors - len(self.flheights)
        if extra > 0:
            lflh = self.flheights[-1]
            self.flheights.extend([lflh]*extra)
            lwah = self.waheights[-1]
            self.waheights.extend([lwah]*extra)
            lclh = self.clheights[-1]
            self.clheights.extend([lclh]*extra)
        self.toheights = self.waheights
        #self.toheights = [x+y+z for x,y,z in
        #    zip(self.flheights,self.waheights,self.clheights)]

    def __init__(self,floors = 3,l = 12,w = 16,
            flheights = None,clheights = None,waheights = None):
        mbp.blueprint.__init__(self)
        self.floors = floors
        self.l = l
        self.w = w
        if flheights is None:self.flheights = [0.5]*self.floors
        else:self.flheights = flheights
        if clheights is None:self.clheights = [0.5]*self.floors
        else:self.clheights = clheights
        if waheights is None:self.waheights = [5.0]*self.floors
        else:self.waheights = waheights
        self.toheights = waheights
        #self.toheights = [x+y+z for x,y,z in
        #    zip(self.flheights,self.waheights,self.clheights)]
        self.style = 'uturn'

    def _params(self,fldex):
        fh = self.flheights[fldex]
        wh = self.waheights[fldex]
        ch = self.clheights[fldex]
        l,w = self.l,self.w
        return l,w,fh,wh,ch

    def _build_walls(self,fldex):
        l,w,fh,wh,ch = self._params(fldex)
        cs = mpu.make_corners(cv.zero(),l,w,0)
        wargs = [
            {'v1':cs[1],'v2':cs[2], 
            'solid':True,'m':'brick2',
            'h':wh,'fh':fh,'w':0.25}, 
            {'v1':cs[2],'v2':cs[3], 
            'solid':True,'m':'brick2',
            'h':wh,'fh':fh,'w':0.25}, 
            {'v1':cs[3],'v2':cs[0], 
            'solid':True,'m':'brick2',
            'h':wh,'fh':fh,'w':0.25},
            {'v1':cs[0],'v2':cs[1],
            'sort':'interior','solid':False,'m':'brick2',
            'h':wh,'fh':fh,'w':0.25}]
        wals = [wa.newwall(**w) for w in wargs]
        [w._face_away(cv.zero()) for w in wals]
        [w._build() for w in wals]
        return pr.sum_primitives([w._primitives() for w in wals])

    def _build_uturn(self,fldex):
        fh = self.flheights[fldex]
        wh = self.waheights[fldex]
        ch = self.clheights[fldex]
        l,w = self.l,self.w

        p1h = fh;p1l = l;p1w = 3.0
        p1x = 0.0;p1y = (p1w - w)/2.0;p1z = 0
        pform1 = mbp.ucube(m = 'cement1')
        pform1.scale(cv.vector(p1l,p1w,p1h))
        pform1.translate(cv.vector(p1x,p1y,p1z))

        p2h = ch;p2l = l;p2w = 3.0
        p2x = 0.0;p2y = (p2w - w)/2.0;p2z = wh - ch
        pform2 = mbp.ucube(m = 'cement1')
        pform2.scale(cv.vector(p2l,p2w,p2h))
        pform2.translate(cv.vector(p2x,p2y,p2z))

        gap = l/5.0
        s = int(wh)
        rw = 2.0*gap
        rl = w - 2.0*p1w
        diff = wh/2.0
        rwoffx = l/2.0 - rw/2.0
        rwoffy = rl/2.0
        sheight = diff/s

        p3h = 2.0*sheight;p3l = l;p3w = 3.0
        p3x = 0.0;p3y = (w - p3w)/2.0;p3z = diff-sheight
        pform3 = mbp.ucube(m = 'cement1')
        pform3.scale(cv.vector(p3l,p3w,p3h))
        pform3.translate(cv.vector(p3x,p3y,p3z))

        extra = mbp.ucube(m = 'brick2')
        extra.scale(cv.vector(gap,rl,wh))
        extra.translate(cv.vector(0,0,0))
        pform1.consume(extra)

        sopts1 = {'bflag':True,'steps':s,'l':rl,'w':rw,'h':diff,'m':'cement1'}
        sopts2 = {'bflag':True,'steps':s,'l':rl,'w':rw,'h':diff,'m':'cement1'}
        lside = build_stairs(**sopts1)
        rside = build_stairs(**sopts2)
        lside.rotate_z(fu.PI).translate_y(rl).translate_z(diff)
        lside.translate_x(-rwoffx).translate_y(-rwoffy).translate_z(fh-sheight)
        rside.translate_x( rwoffx).translate_y(-rwoffy).translate_z(fh-sheight)
        pr.sum_primitives([pform1,pform2,pform3,lside,rside])
        return pform1

    def _build_switchback(self,fldex):
        floor = pr.empty_primitive()
        pdb.set_trace()
        return floor

    def _build_floor(self,fldex):
        style = self.style
        if style == 'uturn':
            floor = self._build_uturn(fldex)
        elif style == 'switchback':
            floor = self._build_switchback(fldex)
        floor.consume(self._build_walls(fldex))
        return floor

    def _primitive_from_slice(self):
        fp = pr.empty_primitive()
        zoff = 0.0
        for fx in range(self.floors):
            np = self._build_floor(fx)
            np.translate_z(zoff)
            fp.consume(np)
            zoff += self.toheights[fx]
            #print 'zoff',zoff
        #fp.translate_y(-self.w/2.0)
        #fp.translate_z(-self.ph)

        fp.consume(mbp.ucube())

        return fp

shaft_factory = shaft()
shaft_factory._build()
def build_shaft(**buildopts):
    shaft_factory._rebuild(**buildopts)
    return shaft_factory._primitive_from_slice()

def test_shaft_factory():
    bopts = {'floors':5,'l':10,'w':16}
    sprim1 = build_shaft(**bopts)
    shaftnode = sg.node(primitives = [sprim1])
    gritgeo.create_element(shaftnode)
    print 'shaft test'

###############################################################################









_ramp_count_ = 0
#class ramp(fl.floor):
class ramp(sg.node):

    def get_name(self):
        global _ramp_count_
        nam = 'ramp ' + str(_ramp_count_)
        _ramp_count_ += 1
        return nam
        
    def __init__(self, *args, **kwargs):
        self._default_('name',self.get_name(),**kwargs)
        self._default_('length',8,**kwargs)
        self._default_('width',4,**kwargs)

        if kwargs['high_side'] in ['front','back']:
            l = self.length
            self.length = self.width
            self.width = l

        fl.floor.__init__(self, *args, **kwargs)
        if self.gapped:
            print('failed to make ramp!!')
        else:
            prim = self.primitives[0]
            high_side = kwargs['high_side']
            differ = kwargs['differential']
            #prim.translate_face(cv.vector(0,0,differ),high_side)

class shaftold(sg.node):
    def __init__(self, *args, **kwargs):
        self._default_('grit_renderingdistance',100.0,**kwargs)
        self._default_('consumes_children',True,**kwargs)
        self._default_('length',10.0,**kwargs)
        self._default_('width',10.0,**kwargs)
        self._default_('floors',2,**kwargs)
        self._default_('basements',1,**kwargs)
        self._default_('floor_heights',[0.5]*self.floors,**kwargs)
        self._default_('ceiling_heights',[0.5]*self.floors,**kwargs)
        self._default_('wall_heights',[4.0]*self.floors,**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        #self._default_('direction','north',**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)
        self.corners = self.find_corners()
        ramps = self.ramps(*args, **kwargs)
        self.add_child(*ramps)
        sg.node.__init__(self, *args, **kwargs)

    def find_corners(self):
        pos = self.tform.position
        l,w = self.length,self.width
        return mpu.make_corners(pos,l,w,0)

    def build_uturn(self, fpos, flh, clh, wh, inside, outside):
        pieces = []
        rw = 4
        platformwidth = 4.0
        rl = self.width - platformwidth
        diff = (wh + flh + clh)/2.0
        rwoff = self.length/2.0 - rw/2.0
        r1pos = fpos.copy()
        r1pos.translate_x(rwoff).translate_y(-platformwidth/2.0)
        rparg = {
            'parent':self,
            'position':r1pos, 
            'length':rl, 
            'width':rw, 
            'high_side':'back', 
            'differential':diff, 
                }
        ramp1 = ramp(**rparg)
        r2pos = fpos.copy().translate_z(diff)
        r2pos.translate_x(-rwoff).translate_y(-platformwidth/2.0)
        rparg['position'] = r2pos
        rparg['high_side'] = 'front'
        ramp2 = ramp(**rparg)
        flpos = fpos.copy().translate_z(diff)
        flpos.translate_y(self.width/2.0 - platformwidth/2.0)
        pargs = {
            'position':flpos, 
            'length':self.length, 
            'width':platformwidth, 
                }
        platform = fl.floor(**pargs)
        pieces.append(ramp1)
        pieces.append(ramp2)
        pieces.append(platform)

        c1,c2,c3,c4 = mpu.make_corners(fpos,self.length,self.width,0)
        cpairs = [(c2,c3),(c3,c4),(c4,c1)]
        walls = [wa.wall(*cp,wall_height = wh, 
            wall_width = self.wall_width,gaped = False,
            rid_top_bottom = False) for cp in cpairs] 
        pieces.extend(walls)

        return pieces

    def build_floor(self, fpos, flh, clh, wh, inside, outside):
        pieces = []
        # currently assuming inside == 0

        if inside == outside: # uturn
            pieces.extend(self.build_uturn(
                fpos, flh, clh, wh, inside, outside))
            
        elif abs(inside - outside) == 2: # switchback
            print 'waaaaait'
            pdb.set_trace()

        return pieces

    def ramps(self, *args, **kwargs):
        comps = []

        spos = cv.zero()
        flcnt = self.floors
        for fdx in range(flcnt):
            flh = self.floor_heights[fdx]
            clh = self.ceiling_heights[fdx]
            wh = self.wall_heights[fdx]
            shoff = flh + clh + wh
            rparg = (spos.copy(),flh,clh,wh,0,0)
            comps.extend(self.build_floor(*rparg))
            spos.z += shoff

        spos = cv.zero()   
        flcnt = self.floors
        for fdx in range(flcnt):
            flh = self.floor_heights[fdx]
            clh = self.ceiling_heights[fdx]
            wh = self.wall_heights[fdx]
            shoff = flh + clh + wh
            rparg = (spos.copy(),flh,clh,wh,0,0)
            comps.extend(self.build_floor(*rparg))
            spos.z += shoff

        return comps










