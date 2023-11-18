// Directives to make interresting windows visible
#pragma qtrvsim show registers
#pragma qtrvsim show memory
.globl  _start
.globl  array_size
.globl  array_start
.option norelax

.text

_start:
	la   a0, array_start
	la   a1, array_size
	lw   a1, 0(a1) // number of elements in the array

	addi x7, zero, -1 //outer loop counter
_outer:
	addi x7, x7, 1
	beq x7, a1, end_loop

	add x8, zero, zero //inner loop counter
	addi x9, a0, -4
	addi x6, a1, -2
	sub x6, x6, x7
	slli x6, x6, 2
	add x6, x6, a0
_inner:
	beq x9, x6, _outer

	addi x9, x9, 4
	lw a2, 0(x9)
	lw a3, 4(x9)

	slt x1, a2, a3
	beq x1, zero, _switch

	j _inner

_switch:
	sw a2, 4(x9)
	sw a3, 0(x9)
	j _inner

end_loop:
	ebreak           // stop the simulator
	j end_loop
	nop

.data
// .align    2 // not supported by QtRVSim yet

array_size:
.word	15
array_start:
.word	5, 3, 4, 1, 15, 8, 9, 2, 10, 6, 11, 1, 6, 9, 12

// Specify location to show in memory window
#pragma qtrvsim focus memory array_start