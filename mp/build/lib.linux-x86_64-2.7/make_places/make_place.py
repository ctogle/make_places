import make_places.fundamental as fu
import mp_utils as mpu
import mp_bboxes as mpbb
import mp_vector as cv
import make_places.blueprints as bp
import make_places.scenegraph as sg
import make_places.primitives as pr
import make_places.waters as mpw
import make_places.cities as cities
import make_places.buildings as blg
import make_places.roads as roads
import make_places.newroads as newroads
import make_places.floors as floors
import make_places.walls as walls
import make_places.newterrain as nmpt
import make_places.profiler as prf

import make_places.gritty as gritgeo

import os
import numpy as np

import pdb

def ucube():
    gritgeo.reset_world_scripts()
    pcube = pr.ucube()
    #pcube.translate(cv.vector(10,0,0))
    gritgeo.create_primitive(pcube)
    gritgeo.output_world_scripts()

def uoctagon():
    gritgeo.reset_world_scripts()
    poct = pr.uoctagon()
    gritgeo.create_primitive(poct)
    gritgeo.output_world_scripts()

def ulineup():
    gritgeo.reset_world_scripts()
    pcube = pr.ucube()
    poct = pr.uoctagon()
    pcube.translate_x(1)
    poct.translate_x(-1)
    gritgeo.create_primitive(pcube,poct)
    gritgeo.output_world_scripts()

def cube_oct_elem(pos, scl, rot, children = []):
    uc = pr.ucube()
    uo = pr.uoctagon()
    uc.scale([2,2,3])
    uc.translate([1,0,0])
    uo.translate([-1,0,0])
    eprims = [uc, uo]
    #elem = fu.element(children = children, 
    elem = sg.node(children = children, 
        position = pos, scales = scl, 
        rotation = rot, primitives = eprims)
    return elem

def uelements():
    gritgeo.reset_world_scripts()
    el1 = cube_oct_elem([-2,-2,2], [2,2,1], [0,0,np.pi/2])
    el2 = cube_oct_elem([2,2,-2], [3,3,2], [0,0,3*(np.pi/2)])
    gritgeo.create_element(el1,el2)
    gritgeo.output_world_scripts()

def uelement_child():
    gritgeo.reset_world_scripts()
    el1 = cube_oct_elem([2,4,1], [1,2,2], [0,0,np.pi/2])
    el2 = cube_oct_elem([0,0,-1], [2,2,1], [0,0,np.pi/2], children = [el1])
    gritgeo.create_element(el2)
    gritgeo.output_world_scripts()

def intersection_g():
    gritgeo.reset_world_scripts()
    iarg = {
        'position':[10,10,0], 
        'road_width':30, 
        'road_height':5, 
            }
    elem = roads.intersection(**iarg)
    gritgeo.create_element(elem)
    gritgeo.output_world_scripts()

def roady():
    gritgeo.reset_world_scripts()
    r1 = {
        'start':[0,0,0], 
        'end':[0,100,10], 
        'directions':['north','south'],
        'road_height':2, 
        'road_width':20, 
            }
    rargs = [r1]
    gritgeo.create_element([roads.road(**rg) for rg in rargs])
    gritgeo.output_world_scripts()

def highway():
    gritgeo.reset_world_scripts()
    r1 = {
        'start':[0,0,0], 
        'end':[0,100,10], 
        'directions':['north','south'],
        'road_height':2, 
        'road_width':20, 
            }
    rargs = [r1]
    gritgeo.create_element([roads.highway(**rg) for rg in rargs])
    gritgeo.output_world_scripts()

def road_network():
    gritgeo.reset_world_scripts()
    rnarg = {}
    elem = roads.road_system(**rnarg)
    gritgeo.create_element(elem)
    gritgeo.output_world_scripts()

def road_network_terrain():
    gritgeo.reset_world_scripts()
    iargs = [{
        'position':[0,0,0], 
            }, {
        'position':[300,300,-10], 
            }, {
        'position':[150,300,20], 
            }, {
        'position':[150,450,-10], 
            }, {
        'position':[300,100,20], 
            }]
    rnarg = {
        'interargs':iargs, 
        'reuse':False, 
            }
    rsys = roads.road_system(**rnarg)
    trarg = {
        'splits':7,
        'smooths':2,
        'pts_of_interest':rsys.terrain_points(), 
        #'pts_of_interest':[], 
        'region_bounds':rsys.region_bounds, 
            }
    terra = terr.terrain(**trarg)
    gritgeo.create_element(rsys,terra)
    #gritgeo.create_element(terra)
    gritgeo.output_world_scripts()

