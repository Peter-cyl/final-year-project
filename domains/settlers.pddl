(define (domain building)
    (:requirements :typing :durative-actions :fluents :timed-initial-literals :equality) 
    
    (:types 
            place vehicle - store
            resource
    )
    
    (:predicates 
        (connected-by-land ?p1 ?p2 - place)             ; ?p1 is connected by land to ?p2
        (connected-by-rail ?p1 - place ?p2 - place)     ; ?p1 is connected by rail to ?p2
        (resourceland ?p - place)                         ; ?p has natural resources available
        (metalliferous ?p - place)                        ; ?p has iron ore deposits
        
        (is-cart ?v - vehicle)                            ; ?v is a cart
        (is-train ?v - vehicle)                           ; ?v is a train
        (at ?v - vehicle ?p - place)                      ; ?v is at ?p
        
        (potential ?v - vehicle)                           ; ?v has not yet been built
        
        (man-available)                                    ; a worker is available
    )
    
    (:functions
        (available ?r - resource ?s - store)              
        (time_to_travel ?p1 ?p2 - place)   
        (space-in-train ?v - vehicle) 
        (space-in-cart ?v - vehicle)
        (housing ?p - place) 
        (big_housing ?p - place)  
    )
    
    (:constants building_resource iron - resource)
    
    ; Load resource ?r onto the train ?v at place ?p
    (:durative-action load-train
     :parameters (?v - vehicle ?p - place ?r - resource) 
     :duration (= ?duration 0.01)
     :condition (and 
                     (over all (at ?v ?p))                           ; ?v is at ?p
                     (over all (is-train ?v))                        ; ?v is a train
                     (at start (> (available ?r ?p) 0))             ; ?r is available at ?p
                     (at start (> (space-in-train ?v) 0))           ; ?v has space available
                     (at start (man-available))                      ; a worker is available
                 ) 
     :effect (and 
               (at start (not (man-available)))
               (at start (decrease (available ?r ?p) 1))
               (at start (decrease (space-in-train ?v) 1)) 
               (at end (increase (available ?r ?v) 1)) 
               (at end (man-available))
             )
    ) 
    
    ; Load resource ?r onto the cart ?v at place ?p
    (:durative-action load-cart
     :parameters (?v - vehicle ?p - place ?r - resource) 
     :duration (= ?duration 0.01)
     :condition (and 
                     (over all (at ?v ?p))                           ; ?v is at ?p
                     (over all (is-cart ?v))                         ; ?v is a cart
                     (at start (> (available ?r ?p) 0))             ; ?r is available at ?p
                     (at start (> (space-in-cart ?v) 0))            ; ?v has space available
                     (at start (man-available))                      ; a worker is available
                 ) 
     :effect (and 
               (at start (not (man-available)))
               (at start (decrease (available ?r ?p) 1))
               (at start (decrease (space-in-cart ?v) 1)) 
               (at end (increase (available ?r ?v) 1)) 
               (at end (man-available))
             )
    ) 
    
    ; Unload resource ?r from the train ?v at place ?p
    (:durative-action unload-train
     :parameters (?v - vehicle ?p - place ?r - resource) 
     :duration (= ?duration 0.01)
     :condition (and 
                     (over all (at ?v ?p))                           ; ?v is at ?p
                     (at start (> (available ?r ?v) 0))             ; ?r is available on ?v
                     (at start (man-available))                      ; a worker is available
                ) 
     :effect (and 
               (at start (not (man-available)))
               (at start (decrease (available ?r ?v) 1))
               (at start (increase (space-in-train ?v) 1)) 
               (at end (increase (available ?r ?p) 1))
               (at end (man-available))
             )
     ) 
     
     ; Unload resource ?r from the cart ?v at place ?p
     (:durative-action unload-cart
     :parameters (?v - vehicle ?p - place ?r - resource) 
     :duration (= ?duration 0.01)
     :condition (and 
                     (over all (at ?v ?p))                           ; ?v is at ?p
                     (at start (> (available ?r ?v) 0))             ; ?r is available on ?v
                     (at start (man-available))                      ; a worker is available
                ) 
     :effect (and 
               (at start (not (man-available)))
               (at start (decrease (available ?r ?v) 1))
               (at start (increase (space-in-cart ?v) 1)) 
               (at end (increase (available ?r ?p) 1))
               (at end (man-available))
             )
     )  
     
     ; Move the train ?v from place ?p1 to place ?p2
     (:durative-action move-train
        :parameters (?v - vehicle ?p1 - place ?p2 - place)
        :duration (= ?duration (* 0.5 (time_to_travel ?p1 ?p2)))
        :condition (and 
                       (over all (is-train ?v))                      ; ?v is a train
                       (over all (not (= ?p1 ?p2)))                 ; ?p1 is different from ?p2
                       (over all (connected-by-rail ?p1 ?p2))       ; ?p1 is connected by rail to ?p2
                       (at start (at ?v ?p1))                        ; ?v is at ?p1
                       (at start (man-available))                    ; a worker is available
                   )
      :effect (and
                  (at start (not (man-available)))
                  (at start (not (at ?v ?p1)))
                  (at end (at ?v ?p2))
                  (at end (man-available))
              )
    )
		
    ; Move the cart ?v from place ?p1 to place ?p2
    (:durative-action move-cart
        :parameters (?v - vehicle ?p1 - place ?p2 - place)
        :duration (= ?duration (* 1 (time_to_travel ?p1 ?p2)))
        :condition (and 
                       (over all (is-cart ?v))                       ; ?v is a cart
                       (over all (not (= ?p1 ?p2)))                 ; ?p1 is different from ?p2
                       (over all (connected-by-land ?p1 ?p2))       ; ?p1 is connected by land to ?p2
                       (at start (at ?v ?p1))                        ; ?v is at ?p1
                       (at start (man-available))                    ; a worker is available
                   )
      :effect (and
                  (at start (not (man-available)))
                  (at start (not (at ?v ?p1)))
                  (at end (at ?v ?p2))
                  (at end (man-available))
              )
    )
    
    
    ; Build a rail connection from place ?p1 to place ?p2
    (:durative-action build-rail 
     :parameters (?p1 - place ?p2 - place) 
     :duration (= ?duration 5) 
     :condition (and 
                   (over all (connected-by-land ?p1 ?p2))           ; ?p1 is connected by land to ?p2
                   (at start (>= (available building_resource ?p1) 2)) ; there are enough building resources at ?p1
                   (at start (>= (available iron ?p1) 3))           ; there is enough iron at ?p1
                   (at start (man-available))                        ; a worker is available
               ) 
     :effect (and 
               (at start (not (man-available)))
               (at start (decrease (available building_resource ?p1) 2)) 
               (at start (decrease (available iron ?p1) 3)) 
               (at end (connected-by-rail ?p1 ?p2))
               (at end (connected-by-rail ?p2 ?p1))
               (at end (man-available))
             )
     ) 
     
     ; Build a train ?v at place ?p
     (:durative-action build-train 
      :parameters (?p - place ?v - vehicle) 
      :duration (= ?duration 5) 
      :condition (and 
                    (at start (>= (available iron ?p) 4))           ; there is enough iron at ?p
                    (at start (potential ?v))                         ; ?v has not yet been built
                    (at start (man-available))                        ; a worker is available
                 )
      :effect (and 
               (at start (not (man-available)))
               (at start (decrease (available iron ?p) 4)) 
               (at start (not (potential ?v))) 
               (at end (at ?v ?p)) 
               (at end (is-train ?v))		
               (at end (assign (space-in-train ?v) 3))
               (at end (assign (available building_resource ?v) 0))
               (at end (assign (available iron ?v) 0))
               (at end (man-available))
           )
    ) 
     
     ; Build a cart ?v at place ?p
     (:durative-action build-cart 
      :parameters (?p - place ?v - vehicle) 
      :duration (= ?duration 1) 
      :condition (and 
                    (at start (>= (available building_resource ?p) 1)) ; there are enough building resources at ?p
                    (at start (potential ?v))                         ; ?v has not yet been built
                    (at start (man-available))                        ; a worker is available
                 )
      :effect (and 
               (at start (not (man-available)))
               (at start (decrease (available building_resource ?p) 1))
               (at start (not (potential ?v))) 
               (at end (at ?v ?p)) 
               (at end (is-cart ?v))		 
               (at end (assign (space-in-cart ?v) 1))
               (at end (assign (available building_resource ?v) 0))
               (at end (assign (available iron ?v) 0))
               (at end (man-available))
           )
    ) 
  
  
    ; Build a house at place ?p
    (:durative-action build-house
     :parameters (?p - place)
     :duration (= ?duration 3) 
     :condition (and 
                   (at start (>= (available building_resource ?p) 2)) ; there are enough building resources at ?p
                   (at start (man-available))                        ; a worker is available
               )
     :effect (and 
                (at start (not (man-available)))
                (at start (decrease (available building_resource ?p) 2))
                (at end (increase (housing ?p) 1))
                (at end (man-available))		
             )
     )	
     
     ; Build a large house at place ?p
     (:durative-action build-big-house
     :parameters (?p - place)
     :duration (= ?duration 3) 
     :condition (and 
                   (at start (>= (available building_resource ?p) 2)) ; there are enough building resources at ?p
                   (at start (>= (available iron ?p) 1))             ; there is enough iron at ?p
                   (at start (man-available))                        ; a worker is available
               )
     :effect (and 
                (at start (not (man-available)))
                (at start (decrease (available building_resource ?p) 2))
                (at start (decrease (available iron ?p) 1)) 
                (at end (increase (big_housing ?p) 1))
                (at end (man-available))		
             )
     )	
     
     
  
  ; Gather building resources at place ?p
  (:durative-action find-resource 
   :parameters (?p - place)
   :duration (= ?duration 1)  
   :condition (and
                 (over all (resourceland ?p))                        ; ?p has natural resources
                 (at start (man-available))                          ; a worker is available
              )
   :effect (and 
               (at start (not (man-available)))
               (at end (increase (available building_resource ?p) 1))
               (at end (man-available))
           )
   ) 
 
 
  ; Mine iron ore at place ?p
  (:durative-action mine-iron 
   :parameters (?p - place) 
   :duration (= ?duration 1) 
   :condition (and 
                 (over all (metalliferous ?p))                       ; ?p has iron ore deposits
                 (at start (man-available))                          ; a worker is available
              )
   :effect (and 
               (at start (not (man-available)))
               (at end (increase (available iron ?p) 1))
               (at end (man-available))
	)) 
     
   
	    
 
)
