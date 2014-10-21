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






