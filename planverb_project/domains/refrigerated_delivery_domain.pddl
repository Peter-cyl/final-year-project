(define (domain refrigerated_delivery)
  (:requirements :typing :durative-actions :fluents :timed-initial-literals) 
  (:types 
    prod driver truck - locatable
    meat cereal - prod
    location
  )
  (:predicates 
    (at ?l1 - locatable ?l2 - location)      ; ?l1 is at location ?l2
    (in ?p - prod ?t - truck)                ; ?p is in ?t
    (boarded ?d - driver ?t - truck)         ; ?d has boarded ?t
    (refrigerated ?t - truck)                ; ?t is refrigerated
    (can_deliver ?p - prod)                  ; ?p can be delivered (is still fresh)
  )

  (:functions
    (time_to_drive ?loc ?loc1 - location)
  )

  ; Load the produce ?prod into the truck ?truck at location ?loc
  (:durative-action load_truck
    :parameters (?prod - prod ?truck - truck ?loc - location)
    :duration (= ?duration 0.01)
    :condition (and 
                  (over all (at ?truck ?loc))   ; ?truck is at ?loc
                  (at start (at ?prod ?loc))    ; ?prod is at ?loc
                )
    :effect (and 
              (at start (not (at ?prod ?loc))) 
              (at end (in ?prod ?truck))
            )
  )

  ; Driver ?d boards the truck ?t at location ?l1
  (:durative-action board_truck
    :parameters (?d - driver ?t - truck ?l1 - location)
    :duration (= ?duration 0.01)
    :condition (and
                  (over all (at ?t ?l1))        ; ?t is at ?l1
                  (at start (at ?d ?l1))        ; ?d is at ?l1
               )
    :effect (and
              (at start (not (at ?d ?l1)))
              (at end (boarded ?d ?t))
            )
  )

  ; Driver ?d drives the truck ?t from location ?l1 to location ?l2
  (:durative-action drive_truck
    :parameters (?d - driver ?t - truck ?l1 ?l2 - location)
    :duration (= ?duration (time_to_drive ?l1 ?l2))
    :condition (and
                  (over all (boarded ?d ?t))    ; ?d has boarded ?t
                  (at start (at ?t ?l1))        ; ?t is at ?l1
               )
    :effect (and
              (at start (not (at ?t ?l1)))
              (at end (at ?t ?l2))
            )
  )
  
  ; Extend the life of the meat ?m that is in the truck ?t
  (:durative-action extend_meat_life
    :parameters (?m - meat ?t - truck)
    :duration (= ?duration 0.01)
    :condition (and
                (over all (in ?m ?t))           ; ?m is in ?t
                (over all (refrigerated ?t))    ; ?t is refrigerated
              )
    :effect (and
              (at end (can_deliver ?m))
            )
  )

  ; Deliver the produce ?p from truck ?t to location ?l
  (:durative-action deliver_produce
    :parameters (?p - prod ?t - truck ?l - location)
    :duration (= ?duration 0.01)
    :condition (and
                  (over all (at ?t ?l))         ; ?t is at ?l
                  (over all (can_deliver ?p))   ; ?p can still be delivered (is fresh)
                  (at start (in ?p ?t))         ; ?p is in ?t
               )
    :effect (and
              (at start (not (in ?p ?t)))
              (at end (at ?p ?l))
            )
  )

)
