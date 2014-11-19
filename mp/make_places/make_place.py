import make_places.fundamental as fu
import make_places.scenegraph as sg
import make_places.primitives as pr
import make_places.cities as cities
import make_places.buildings as blg
import make_places.roads as roads
import make_places.floors as floors
import make_places.walls as walls
import make_places.terrain as terr
import make_places.profiler as prf

import make_places.blend_in as blgeo
import make_places.gritty as gritgeo

import os
import numpy as np

def ucube_b():
    pcube = pr.ucube()
    blgeo.create_primitive(pcube)

def ucube_g():
    gritgeo.reset_world_scripts()
    pcube = pr.ucube()
    gritgeo.create_primitive(pcube)
    gritgeo.output_world_scripts()

def uoctagon_b():
    poct = pr.uoctagon()
    blgeo.create_primitive(poct)

def uoctagon_g():
    gritgeo.reset_world_scripts()
    poct = pr.uoctagon()
    gritgeo.create_primitive(poct)
    gritgeo.output_world_scripts()

def ulineup_b():
    pcube = pr.ucube()
    poct = pr.uoctagon()
    pcube.translate([1,0,0])
    poct.translate([-1,0,0])
    blgeo.create_primitive(pcube,poct)

def ulineup_g():
    gritgeo.reset_world_scripts()
    pcube = pr.ucube()
    poct = pr.uoctagon()
    pcube.translate([1,0,0])
    poct.translate([-1,0,0])
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

def uelements_b():
    el1 = cube_oct_elem([-2,-2,2], [2,2,1], [0,0,np.pi/2])
    el2 = cube_oct_elem([2,2,-2], [3,3,2], [0,0,3*(np.pi/2)])
    blgeo.create_element(el1,el2)

def uelements_g():
    gritgeo.reset_world_scripts()
    el1 = cube_oct_elem([-2,-2,2], [2,2,1], [0,0,np.pi/2])
    el2 = cube_oct_elem([2,2,-2], [3,3,2], [0,0,3*(np.pi/2)])
    gritgeo.create_element(el1,el2)
    gritgeo.output_world_scripts()

def uelement_child_b():
    el1 = cube_oct_elem([2,4,1], [1,2,2], [0,0,np.pi/6])
    el2 = cube_oct_elem([0,0,-1], [2,2,1], [0,0,np.pi/2], children = [el1])
    blgeo.create_element(el2)

def uelement_child_g():
    gritgeo.reset_world_scripts()
    el1 = cube_oct_elem([2,4,1], [1,2,2], [0,0,np.pi/2])
    el2 = cube_oct_elem([0,0,-1], [2,2,1], [0,0,np.pi/2], children = [el1])
    gritgeo.create_element(el2)
    gritgeo.output_world_scripts()

def intersection_b():
    iarg = {
        'position':[10,10,0], 
        'road_width':30, 
        'road_height':5, 
            }
    elem = roads.intersection(**iarg)
    blgeo.create_element(elem)

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

def roady_b():
    r1 = {
        'start':[0,0,0], 
        'end':[0,100,10], 
        'directions':['north','south'],
        'road_height':2, 
        'road_width':20, 
            }
    rargs = [r1]
    blgeo.create_element([roads.road(**rg) for rg in rargs])

def roady_g():
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

def highway_g():
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

def road_network_b():
    rnarg = {}
    elem = roads.road_system(**rnarg)
    blgeo.create_element(elem)

def road_network_g():
    gritgeo.reset_world_scripts()
    rnarg = {}
    elem = roads.road_system(**rnarg)
    gritgeo.create_element(elem)
    gritgeo.output_world_scripts()

