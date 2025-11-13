// Matrix multiplication template

// Directives to make interesting windows visible
#pragma qtrvsim show registers
#pragma qtrvsim show memory

.option norelax

.globl    matrix_a_rows
.globl    matrix_a_cols
.globl    matrix_b_rows
.globl    matrix_b_cols
.globl    matrix_c_rows
.globl    matrix_c_cols
.globl    matrix_a_start
.globl    matrix_b_start
.globl    matrix_c_start

.text
.globl _start

_start:

//Insert your code here
	la a0, matrix_a_start


//Final infinite loop
end_loop:
	fence           // flush cache memory
	ebreak          // stop the simulator
	j end_loop


.data

matrix_a_rows:
.word	3
matrix_a_cols:
.word	3
matrix_b_rows:
.word	3
matrix_b_cols:
.word	3
matrix_c_rows:
.word	3
matrix_c_cols:
.word	3

matrix_a_start:
.word	1, 2, 3, 4, 5, 6, 7, 8, 9
matrix_b_start:
.word	1, 2, 3, 4, 5, 6, 7, 8, 9
matrix_c_start:
.word	0, 0, 0, 0, 0, 0, 0, 0, 0

// Specify location to show in memory window
#pragma qtrvsim focus memory array_size
