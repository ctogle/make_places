import make_places.fundamental as fu
import make_places.scenegraph as sg
import make_places.blueprints as mbp
import make_places.walls as wa
import make_places.floors as fl

import mp_utils as mpu
import mp_vector as cv

#from make_places.scenegraph import node
#from make_places.floors import floor

import pdb

###############################################################################
stair_factory = stairs()
stair_factory._build()
def build_stairs(**buildopts):
    stair_factor._rebuild(**buildopts)
    return stair_factory._primitive_from_slice()

class stairs(blueprint):

    def __init__(self,steps = 5,l = 10,w = 4,h = 8):
        blueprint.__init__(self)
        self.steps = steps
        self.l = l
        self.w = w
        self.h = h

    def _rebuild(self,steps = None,l = None,w = None,h = None):
        bflag = False
        if not steps is None:
            self.steps = steps
            bflag = True
        if not l is None:
            self.l = l
            bflag = True
        if not w is None:
            self.w = w
            bflag = True
        if not h is None:
            self.h = h
            bflag = True
        if bflag: self._build()

    def _build(self):
        l,w,h = float(self.l),float(self.w),float(self.h)
        steps = self.steps
        stepheight = h/steps
        steplength = l/steps
        p = cv.zero()
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
        bottom = point_line(cv.zero(),cv.vector(0,l,h),blength,steps)
        for bdx in range(steps):
            bottom.insert(2*bdx+1,bottom[2*bdx+1].copy())
        cv.translate_coords_z(bottom[1:],-stepheight)
        bottomleft = [pt.copy().translate_x(-w/2.0) for pt in bottom] 
        bottomright = [pt.copy().translate_x(w/2.0) for pt in bottom] 

        self._bridge(topleft,topright,m = 'concrete')
        self._bridge(bottomleft,topleft,m = 'concrete')
        self._bridge(topright,bottomright,m = 'concrete')
        self._bridge(bottomright,bottomleft,m = 'concrete')
        
        self._assign_material('grass',slice(-4,-1))

        return self._primitive_from_slice()

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



class shaft_plan(mbp.blueprint):
    def __init__(self, position, **kwargs):
        self.position = position
        self._default_('floors',3,**kwargs)
        self._default_('floor_heights',[0.5]*self.floors,**kwargs)
        self._default_('ceiling_heights',[0.5]*self.floors,**kwargs)
        self._default_('wall_heights',[4.0]*self.floors,**kwargs)
        self._default_('length',8,**kwargs)
        self._default_('width',8,**kwargs)

    def build(self):
        pieces = []
        shargs = {
            'position':self.position.copy(), 
            'floor_heights':self.floor_heights, 
            'ceiling_heights':self.ceiling_heights, 
            'wall_heights':self.wall_heights, 
            'length':self.length, 
            'width':self.width, 
            'floors':self.floors, 
                }
        pieces.append(shaft(**shargs))
        return pieces

_ramp_count_ = 0
class ramp(fl.floor):

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

class shaft(sg.node):
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










