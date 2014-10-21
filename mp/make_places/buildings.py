from make_places.fundamental import element
import make_places.fundamental as fu
from make_places.stairs import ramp
from make_places.floors import floor
from make_places.walls import wall
from make_places.walls import perimeter

class story(element):

    def __init__(self, *args, **kwargs):
        self.floor_number = args[0]
        self._default_('shafts',[],**kwargs)
        self._default_('position',[0,0,0],**kwargs)
        self._default_('length',20,**kwargs)
        self._default_('width',20,**kwargs)
        self._default_('floor_height',1,**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        self._default_('wall_height',4.0,**kwargs)
        self._default_('ext_gaped',True,**kwargs)
        self.floor_ = self.make_floor(*args, **kwargs)
        ext_walls = self.make_exterior_walls(*args, **kwargs)
        #int_walls = self.make_interior_walls(*args, **kwargs)
        self.children = self.floor_ + ext_walls #+ int_walls
        element.__init__(self, *args, **kwargs)

    def make_floor(self, *args, **kwargs):
        gaps = []
        if self.floor_number > 0:
            for sh in self.shafts:
                gaps.extend(sh.floor_gaps)
        flpos = [0,0,0]
        flargs = {
            'position':flpos, 
            'length':self.length, 
            'width':self.width, 
            'gaps':gaps,
            'height':self.floor_height
                }
        floor_ = floor(**flargs)
        return [floor_]

    def make_exterior_walls(self, *args, **kwargs):
        #floor_pieces = kwargs['floor']
        floor_pieces = self.floor_
        peargs = [{
            'floor':fl, 
            'gaped':self.ext_gaped, 
            #'gaped':True, 
            'wall_height':self.wall_height, 
            'wall_width':self.wall_width, 
                } for fl in floor_pieces]
        perims = [perimeter(**pe) for pe in peargs]
        return perims

    def make_interior_walls(self, *args, **kwargs):
        comps = []
        kwargs['gaped'] = False
        for sh in self.shafts:
            topo = sh.topology[self.floor_number]
            entry = topo[0]
            shwg = sh.wall_gaps
            kwargs['wall_gaps'] = [
                shwg[0] if entry is 'front' else [],
                shwg[1] if entry is 'right' else [],
                shwg[2] if entry is 'back' else [],
                shwg[3] if entry is 'left' else [],
                ]
            shcorns = sh.corners
            kwargs['corners'] = shcorns
            comps.append(perimeter(**kwargs))
        return comps

class rooftop(story):

    def __init__(self, *args, **kwargs):
        self._default_('wall_height',1,{})
        self._default_('ext_gaped',False,**kwargs)
        story.__init__(self, *args, **kwargs)

class shaft(element):

    def __init__(self, *args, **kwargs):
        #self.building = kwargs['building']
        self._default_('position',[0,0,0],**kwargs)
        self._default_('length',10,**kwargs)
        self._default_('width',10,**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        self._default_('floor_height',0.5,**kwargs)
        self._default_('wall_height',4,**kwargs)
        self._default_('floors',2,**kwargs)
        self._default_('direction','north',**kwargs)
        l = self.length
        w = self.width
        self.corners = fu.find_corners(self.position, l, w)
        m = 0.25
        self.wall_gaps = [
            [[m,l-2*m]], 
            [[m,w-2*m]], 
            [[m,l-2*m]],
            [[m,w-2*m]],
                ]
        self.floor_gaps = [[self.position, l, w]]
        self.bottom = 0
        self.top = 'roof'
        ramps = self.ramps(*args, **kwargs)
        kwargs['children'] = ramps
        element.__init__(self, *args, **kwargs)

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

class building(element):

    def __init__(self, *args, **kwargs):
        self._default_('floors',5,**kwargs)
        self._default_('length',40,**kwargs)
        self._default_('width',30,**kwargs)
        self._default_('rotation',[0,0,0],**kwargs)
        self._default_('materials',['imgtex'],**kwargs)
        self._default_('wall_height',4,**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        self._default_('floor_height',1,**kwargs)
        self._default_('building_name','__abldg__',**kwargs)
        self._default_('roof_access',True,**kwargs)
        shafts = self.make_shafts(*args, **kwargs)
        self.shafts = shafts
        stories = self.make_floors_from_shafts(*args, **kwargs)
        self.children = shafts + stories
        element.__init__(self, *args, **kwargs)

    def make_shafts(self, *args, **kwargs):
        flcnt = self.floors
        if not self.roof_access: flcnt -= 1
        shargs = [{
            'position':[2,-1,0], 
            'rotation':[0,0,0], 
            'wall_height':self.wall_height, 
            'floor_height':self.floor_height, 
            'length':8, 
            'width':8, 
            'bottom':0, 
            'top':'roof',
            'floors':flcnt, 
                }]
        shafts = [shaft(**sh) for sh in shargs]
        return shafts

    def get_bbox(self, *args, **kwargs):
        cornas = self.find_corners()
        bb = fu.bbox(corners = cornas)
        return [bb]

    def find_corners(self):
        length = self.length
        width = self.width
        pos = [0,0,0]
        c1, c2, c3, c4 = pos[:], pos[:], pos[:], pos[:]
        c2[0] += length
        c3[0] += length
        c3[1] += width
        c4[1] += width
        corncoords = [c1, c2, c3, c4]
        corncoords = fu.rotate_z_coords(corncoords,self.rotation[2])
        fu.translate_coords(corncoords,self.position)
        return [c1, c2, c3, c4]

    def make_floors_from_shafts(self, *args, **kwargs):
        shafts = self.shafts
        bname = self.building_name
        bpos = [0,0,0]
        stheight = self.wall_height + self.floor_height
        ww = self.wall_width
        l,w = self.length,self.width

        floors = []
        flcnt = self.floors
        for fdx in range(flcnt):
            stname = bname + '_story_' + str(fdx)
            fl_pos = bpos[:]
            fl_pos[2] += stheight*fdx
            stargs = {
                'name':stname, 
                'position':fl_pos, 
                'shafts':shafts, 
                'length':self.length, 
                'width':self.width, 
                'wall_height':self.wall_height, 
                'wall_width':ww, 
                    }
            floors.append(story(fdx, **stargs))
        roof_name = bname + '_roof_'
        fl_pos = bpos[:]
        fl_pos[2] += stheight*(flcnt)
        rfarg = {
            'name':roof_name, 
            'position':fl_pos, 
            'length':self.length, 
            'width':self.width, 
            'shafts':shafts, 
            'wall_height':1, 
            'wall_width':ww, 
                }
        if self.roof_access:
            rfarg['gaps'] = []
            for sh in shafts:
                for gap in sh.floor_gaps:
                    topgap = gap[:]
                    rfarg['gaps'].append(topgap)
        roof = rooftop(flcnt - 1, **rfarg)
        floors.append(roof)
        return floors








