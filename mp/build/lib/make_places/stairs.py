import make_places.fundamental as fu
from make_places.scenegraph import node
from make_places.floors import floor

class ramp(floor):
    def __init__(self, *args, **kwargs):
        floor.__init__(self, *args, **kwargs)
        if self.gapped:
            print('failed to make ramp!!')
        else:
            prim = self.primitives[0]
            high_side = kwargs['high_side']
            differ = kwargs['differential']
            prim.translate_face([0,0,differ],high_side)

class shaft(node):

    def __init__(self, *args, **kwargs):
        #self.building = kwargs['building']
        #self._default_('position',[0,0,0],**kwargs)
        self._default_('length',10,**kwargs)
        self._default_('width',10,**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        self._default_('floor_height',0.5,**kwargs)
        self._default_('wall_height',4,**kwargs)
        self._default_('floors',2,**kwargs)
        self._default_('direction','north',**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        l = self.length
        w = self.width
        self.corners = fu.find_corners(self.tform.position, l, w)
        m = 0.25
        self.wall_gaps = [
            [[m,l-2*m]], 
            [[m,w-2*m]], 
            [[m,l-2*m]],
            [[m,w-2*m]],
                ]
        self.floor_gaps = [[self.tform.position, l, w]]
        self.bottom = 0
        self.top = 'roof'
        ramps = self.ramps(*args, **kwargs)
        kwargs['children'] = ramps
        node.__init__(self, *args, **kwargs)

    def ramps(self, *args, **kwargs):
        comps = []
        ww = self.wall_width
        floffset = self.floor_height + self.wall_height
        flcnt = self.floors
        topology = []

        def get_pos_fb(odd):
            bpos = [rl*odd-rl/2.0,0,0]
            return bpos, rl, rw

        def get_pos_rl(odd):
            bpos = [0,rw*odd-rw/2.0,0]
            return bpos, rl, rw

        if self.direction == 'east':
            sides = ['right','left']
            rw, rl = [4, 8]
            get_pos = get_pos_rl

        elif self.direction == 'north':
            sides = ['front','back']
            rw, rl = [8, 4]
            get_pos = get_pos_fb

        for fdx in range(flcnt):
            odd = fdx % 2
            rpos, rl, rw = get_pos(odd)
            rpos[2] += floffset * fdx
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






