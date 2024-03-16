.option norelax

.globl    vect_start
.globl    vect_len
.globl    vect_sum
.globl	  vect_min
.globl    vect_max

.text
.globl _start

_start:

	la   a0, vect_start
	la   a1, vect_size
	lw   a1, 0(a1) // number of elements in the array

//Insert your code here

//Final infinite loop
end_loop:
	fence           // flush cache memory
	ebreak          // stop the simulator
	j end_loop


.data

vect_len:
.word	15
vect_start:
.word	5, 3, 4, 1, 15, 8, 9, 2, 10, 6, 11, 1, 6, 9, 12
vect_sum:
.word	112
vect_min:
.word	1
vect_max:
.word	15
