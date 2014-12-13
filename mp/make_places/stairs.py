import make_places.fundamental as fu
import make_places.walls as wa
import mp_utils as mpu
import mp_vector as cv
from make_places.scenegraph import node
from make_places.floors import floor

import pdb

_ramp_count_ = 0
class ramp(floor):

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

        floor.__init__(self, *args, **kwargs)
        if self.gapped:
            print('failed to make ramp!!')
        else:
            prim = self.primitives[0]
            high_side = kwargs['high_side']
            differ = kwargs['differential']
            prim.translate_face(cv.vector(0,0,differ),high_side)

class shaft(node):
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
        node.__init__(self, *args, **kwargs)

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
        platform = floor(**pargs)
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





class shaft_____old(node):

    def __init__(self, *args, **kwargs):
        self._default_('grit_renderingdistance',100.0,**kwargs)
        self._default_('consumes_children',True,**kwargs)
        self._default_('length',10.0,**kwargs)
        self._default_('width',10.0,**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        self._default_('floor_height',0.5,**kwargs)
        self._default_('ceiling_height',0.5,**kwargs)
        self._default_('wall_height',4,**kwargs)
        self._default_('floors',2,**kwargs)
        self._default_('direction','north',**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)
        l = self.length
        w = self.width
        self.corners = self.find_corners()
        #self.corners = fu.find_corners(self.tform.position, l, w)
        m = 0.25
        self.wall_gaps = [
            [[m,l-2*m]], 
            [[m,w-2*m]], 
            [[m,l-2*m]],
            [[m,w-2*m]],
                ]
        self.floor_gaps = [[self.tform.position, l, w]]
        self.bottom = -1
        self.top = 'roof'
        ramps = self.ramps(*args, **kwargs)
        self.add_child(*ramps)
        node.__init__(self, *args, **kwargs)

    def find_corners(self):
        pos = self.tform.position
        l,w = self.length,self.width
        return mpu.make_corners(pos,l,w,0)

        #c1,c2,c3,c4 = pos.copy(),pos.copy(),pos.copy(),pos.copy()
        #c2.x += l
        #c3.x += l
        #c3.y += w
        #c4.y += w
        #return [c1,c2,c3,c4]

    def ramps(self, *args, **kwargs):
        comps = []
        ww = self.wall_width
        floffset = self.wall_height+self.floor_height+self.ceiling_height
        flcnt = self.floors
        topology = []

        def get_pos_fb(odd):
            bpos = cv.vector(rl*odd-rl/2.0,0.0,0.0)
            return bpos, rl, rw

        def get_pos_rl(odd):
            bpos = cv.vector(0.0,rw*odd-rw/2.0,0.0)
            return bpos, rl, rw

        if self.direction == 'east':
            sides = ['right','left']
            rw, rl = [4.0, 8.0]
            get_pos = get_pos_rl

        elif self.direction == 'north':
            sides = ['front','back']
            rw, rl = [8.0, 4.0]
            get_pos = get_pos_fb

        for fdx in range(flcnt):
            odd = fdx % 2.0
            rpos, rl, rw = get_pos(odd)
            rpos.z += floffset * fdx
            lside = sides[0] if odd else sides[1]
            hside = sides[1] if odd else sides[0]
            rparg = {
                'parent':self,
                'position':rpos, 
                'length':rl, 
                'width':rw, 
                'high_side':hside, 
                'differential':floffset, 
                    }
            topology.append((lside,hside))
            ramp_ = ramp(**rparg)
            comps.append(ramp_)
        self.topology = topology
        return comps






