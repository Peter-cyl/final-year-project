Parsing and Instantiating...
Done
One way facts...
Semaphore Facts...
Envelope Facts...
One-shot actions...
(board_truck d1 t1 a) is 1 shot
(board_truck d1 t2 a) is 1 shot
Integral variables...
Variable bounds...
Static numeric conditions...
Duration bounds...
TIL time window analysis...
Bounding action timestamps due to time windows...
(can_deliver ce) forms a window with range [0.000,1000.000]
Bounds on (deliver_produce ce t1 a) (duration [0.010,0.010]):
	0: [0.000,999.990]
	1: [0.000,999.990]
	2: [0.010,1000.000]
Bounds on (deliver_produce ce t2 a) (duration [0.010,0.010]):
	0: [0.000,999.990]
	1: [0.000,999.990]
	2: [0.010,1000.000]
Bounds on (deliver_produce ce t1 b) (duration [0.010,0.010]):
	0: [0.000,999.990]
	1: [0.000,999.990]
	2: [0.010,1000.000]
Bounds on (deliver_produce ce t2 b) (duration [0.010,0.010]):
	0: [0.000,999.990]
	1: [0.000,999.990]
	2: [0.010,1000.000]
Bounds on (deliver_produce ce t1 c) (duration [0.010,0.010]):
	0: [0.000,999.990]
	1: [0.000,999.990]
	2: [0.010,1000.000]
Bounds on (deliver_produce ce t2 c) (duration [0.010,0.010]):
	0: [0.000,999.990]
	1: [0.000,999.990]
	2: [0.010,1000.000]
Dominance constraints (excluding processes and events)...
Damaging events...
Dominance constraints (including processes and events)...
Variable monotonicity...
Max/min needed values for any single precondition...
Irrelevant action pruning by backward reachability from goal...
Uninterestingness criteria...
Compression-safe actions...
Compression-safe invariants...
100% of durative actions in this problem are compression safe
Goal Goal [3]
    (-(total-time) >= -inf)
    (at ce c)
    (at m b)

Finishing preprocessing.  Making a TRPG heuristic...
Making an open list...
Running WA* search (g weight = 1, h weight = 5)
{(at t1 a),(at t2 a),(at d1 a),(at m a),(at ce a),(can_deliver m),(can_deliver ce)}
[]
Initial heuristic = 7
Initial stats: t=0s, 5488kb
b (6 @ n=2, t=0s, 5488kb)b (5 @ n=9, t=0s, 5488kb)b (4 @ n=15, t=0s, 5488kb)b (3 @ n=20, t=0s, 5488kb)b (2 @ n=28, t=0s, 5488kb)b (1 @ n=32, t=0s, 5488kb)
;;;; Solution Found
; Time 0.00
; Peak memory 5620kb
; Nodes Generated: 37
; Nodes Expanded:  7
; Nodes Evaluated: 36
; Nodes Tunneled:  0
; Nodes memoised with open actions: 0
; Nodes memoised without open actions: 37
; Nodes pruned by memoisation: 0
; Metric value 35.031
0.001: (load_truck ce t1 a) [0.010] ; (0)
0.001: (load_truck m t1 a) [0.010] ; (1)
0.001: (board_truck d1 t1 a) [0.010] ; (12)
0.011: (drive_truck d1 t1 a b) [20.000] ; (20)
20.011: (deliver_produce m t1 b) [0.010] ; (38)
20.021: (drive_truck d1 t1 b c) [15.000] ; (28)
35.021: (deliver_produce ce t1 c) [0.010] ; (41)

;;;; Solution Found
; Time 3.57
; Peak memory 330084kb
; Nodes Generated: 60736
; Nodes Expanded:  12996
; Nodes Evaluated: 47939
; Nodes Tunneled:  0
; Nodes memoised with open actions: 0
; Nodes memoised without open actions: 60736
; Nodes pruned by memoisation: 0
; Metric value 25.031
0.001: (board_truck d1 t2 a) [0.010] ; (13)
0.001: (load_truck ce t2 a) [0.010] ; (2)
0.001: (load_truck m t2 a) [0.010] ; (3)
0.011: (drive_truck d1 t2 a c) [10.000] ; (27)
10.011: (deliver_produce ce t2 c) [0.010] ; (43)
10.021: (drive_truck d1 t2 c b) [15.000] ; (25)
21.991: (extend_meat_life m t2) [0.010] ; (32)
25.021: (deliver_produce m t2 b) [0.010] ; (40)
