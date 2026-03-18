(define (domain Rover)
(:requirements :typing :durative-actions :fluents :duration-inequalities)
(:types rover waypoint store lander )

(:predicates 
             (at ?x - rover ?y - waypoint)                          ; ?x is at ?y
             (at_lander ?x - lander ?y - waypoint)                  ; lander ?x is at ?y
             (can_traverse ?r - rover ?x - waypoint ?y - waypoint)  ; ?r can travel from ?x to ?y
             (equipped_for_soil_analysis ?r - rover)                 ; ?r is equipped for soil analysis
             (equipped_for_rock_analysis ?r - rover)                 ; ?r is equipped for rock analysis
             
             (empty ?s - store)                                      ; ?s is empty
             (have_rock_analysis ?r - rover ?w - waypoint)           ; ?r has rock analysis data from ?w
             (have_soil_analysis ?r - rover ?w - waypoint)           ; ?r has soil analysis data from ?w
             (full ?s - store)                                       ; ?s is full

             (available ?r - rover)                                  ; ?r is available
             (visible ?w - waypoint ?p - waypoint)                   ; ?w is visible from ?p

             (communicated_soil_data ?w - waypoint)                  ; soil data from ?w has been communicated
             (communicated_rock_data ?w - waypoint)                  ; rock data from ?w has been communicated

             (at_soil_sample ?w - waypoint)                          ; there is a soil sample at ?w
             (at_rock_sample ?w - waypoint)                          ; there is a rock sample at ?w

             (store_of ?s - store ?r - rover)                        ; ?s is the store of ?r

             (channel_free ?l - lander)                              ; ?l has a free communication channel
             (in_sun ?w - waypoint)                                  ; ?w is in sunlight
             (notcharging ?r - rover)                                ; ?r is not currently charging

)
(:functions (energy ?r - rover) (recharge-rate ?x - rover))

; Rover ?x navigates from waypoint ?y to waypoint ?z
(:durative-action navigate
:parameters (?x - rover ?y - waypoint ?z - waypoint) 
:duration (= ?duration 5)
:condition (and 
                (over all (can_traverse ?x ?y ?z))       ; ?x can traverse from ?y to ?z
                (at start (available ?x))                 ; ?x is available
                (at start (at ?x ?y))                     ; ?x is at ?y
                (at start (>= (energy ?x) 5))            ; ?x has enough energy
                (over all (visible ?y ?z))                ; ?y is visible from ?z
            )
:effect (and (at start (decrease (energy ?x) 5)) (at start (not (at ?x ?y))) (at end (at ?x ?z))))

; Rover ?x recharges at waypoint ?w
(:durative-action recharge
:parameters (?x - rover ?w - waypoint)
:duration (= ?duration 1)
:condition (and 
                (at start (at ?x ?w))                     ; ?x is at ?w
                (over all (at ?x ?w))                     ; ?x stays at ?w
                (at start (in_sun ?w))                    ; ?w is in sunlight
                (at start (<= (energy ?x) 20))           ; ?x has low energy
                (at start (notcharging ?x))               ; ?x is not already charging
           )
:effect (and 
             (at start (not (notcharging ?x)))
             (at end (increase (energy ?x) (* ?duration (recharge-rate ?x))))
             (at end (notcharging ?x))
             )
)


; Rover ?x collects a soil sample at waypoint ?p using store ?s
(:durative-action sample_soil
:parameters (?x - rover ?s - store ?p - waypoint)
:duration (= ?duration 10)
:condition (and 
                (over all (at ?x ?p))                     ; ?x is at ?p
                (at start (at ?x ?p))                     ; ?x is at ?p
                (at start (at_soil_sample ?p))            ; there is a soil sample at ?p
                (at start (equipped_for_soil_analysis ?x)) ; ?x is equipped for soil analysis
                (at start (>= (energy ?x) 3))            ; ?x has enough energy
                (at start (store_of ?s ?x))               ; ?s is the store of ?x
                (at start (empty ?s))                     ; ?s is empty
           )
:effect (and (at start (not (empty ?s))) (at end (full ?s)) (at start (decrease (energy ?x) 3)) (at end (have_soil_analysis ?x ?p)) (at end (not (at_soil_sample ?p))))
)

; Rover ?x collects a rock sample at waypoint ?p using store ?s
(:durative-action sample_rock
:parameters (?x - rover ?s - store ?p - waypoint)
:duration (= ?duration 8)
:condition (and 
                (over all (at ?x ?p))                     ; ?x is at ?p
                (at start (at ?x ?p))                     ; ?x is at ?p
                (at start (>= (energy ?x) 5))            ; ?x has enough energy
                (at start (at_rock_sample ?p))            ; there is a rock sample at ?p
                (at start (equipped_for_rock_analysis ?x)) ; ?x is equipped for rock analysis
                (at start (store_of ?s ?x))               ; ?s is the store of ?x
                (at start (empty ?s))                     ; ?s is empty
           )
:effect (and (at start (not (empty ?s))) (at end (full ?s)) (at end (have_rock_analysis ?x ?p)) (at start (decrease (energy ?x) 5)) (at end (not (at_rock_sample ?p))))
)

; Rover ?x empties store ?y
(:durative-action drop
:parameters (?x - rover ?y - store)
:duration (= ?duration 1)
:condition (and 
                (at start (store_of ?y ?x))               ; ?y is the store of ?x
                (at start (full ?y))                      ; ?y is full
           )
:effect (and (at end (not (full ?y))) (at end (empty ?y)))
)



; Rover ?r communicates soil data from waypoint ?p via lander ?l
(:durative-action communicate_soil_data
 :parameters (?r - rover ?l - lander ?p - waypoint ?x - waypoint ?y - waypoint)
 :duration (= ?duration 10)
 :condition (and 
                (over all (at ?r ?x))                     ; ?r is at ?x
                (over all (at_lander ?l ?y))              ; lander ?l is at ?y
                (at start (have_soil_analysis ?r ?p))     ; ?r has soil analysis data from ?p
                (at start (>= (energy ?r) 4))            ; ?r has enough energy
                (at start (visible ?x ?y))                ; ?x is visible from ?y
                (at start (available ?r))                  ; ?r is available
                (at start (channel_free ?l))               ; ?l has a free channel
            )
 :effect (and (at start (not (available ?r))) (at start (not (channel_free ?l))) (at end (channel_free ?l))
		(at end (communicated_soil_data ?p))(at end (available ?r))(at start (decrease (energy ?r) 4)))
)

; Rover ?r communicates rock data from waypoint ?p via lander ?l
(:durative-action communicate_rock_data
 :parameters (?r - rover ?l - lander ?p - waypoint ?x - waypoint ?y - waypoint)
 :duration (= ?duration 10)
 :condition (and 
                (over all (at ?r ?x))                     ; ?r is at ?x
                (over all (at_lander ?l ?y))              ; lander ?l is at ?y
                (at start (have_rock_analysis ?r ?p))     ; ?r has rock analysis data from ?p
                (at start (visible ?x ?y))                ; ?x is visible from ?y
                (at start (available ?r))                  ; ?r is available
                (at start (channel_free ?l))               ; ?l has a free channel
                (at start (>= (energy ?r) 4))            ; ?r has enough energy
            )
 :effect (and (at start (not (available ?r))) (at start (not (channel_free ?l))) (at end (channel_free ?l))(at end (communicated_rock_data ?p))(at end (available ?r)) (at start (decrease (energy ?r) 4)))
)




)
