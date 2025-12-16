(define (problem building)
(:domain building)
(:objects
	location0 - place
	location3 - place
        
	vehicle3 - vehicle
)
(:init
	(= (housing location0) 0)
	(= (available building_resource location0) 0)
	(= (available iron location0) 0)
	(resourceland location3)
	(metalliferous location3)
	(= (housing location3) 0)
	(= (available building_resource location3) 0)
	(= (available iron location3) 0)
       
	(connected-by-land location3 location0)
	(connected-by-land location0 location3)
        
	(potential vehicle3)
	(man-available)
	
        (= (time_to_travel location0 location3) 2)
        (= (time_to_travel location3 location0) 2)
        
        


)
(:goal (and
	  (>= (housing location0) 2)
	
	  (is-train vehicle3)
	)
)

(:metric minimize (total-time))

)