def road_network_terrain_b():
    iargs = [{
        'position':[0,0,0], 
            }, {
        'position':[300,300,-10], 
            }, {
        'position':[150,300,20], 
            }, {
        'position':[150,450,-10], 
            }, {
        'position':[300,100,10], 
            }]
    rnarg = {
        'interargs':iargs, 
        'reuse':False, 
            }
    rsys = roads.road_system(**rnarg)
    trarg = {
        'splits':8,
        'smooths':5,
        'pts_of_interest':rsys.terrain_points(), 
        #'pts_of_interest':[], 
        'region_bounds':rsys.region_bounds, 
        #'bboxes':
            }
    terra = terr.terrain(**trarg)
    blgeo.create_element(rsys,terra)

def road_network_terrain_g():
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

def profile_road_network_terrain_b():
    prf.profile_function(road_network_terrain_b)

def profile_road_network_terrain_g():
    prf.profile_function(road_network_terrain_g)

def afloor_b():
    elem = floors.floor()
    blgeo.create_element(elem)

def afloor_g():
    gritgeo.reset_world_scripts()
    elem = floors.floor()
    pcube = pr.ucube()
    gritgeo.create_primitive(pcube)
    gritgeo.create_element(elem)
    gritgeo.output_world_scripts()

def awall_b():
    v1,v2 = [10,10,0], [50,30,0]
    v3,v4 = [0,0,0], [0,30,0]
    w1 = walls.wall(v1,v2)
    w2 = walls.wall(v3,v4,gaped = True)
    blgeo.create_element(w1,w2)

def awall_g():
    gritgeo.reset_world_scripts()
    v1,v2 = [10,10,0], [50,30,0]
    v3,v4 = [0,0,0], [0,30,0]
    w1 = walls.wall(v1,v2)
    w2 = walls.wall(v3,v4,gaped = True)
    gritgeo.create_element(w1,w2)
    gritgeo.output_world_scripts()

def abox_b():
    fl = floors.floor()
    pe = walls.perimeter(floor = fl)
    elems = [fl,pe]
    blgeo.create_element(elems)

def abox_g():
    gritgeo.reset_world_scripts()
    fl = floors.floor(
        position = [2,2,2],
        rotation = [0,0,fu.PI/6.0])
    pe = walls.perimeter(floor = fl)
    elems = [fl,pe]
    gritgeo.create_element(elems)
    gritgeo.output_world_scripts()

def astory_b():
    st = blg.story(1, position = [1,1,1])
    blgeo.create_element(st)

def astory_g():
    gritgeo.reset_world_scripts()
    st = blg.story(1)
    pcube = pr.ucube()
    gritgeo.create_primitive(pcube)
    gritgeo.create_element(st)
    gritgeo.output_world_scripts()

def ashaft_b():
    sh = blg.shaft()
    blgeo.create_element(sh)

def ashaft_g():
    gritgeo.reset_world_scripts()
    sh = blg.shaft()
    gritgeo.create_element(sh)
    gritgeo.output_world_scripts()

def someshafts_b():
    sh1 = blg.shaft(position = [-10,0,0],direction = 'north')
    sh2 = blg.shaft(position = [10,0,0], direction = 'east')
    blgeo.create_element(sh1,sh2)

def someshafts_g():
    gritgeo.reset_world_scripts()
    sh1 = blg.shaft(position = [-10,0,0],direction = 'north')
    sh2 = blg.shaft(position = [10,0,0], direction = 'east')
    blgeo.create_element(sh1,sh2)
    gritgeo.output_world_scripts()

def abox():
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
    ab = abox()
    built = blg.building(position = [0,20,-5], rotation = [0,0,fu.PI/12.0])
    
    pcube = pr.ucube()

    gritgeo.create_primitive(pcube)
    gritgeo.create_element(st1)
    gritgeo.create_element(stn)
    gritgeo.create_element(ab)
    gritgeo.create_element(built)
    
    gritgeo.output_world_scripts()

def build_b():
    built = blg.building()
    blgeo.create_element(built)

