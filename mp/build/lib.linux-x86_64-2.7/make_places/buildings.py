#from make_places.fundamental import element
from make_places.scenegraph import node
import make_places.fundamental as fu
from make_places.stairs import ramp
from make_places.stairs import shaft
from make_places.floors import floor
from make_places.walls import wall
from make_places.walls import perimeter

class story(node):

    def __init__(self, *args, **kwargs):
        self.floor_number = args[0]
        self._default_('shafts',[],**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
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
        node.__init__(self, *args, **kwargs)

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
            'height':self.floor_height, 
            'parent':self, 
                }
        floor_ = floor(**flargs)
        return [floor_]

    def make_exterior_walls(self, *args, **kwargs):
        #floor_pieces = kwargs['floor']
        floor_pieces = self.floor_
        peargs = [{
            'parent':fl, 
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
            kwargs['parent'] = self
            comps.append(perimeter(**kwargs))
        return comps

class rooftop(story):

    def __init__(self, *args, **kwargs):
        self._default_('wall_height',1,{})
        self._default_('ext_gaped',False,**kwargs)
        story.__init__(self, *args, **kwargs)

class building(node):

    def __init__(self, *args, **kwargs):
        self._default_('floors',5,**kwargs)
        self._default_('length',40,**kwargs)
        self._default_('width',30,**kwargs)
        self._default_('tform',
            self.def_tform(*args,**kwargs),**kwargs)
        #self._default_('rotation',[0,0,0],**kwargs)
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
        node.__init__(self, *args, **kwargs)

    def make_shafts(self, *args, **kwargs):
        flcnt = self.floors
        if not self.roof_access: flcnt -= 1
        shargs = [{
            'parent':self, 
            'position':[0,0,0], 
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
        c1[0] -= length/2.0
        c1[1] -= width/2.0
        c2[0] += length/2.0
        c2[1] -= width/2.0
        c3[0] += length/2.0
        c3[1] += width/2.0
        c4[0] -= length/2.0
        c4[1] += width/2.0
        corncoords = [c1, c2, c3, c4]
        zang = self.tform.rotation[2]
        corncoords = fu.rotate_z_coords(corncoords,zang)
        fu.translate_coords(corncoords,self.tform.position)
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
                'parent':self, 
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
            'parent':self, 
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







