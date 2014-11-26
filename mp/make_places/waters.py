import make_places.scenegraph as sg
import make_places.primitives as pr

class waters(sg.node):
    def __init__(self, *args, **kwargs):
        self._default_('length',100,**kwargs)
        self._default_('width',100,**kwargs)
        self._default_('sealevel',0.0,**kwargs)
        self._default_('depth',40.0,**kwargs)
        self.primitives = self.make_waters(*args,**kwargs)
        sg.node.__init__(self, *args, **kwargs)

    def make_waters(self, *args, **kwargs):
        wcube = pr.ucube()
        wcube.scale([self.length,self.width,self.depth])
        wcube.translate([0,0,self.sealevel-self.depth])
        wcube.assign_material('ocean')
        return [wcube]