def profile_road_network_terrain():
    prf.profile_function(road_network_terrain_g)

def afloor():
    gritgeo.reset_world_scripts()
    elem = floors.floor(position = cv.vector(0,0,0))
    pcube = pr.ucube()
    pcube.translate(cv.vector(10,2,5))
    gritgeo.create_element(elem)
    gritgeo.create_primitive(pcube)
    gritgeo.output_world_scripts()

def awall():
    gritgeo.reset_world_scripts()
    v1,v2 = cv.vector(10,10,0), cv.vector(50,30,0)
    v3,v4 = cv.vector( 0, 0,0), cv.vector( 0,30,0)
    wargs = {'gaped':False,'rid_top_bottom':False}
    w1 = walls.wall(v1,v2,**wargs)
    w2 = walls.wall(v3,v4,**wargs)
    gritgeo.create_element(w1,w2)
    gritgeo.output_world_scripts()

def abox():
    gritgeo.reset_world_scripts()
    fl = floors.floor(
        position = cv.vector(2,2,2),
        rotation = cv.vector(0,0,fu.PI/6.0))
    pe = walls.perimeter(floor = fl)
    elems = [fl,pe]
    gritgeo.create_element(elems)
    gritgeo.output_world_scripts()

def astory():
    gritgeo.reset_world_scripts()
    st = blg.story(1)
    pcube = pr.ucube()
    gritgeo.create_primitive(pcube)
    gritgeo.create_element(st)
    gritgeo.output_world_scripts()

def ashaft():
    gritgeo.reset_world_scripts()
    sh = blg.shaft()
    gritgeo.create_element(sh)
    gritgeo.output_world_scripts()

def someshafts():
    gritgeo.reset_world_scripts()
    sh1 = blg.shaft(position = [-10,0,0],direction = 'north')
    sh2 = blg.shaft(position = [10,0,0], direction = 'east')
    gritgeo.create_element(sh1,sh2)
    gritgeo.output_world_scripts()

def abox_el():
    fl = floors.floor(
        position = [20,0,5],
        rotation = [0,0,fu.PI/6.0])
    pe = walls.perimeter(floor = fl, gaped = True)
    elems = [fl,pe]
    no = sg.node(children = elems)
    return no

def tg():
    gritgeo.reset_world_scripts()

    st1 = blg.story(1, position = [0,-20,0], rotation = [0,0,fu.PI/3.0])
    st2 = blg.story(1, position = [-20,0,0], rotation = [0,0,fu.PI/3.0])
    stn = sg.node(position = [0,0,-5])
    stn.add_child(st2)
    ab = abox_el()
    built = blg.building(position = [0,20,-5], rotation = [0,0,fu.PI/12.0])
    poi = built.terrain_points()
    ter = terr.terrain(splits = 6, pts_of_interest = poi)
    
    pcube = pr.ucube()
    pcube.remove_face('top','front')

    pc = pr.ucube()
    pc.scale([10,10,10])
    pc.assign_material('ocean')

    gritgeo.create_primitive(pc)
    gritgeo.create_primitive(pcube)
    gritgeo.create_element(st1)
    gritgeo.create_element(stn)
    gritgeo.create_element(ab)
    gritgeo.create_element(built)
    gritgeo.create_element(ter)
    
    gritgeo.output_world_scripts()

def build():
    gritgeo.reset_world_scripts()
    built = blg.building()
    pcube = pr.ucube()
    gritgeo.create_element(built)
    gritgeo.create_primitive(pcube)
    gritgeo.output_world_scripts()

def buildfew():
    gritgeo.reset_world_scripts()
    ang = np.pi/6
    bargs = [{
        'position':cv.vector(10,50,10), 
        'length':40, 
        'width':40, 
            }, {
        'length':40, 
        'width':40, 
        'position':cv.vector(-10,-10,0), 
        'rotation':cv.vector(0,0,ang), 
            }]
    built = [blg.building(**ba) for ba in bargs]
    gritgeo.create_element(built)
    gritgeo.output_world_scripts()

def profile_buildfew():
    prf.profile_function(buildfew)

