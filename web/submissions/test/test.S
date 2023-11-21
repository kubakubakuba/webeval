.globl  _start
.globl  array_size
.globl  array_start
.option norelax

.text

_start:
	// get number 17 to register a0
	li a1, 10
	li a2, 12
	// add the two numbers and store the result in a3
	add a3, a1, a2
	// store the result in memory on adress 0x55
	sw a3, 0x55(a0)
	ebreak
	nop

.data

#pragma qtrvsim focus memory array_start
