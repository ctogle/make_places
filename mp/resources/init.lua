
solemn_input_filter = InputFilter(10,'solemn_bindings')

include `../system/sky_cycle.lua`

map_ghost_spawn(vector3(0, 0, 100))

--include `bestworld/map.lua`
include `newworld/map.lua`
--include `oldworld/map.lua`
--include `greatworld/map.lua`

include `weapons/init.lua`
include `characters/init.lua`
include `vehicles/init.lua`

object `/solemn/vehicles/bug` (0,0,100) { bearing=45, name=`bug1` }
object `/solemn/characters/char` (0,0,100) { bearing=45, name=`char1` }
--object `/solemn/weapons/m24/m24sniper` (10,0,20) { bearing=45, name=`m24_1` }


function spawn_player()
  print('spawning player')
  place `/solemn/characters/char`
end

function spawn_bug()
  print('spawning bug')
  place `/solemn/vehicles/bug`
end

the_tod = 60000
function time_of_day()
	env.clockTicking = false
	env.secondsSinceMidnight= the_tod
end
time_of_day()

function move_time()
  the_tod = (the_tod + 2500) % 86400
  time_of_day()
end



solemn_input_filter:bind(`p`, spawn_player, nil, true)
solemn_input_filter:bind(`b`, spawn_bug, nil, true)
solemn_input_filter:bind(`t`, move_time, nil, true)