def block():
    gritgeo.reset_world_scripts()
    iargs = [{
        'position':cv.zero(), 
            }, {
        'position':cv.vector(0,300,-10), 
            }, {
        'position':cv.vector(300,100,10), 
            }]
    rsargs = {
        #'interargs':iargs, 
            }
    rsys = roads.road_system(**rsargs)
    rd = rsys.roads[1]
    bboxes = rd.get_bbox()
    b1 = {
        'name':'block1',
        'road':rd, 
        'bboxes':bboxes,
        'side':'right',
        'theme':'suburbs', 
            }
    b2 = {
        'road':rd, 
        'bboxes':bboxes,
        'side':'left',
            }
    bl1 = cities.block(**b1)
    bl2 = cities.block(**b2)
    pts_of_int =\
        rsys.terrain_points() +\
        bl1.terrain_points() +\
        bl2.terrain_points()
    ter = terr.terrain(smooths = 100, 
        pts_of_interest = pts_of_int, 
        splits = 7, bboxes = bboxes)
    
    ocean = mpw.waters(position = cv.vector(500,500,0),
        depth = 50,sealevel = -30.0,length = 2000,width = 2000)

    gritgeo.create_element(rsys,bl1,bl2,ter,ocean)

    gritgeo.output_world_scripts()

def profile_block():
    prf.profile_function(block)

def city():
    gritgeo.reset_world_scripts()
    cities.city()
    gritgeo.output_world_scripts()
    cities.plot_try_data()

def profile_city():
    prf.profile_function(city)

def add_prims():
    gritgeo.reset_world_scripts()
    p1 = pr.ucube()
    p1.translate([1,1,0])
    p2 = pr.ucube()
    p2.translate([-1,-1,0])
    p3 = p1 + p2
    gritgeo.create_primitive(p3)
    gritgeo.output_world_scripts()

def terrain():
    gritgeo.reset_world_scripts()
    ter = terr.terrain(splits = 8)
    gritgeo.create_element(ter)
    gritgeo.output_world_scripts()

def profile_terrain():
    prf.profile_function(terrain)

def newroadsys():
    gritgeo.reset_world_scripts()

    rsys = newroads.road_system_new()
    rsys.build()
    fixed_pts = rsys.terrain_points()

    targs = {
        'fixed_pts':fixed_pts,
        'hole_pts':[mpu.make_corners(cv.zero(),100,100,0)], 
        'region_pts':mpu.make_corners(cv.zero(),2000,2000,0), 
        'polygon_edge_length':20, 
        'primitive_edge_length':400, 
            }
    terr = nmpt.make_terrain(**targs)

    gritgeo.create_element(rsys)
    gritgeo.create_element(terr)
    gritgeo.output_world_scripts()

def profile_newroadsys():
    prf.profile_function(newroadsys)

def newterrain():
    gritgeo.reset_world_scripts()
    terr = nmpt.test()
    gritgeo.create_element(terr)
    gritgeo.output_world_scripts()
    
def profile_newterrain():
    prf.profile_function(newterrain)

def blgplan():
    gritgeo.reset_world_scripts()
    newblg = blg.building()
    #    position = cv.vector(10,10,-10), 
    #    rotation = cv.vector(0,0,fu.PI/3.0))
    pdb.set_trace()
    gritgeo.create_element(newblg)
    gritgeo.output_world_scripts()

def profile_blgplan():
    prf.profile_function(blgplan)

def bplan():
    gritgeo.reset_world_scripts()

    last = cv.vector(0,0,0)
    for x in range(3):
        plan = bp.floor_plan()
        pieces = plan.build()
        [p.translate(last) for p in pieces]
        gritgeo.create_element(pieces)
        last.z += 20.0

    gritgeo.output_world_scripts()

def bplans():
    gritgeo.reset_world_scripts()

    last = cv.vector(0,0,0)
    for x in range(3):
        outline = bp.outline_test(last)
        #outline = [o.to_list() for o in outline]
        pe = walls.perimeter(
            rid_top_bottom_walls = False, 
            gaped = False, corners = outline)
        gritgeo.create_element(pe)
        last.x += 25.0

    gritgeo.output_world_scripts()

def testlod():
    gritgeo.reset_world_scripts()
    
    p = cv.zero()
    l = 10
    w = 20

    pieces = []
    fargs = {
        'position':p.copy(), 
        'length':l,
        'width':w, 
            }
    pieces.append(floors.floor(**fargs))

    piece = pr.ucube(is_lod = True)
    piecenode = sg.node(
        position = p.copy().translate_z(-1.0), 
        scales = cv.vector(l,w,10), 
        lod_primitives = [piece])
    pieces.append(piecenode)

    no = sg.node(name = 'somenodename',
        children = pieces,consumes_children = True)

    gritgeo.create_element(no)
    gritgeo.output_world_scripts()







