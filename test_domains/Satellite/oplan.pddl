Number of literals: 37
Constructing lookup tables: [10%] [20%] [30%] [40%] [50%] [60%] [70%] [80%] [90%] [100%]
Post filtering unreachable actions:  [10%] [20%] [30%] [40%] [50%] [60%] [70%] [80%] [90%] [100%]
[01;34mNo analytic limits found, not considering limit effects of goal-only operators[00m
All the ground actions in this problem are compression-safe
Initial heuristic = 12.000
b (11.000 | 2.000)b (10.000 | 10.001)b (9.000 | 10.002)b (8.000 | 17.002)b (7.000 | 22.002)b (6.000 | 29.002)b (5.000 | 34.002)b (4.000 | 41.002)b (3.000 | 46.002)b (2.000 | 53.002)b (1.000 | 58.002)
; Plan found with metric 65.002
; States evaluated so far: 33
; Time 0.00
0.000: (switch_on instrument1 satellite0)  [2.000]
0.000: (turn_to satellite0 groundstation2 planet4)  [5.000]
5.001: (calibrate satellite0 instrument1 groundstation2)  [5.000]
5.002: (turn_to satellite0 phenomenon5 groundstation2)  [5.000]
10.002: (take_image satellite0 phenomenon5 instrument1 image2)  [7.000]
17.002: (turn_to satellite0 phenomenon6 phenomenon5)  [5.000]
22.002: (take_image satellite0 phenomenon6 instrument1 infrared0)  [7.000]
29.002: (turn_to satellite0 planet3 phenomenon6)  [5.000]
34.002: (take_image satellite0 planet3 instrument1 infrared0)  [7.000]
41.002: (turn_to satellite0 planet4 planet3)  [5.000]
46.002: (take_image satellite0 planet4 instrument1 infrared0)  [7.000]
53.002: (turn_to satellite0 star7 planet4)  [5.000]
58.002: (take_image satellite0 star7 instrument1 infrared0)  [7.000]

 * All goal deadlines now no later than 65.002

Resorting to best-first search
b (11.000 | 2.000)b (10.000 | 10.001)b (9.000 | 10.002)b (8.000 | 17.002)b (7.000 | 22.002)b (6.000 | 29.002)b (5.000 | 34.002)b (4.000 | 41.002)b (3.000 | 46.002)b (2.000 | 53.002)b (1.000 | 58.002
