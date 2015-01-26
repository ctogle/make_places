import make_places.make_place as mp
import make_places.fundamental as fu
import make_places.scenegraph as sg
import make_places.blueprints as mbp
import make_places.gritty as gritgeo

import make_places.walls as wa
import make_places.newnewroads as nrds
import make_places.newterrain as mpt

import mp_utils as mpu
import mp_vector as cv
import mp_bboxes2 as mpbb2

import matplotlib.pyplot as plt


def problem():
    nwargs = {
        'v1':cv.vector(-10,10,0),
        'v2':cv.vector( 10,10,0),
        'm':'brick2','h':5.0,'w':0.25}
    nw = wa.newwall(**nwargs)
    nw._build()
    p = nw._primitives()

    no = sg.node(primitives = [p])
    nod = sg.node(
        consumes_children = False,
        children = [no])
    nod2 = sg.node(
        consumes_children = True,
        children = [nod])
        

    gritgeo.reset_world_scripts()
    #gritgeo.create_primitive(p)
    gritgeo.create_element(nod2)
    gritgeo.output_world_scripts()

#problem()


#mp.wall_speed_test()

#mp.ahouse()
#mp.profile_buildfew()

#mp.material_demo()
#mp.foliage_demo()

#mp.somestairs()
#mp.ashaft()
#mp.awall()
#mp.afloor()

#mp.profile_block()
mp.profile_city()
#mp.profile_hashima()

#mpt.test_fill()

#mp.terrain()




