(define (domain CrewPlanning)
 (:requirements :durative-actions :typing :fluents :action-costs )
(:types MedicalState FilterState CrewMember PayloadAct Day RPCM - objects)

(:predicates
	(changed ?fs - FilterState ?d - Day)                ; filter ?fs has been changed on ?d

	(done_meal  ?c - CrewMember ?d - Day)               ; ?c has eaten on ?d
	(done_exercise  ?c - CrewMember ?d - Day)           ; ?c has exercised on ?d
	(not_sleeping ?c - CrewMember)                       ; ?c is awake
	(gone_to_sleep ?c - CrewMember ?d - Day)            ; ?c has gone to sleep on ?d

	(payload_act_completed ?pa - PayloadAct)            ; payload activity ?pa has been completed

	(currentday ?d - Day)                                ; the current day is ?d
	(active ?c - CrewMember  ?d - day)                   ; ?c is active on ?d
	(next ?d1 ?d2 - Day)                                 ; ?d2 follows ?d1

	(not-action-performing)                              ; no action is currently being performed
)

(:functions
	(available_time ?c - CrewMember ?d - Day) - number
	(crew_efficiency ?c - CrewMember ?d - Day) - number
	(achieve_time_discount ?d - Day) - number
	(payloadact_length ?pa - PayloadAct) - number
	(the-cost) - number)


; Move to the next day from ?d1 to ?d2
(:durative-action move_to_next_day
 :parameters (?d1 ?d2 - Day)
 :duration (= ?duration 0.01)
 :condition (and 
                (at start (currentday ?d1))                          ; the current day is ?d1
		(over all (next ?d1 ?d2))                            ; ?d2 follows ?d1
		(over all (forall (?c - CrewMember) (gone_to_sleep ?c ?d1))) ; all crew members have gone to sleep on ?d1
		(at start (not-action-performing))                   ; no action is being performed
		)
 :effect (and 
        (at start (not (not-action-performing)))
        (at start (not (currentday ?d1)))
	(at end (currentday ?d2))
	(at end (not-action-performing))
	)
)


; Crew member ?c wakes up on day ?d
(:durative-action wake_up
 :parameters (?c - CrewMember ?d - Day)
 :duration (= ?duration 195)
 :condition (and  
                (over all (currentday ?d))                           ; the current day is ?d
	        (at start (>= (available_time ?c ?d) 195))          ; ?c has enough available time
	        (at start (not-action-performing))                   ; no action is being performed
	        )
 :effect (and  
           (at start (not (not-action-performing)))
           (at start (not_sleeping ?c))
	   (at start (increase (the-cost) 195))
	   (at start (decrease (available_time ?c ?d) 195))
	   (at end (not-action-performing))
	 )
)


; Crew member ?c has a meal on day ?d
(:durative-action have_meal
 :parameters (?c - CrewMember ?d - Day)
 :duration (= ?duration 60)
 :condition (and  
                (over all (currentday ?d))                           ; the current day is ?d
		(over all (not_sleeping ?c))                          ; ?c is awake
	        (at start (>= (available_time ?c ?d) 60))           ; ?c has enough available time
	        (at start (not-action-performing))                   ; no action is being performed
	        )
 :effect (and  
           (at start (not (not-action-performing)))
           (at end (done_meal ?c ?d))
	   (at start (increase (the-cost) 60))
	   (at start (decrease (available_time ?c ?d) 60))
	   (at end (not-action-performing))
	   )
)

; Crew member ?c exercises on day ?d
(:durative-action exercise
 :parameters (?c - CrewMember ?d - Day)
 :duration (= ?duration 60)
 :condition (and  
                (over all (currentday ?d))                           ; the current day is ?d
		(over all (not_sleeping ?c))                          ; ?c is awake
	        (at start (>= (available_time ?c ?d) 60))           ; ?c has enough available time
	        (at start (not-action-performing))                   ; no action is being performed
	        )
 :effect (and  
           (at start (not (not-action-performing)))
           (at end (done_exercise ?c ?d))
	   (at start (increase (the-cost) 60))
	   (at start (decrease (available_time ?c ?d) 60))
	   (at end (not-action-performing))
	   )
)


; Crew member ?c goes to sleep on day ?d
(:durative-action sleep
 :parameters (?c - CrewMember ?d - Day)
 :duration (= ?duration 600)
 :condition (and  
               (over all (currentday ?d))                            ; the current day is ?d
		(at start (not_sleeping ?c))                          ; ?c is awake
		(at start (not (gone_to_sleep ?c ?d)))               ; ?c has not already gone to sleep on ?d
		(at start (active ?c ?d))                             ; ?c is active on ?d
		(over all (done_exercise ?c ?d))                      ; ?c has exercised on ?d
		(over all (done_meal ?c ?d))                          ; ?c has eaten on ?d
	        (at start (>= (available_time ?c ?d) 600))          ; ?c has enough available time
	        (at start (not-action-performing))                   ; no action is being performed
	        )
 :effect (and  
           (at start (not (not-action-performing)))
           (at start (not (active ?c ?d)))
	   (at start (not (not_sleeping ?c)))
	   (at start (gone_to_sleep ?c ?d))
	   (at start (increase (the-cost) 600))
	   (at start (decrease (available_time ?c ?d) 600))
	   (at end (not-action-performing))
	   )
)


; Crew member ?c changes filter ?fs on day ?d
(:durative-action change_filter
 :parameters (?fs - FilterState  ?c - CrewMember ?d - Day)
 :duration (= ?duration (* 6 (crew_efficiency ?c ?d)))
 :condition (and  
                (over all (currentday ?d))                           ; the current day is ?d
		(over all (not_sleeping ?c))                          ; ?c is awake
	         (at start (>= (available_time ?c ?d) 60))          ; ?c has enough available time
	         (at start (not-action-performing))                  ; no action is being performed
	         )
 :effect (and  
            (at start (not (not-action-performing)))
            (at end (changed ?fs ?d))
	    (at start (increase (the-cost) (* 6 (crew_efficiency ?c ?d))))
	    (at start (decrease (available_time ?c ?d) 60))
	    (at end (not-action-performing))
	    )
)


; Crew member ?c conducts payload activity ?pa on day ?d
(:durative-action conduct_payload_activity
 :parameters (?pa - PayloadAct ?c - CrewMember ?d - Day)
 :duration (= ?duration (* (/ (payloadact_length ?pa) 10) (+ (crew_efficiency ?c ?d) (achieve_time_discount ?d))))
 :condition (and 
                (over all (currentday ?d))                           ; the current day is ?d
		(over all (not_sleeping ?c))                          ; ?c is awake
		(at start (>= (available_time ?c ?d) (payloadact_length ?pa))) ; ?c has enough available time
		(at start (not-action-performing))                   ; no action is being performed
		)
 :effect (and 
             (at start (not (not-action-performing)))
             (at end (payload_act_completed ?pa))
	      (at start (increase (the-cost)
                    (* (/ (payloadact_length ?pa) 10)
		     (+ (crew_efficiency ?c ?d) (achieve_time_discount ?d)))))
	      (at start (decrease (available_time ?c ?d) (payloadact_length ?pa)))
	      (at end (not-action-performing))
	 )
)

)
