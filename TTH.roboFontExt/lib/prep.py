
PREP = [
'PUSHW[ ] 0', # call function 0
'CALL[ ]',
'SVTCA[0]',
'PUSHW[ ] 1 2 2', #call function 1 two times -> round in pixel CVT 1 and 2
'CALL[ ]',
'SVTCA[1]',
'PUSHW[ ] 3 2 2', #call function 1 two times -> round in pixel CVT 3 and 4
'CALL[ ]',
'SVTCA[1]',
'PUSHW[ ] 3 68 59 48 34 22 0 8', #
'CALL[ ]',
'PUSHW[ ] 4 75 59 48 34 22 0 8',
'CALL[ ]',
'SVTCA[0]',
'PUSHW[ ] 1 83 72 48 34 26 0 8',
'CALL[ ]',
'PUSHW[ ] 2 92 72 59 42 26 0 8',
'CALL[ ]',
'SVTCA[0]',
'PUSHW[ ] 5 6 7',
'CALL[ ]',
'PUSHW[ ] 0',
'DUP[ ]',
'RCVT[ ]',
'RDTG[ ]',
'ROUND[01]',
'RTG[ ]',
'WCVTP[ ]',
PUSHW[ ]  /* 3 values pushed */
15 11 1
DELTAC1[ ]
'MPPEM[ ]',
'PUSHW[ ] 72',
'GT[ ]',
'IF[ ]',
'PUSHB[ ] 1',
'ELSE[ ]',
'PUSHB[ ] 0',
'EIF[ ]',
'PUSHB[ ] 1',
'INSTCTRL[ ]'
]