def build_g():
    gritgeo.reset_world_scripts()
    built = blg.building()
    pcube = pr.ucube()
    gritgeo.create_element(built)
    gritgeo.create_primitive(pcube)
    gritgeo.output_world_scripts()

def buildfew_b():
    ang = np.pi/24
    bargs = [{
        'position':[10,50,10], 
            }, {
        'position':[-10,-10,0], 
        'rotation':[0,0,ang], 
            }]
    built = [blg.building(**ba) for ba in bargs]
    blgeo.create_element(built)

def buildfew_g():
    gritgeo.reset_world_scripts()
    ang = np.pi/6
    bargs = [{
        'position':[10,50,10], 
            }, {
        'position':[-10,-10,0], 
        'rotation':[0,0,ang], 
            }]
    built = [blg.building(**ba) for ba in bargs]
    gritgeo.create_element(built)
    gritgeo.output_world_scripts()

def profile_buildfew_g():
    prf.profile_function(buildfew_g)

def block_b():
    iargs = [{
        'position':[0,0,0], 
            }, {
        'position':[0,300,-10], 
            }, {
        'position':[300,100,10], 
            }]
    rsargs = {
        'interargs':iargs, 
            }
    rsys = roads.road_system(**rsargs)
    rd = rsys.roads[1]
    b1 = {
        'road':rd, 
        'bboxes':rd.get_bbox(),
        'side':'right',
            }
    b2 = {
        'road':rd, 
        'bboxes':rd.get_bbox(),
        'side':'left',
            }
    bl1 = cities.block(**b1)
    bl2 = cities.block(**b2)
    blgeo.create_element(rsys,bl1,bl2)

def block_g():
    gritgeo.reset_world_scripts()
    iargs = [{
        'position':[0,0,0], 
            }, {
        'position':[0,300,-10], 
            }, {
        'position':[300,100,10], 
            }]
    rsargs = {
        'interargs':iargs, 
            }
    rsys = roads.road_system(**rsargs)
    rd = rsys.roads[1]
    b1 = {
        'name':'block1',
        'road':rd, 
        'bboxes':rd.get_bbox(),
        'side':'right',
        #'reuse':True,
            }
    b2 = {
        'road':rd, 
        'bboxes':rd.get_bbox(),
        'side':'left',
            }
    bl1 = cities.block(**b1)
    bl2 = cities.block(**b2)
    pts_of_int =\
        rsys.terrain_points() +\
        bl1.terrain_points() +\
        bl2.terrain_points()
    corners = [[0,0,0],[200,0,0],[200,200,0],[0,200,0]]
    bboxes = [fu.bbox(corners = corners)]
    bboxes = rsys.get_bbox() + bl1.get_bbox() + bl2.get_bbox()
    ter = terr.terrain(
        pts_of_interest = pts_of_int, 
        splits = 5, bboxes = bboxes)
    #gritgeo.create_element(rsys,bl1)
    gritgeo.create_element(rsys,bl1,bl2,ter)
    gritgeo.output_world_scripts()

def profile_block_b():
    prf.profile_function(block_b)

def profile_block_g():
    prf.profile_function(block_g)

def city_b():
    elem = cities.city()
    blgeo.create_element(elem)

def city_g():
    gritgeo.reset_world_scripts()
    elem = cities.city()
    gritgeo.create_element(elem)
    gritgeo.output_world_scripts()

def profile_city_b():
    prf.profile_function(city_b)

def profile_city_g():
    prf.profile_function(city_g)

def add_prims_g():
    gritgeo.reset_world_scripts()
    p1 = pr.ucube()
    p1.translate([1,1,0])
    p2 = pr.ucube()
    p2.translate([-1,-1,0])
    p3 = p1 + p2
    gritgeo.create_primitive(p3)
    gritgeo.output_world_scripts()

def terrain_g():
    gritgeo.reset_world_scripts()
    ter = terr.terrain()
    gritgeo.create_element(ter)
    gritgeo.output_world_scripts()








