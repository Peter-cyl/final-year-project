(define (problem strips-sat-x-1)
(:domain satellite)
(:objects
	satellite0 - satellite
	instrument0 - instrument
	instrument1 - instrument
	infrared0 - mode
	infrared1 - mode
	image2 - mode
	GroundStation1 - direction
	Star0 - direction
	GroundStation2 - direction
	Planet3 - direction
	Planet4 - direction
	Phenomenon5 - direction
	Phenomenon6 - direction
	Star7 - direction
)
(:init
	(supports instrument0 infrared1)
	(supports instrument0 infrared0)
	(calibration_target instrument0 Star0)
	(supports instrument1 image2)
	(supports instrument1 infrared1)
	(supports instrument1 infrared0)
	(calibration_target instrument1 GroundStation2)
	(on_board instrument0 satellite0)
	(on_board instrument1 satellite0)
	(power_avail satellite0)
	(pointing satellite0 Planet4)
	
	(not_same GroundStation1 Star0)
	(not_same GroundStation1 GroundStation2)
	(not_same GroundStation1 Planet3)
	(not_same GroundStation1 Planet4)
	(not_same GroundStation1 Phenomenon5)
	(not_same GroundStation1 Phenomenon6)
	(not_same GroundStation1 Star7)

	(not_same Star0 GroundStation1)
	(not_same Star0 GroundStation2)
	(not_same Star0 Planet3)
	(not_same Star0 Planet4)
	(not_same Star0 Phenomenon5)
	(not_same Star0 Phenomenon6)
	(not_same Star0 Star7)

	(not_same GroundStation2 GroundStation1)
	(not_same GroundStation2 Star0)
	(not_same GroundStation2 Planet3)
	(not_same GroundStation2 Planet4)
	(not_same GroundStation2 Phenomenon5)
	(not_same GroundStation2 Phenomenon6)
	(not_same GroundStation2 Star7)

	(not_same Planet3 GroundStation1)
	(not_same Planet3 Star0)
	(not_same Planet3 GroundStation2)
	(not_same Planet3 Planet4)
	(not_same Planet3 Phenomenon5)
	(not_same Planet3 Phenomenon6)
	(not_same Planet3 Star7)

	(not_same Planet4 GroundStation1)
	(not_same Planet4 Star0)
	(not_same Planet4 GroundStation2)
	(not_same Planet4 Planet3)
	(not_same Planet4 Phenomenon5)
	(not_same Planet4 Phenomenon6)
	(not_same Planet4 Star7)

	(not_same Phenomenon5 GroundStation1)
	(not_same Phenomenon5 Star0)
	(not_same Phenomenon5 GroundStation2)
	(not_same Phenomenon5 Planet3)
	(not_same Phenomenon5 Planet4)
	(not_same Phenomenon5 Phenomenon6)
	(not_same Phenomenon5 Star7)

	(not_same Phenomenon6 GroundStation1)
	(not_same Phenomenon6 Star0)
	(not_same Phenomenon6 GroundStation2)
	(not_same Phenomenon6 Planet3)
	(not_same Phenomenon6 Planet4)
	(not_same Phenomenon6 Phenomenon5)
	(not_same Phenomenon6 Star7)

	(not_same Star7 GroundStation1)
	(not_same Star7 Star0)
	(not_same Star7 GroundStation2)
	(not_same Star7 Planet3)
	(not_same Star7 Planet4)
	(not_same Star7 Phenomenon5)
	(not_same Star7 Phenomenon6)
)
(:goal (and
	(have_image Planet3 infrared0)
	(have_image Planet4 infrared0)
	(have_image Phenomenon5 image2)
	(have_image Phenomenon6 infrared0)
	(have_image Star7 infrared0)
))
(:metric minimize (total-time))

)
