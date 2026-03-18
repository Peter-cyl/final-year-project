
(define (domain satellite)
  (:requirements :strips :equality :typing :durative-actions)
(:types satellite direction instrument mode)
 (:predicates 
               (on_board ?i - instrument ?s - satellite)             ; ?i is on board ?s
               (supports ?i - instrument ?m - mode)                  ; ?i supports mode ?m
               (pointing ?s - satellite ?d - direction)              ; ?s is pointing at ?d
               (power_avail ?s - satellite)                          ; ?s has power available
               (power_on ?i - instrument)                            ; ?i is powered on
               (calibrated ?i - instrument)                          ; ?i is calibrated
               (have_image ?d - direction ?m - mode)                 ; an image of ?d in mode ?m has been taken
               (calibration_target ?i - instrument ?d - direction)   ; ?d is the calibration target for ?i
         (not_same ?d_new ?d_prev - direction))
 
 

  ; Turn satellite ?s from direction ?d_prev to direction ?d_new
  (:durative-action turn_to
   :parameters (?s - satellite ?d_new - direction ?d_prev - direction)
   :duration (= ?duration 5)
   :condition (and 
                   (at start (pointing ?s ?d_prev))                  ; ?s is pointing at ?d_prev
                   (over all (not_same ?d_new ?d_prev))              ; ?d_new is different from ?d_prev
              )
   :effect (and  (at end (pointing ?s ?d_new))
                 (at start (not (pointing ?s ?d_prev)))
           )
  )

 
  ; Switch on instrument ?i on satellite ?s
  (:durative-action switch_on
   :parameters (?i - instrument ?s - satellite)
   :duration (= ?duration 2)
   :condition (and 
                      (over all (on_board ?i ?s))                    ; ?i is on board ?s
                      (at start (power_avail ?s))                    ; ?s has power available
              )
   :effect (and (at end (power_on ?i))
                (at start (not (calibrated ?i)))
                (at start (not (power_avail ?s)))
           )
          
  )

 
  ; Switch off instrument ?i on satellite ?s
  (:durative-action switch_off
   :parameters (?i - instrument ?s - satellite)
   :duration (= ?duration 1)
   :condition (and 
                      (over all (on_board ?i ?s))                    ; ?i is on board ?s
                      (at start (power_on ?i))                       ; ?i is powered on
                  )
   :effect (and (at start (not (power_on ?i)))
                (at end (power_avail ?s))
           )
  )

  ; Calibrate instrument ?i on satellite ?s pointing at direction ?d
  (:durative-action calibrate
   :parameters (?s - satellite ?i - instrument ?d - direction)
   :duration (= ?duration 5)
   :condition (and 
                      (over all (on_board ?i ?s))                    ; ?i is on board ?s
                      (over all (calibration_target ?i ?d))          ; ?d is the calibration target for ?i
                      (at start (pointing ?s ?d))                    ; ?s is pointing at ?d
                      (over all (power_on ?i))                       ; ?i is powered on
                      (at end (power_on ?i))                         ; ?i is still powered on at end
                  )
   :effect (at end (calibrated ?i)) 
  )


  ; Take an image of direction ?d in mode ?m using instrument ?i on satellite ?s
  (:durative-action take_image
   :parameters (?s - satellite ?d - direction ?i - instrument ?m - mode)
   :duration (= ?duration 7)
   :condition (and 
                      (over all (calibrated ?i))                     ; ?i is calibrated
                      (over all (on_board ?i ?s))                    ; ?i is on board ?s
                      (over all (supports ?i ?m))                    ; ?i supports mode ?m
                      (over all (power_on ?i))                       ; ?i is powered on
                      (over all (pointing ?s ?d))                    ; ?s is pointing at ?d
                      (at end (power_on ?i))                         ; ?i is still powered on at end
               )
   :effect (at end (have_image ?d ?m))
  )
)
