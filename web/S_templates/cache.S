// Test algorithm in qtrvsim_gui program
// Select the CPU core configuration with delay-slot
// This setups requires (for simplicity) one NOP instruction after
// each branch and jump instruction (more during lecture about pipelining)

//Set the parameters of the cache by using #cache:policy,sets,words_in_blocks,ways,write_method
// on a separate line in your task submission.
//For example: #cache:lru,1,1,1,wb
// The cache size is limited to 16 words maximum.

// Directives to make interesting windows visible
#pragma qtrvsim show registers
#pragma qtrvsim show memory

.option norelax

.globl    array_size
.globl    array_start

.text
.globl _start

_start:

	la   a0, array_start
	la   a1, array_size
	lw   a1, 0(a1) // number of elements in the array

//Insert your code there

//Final infinite loop
end_loop:
	fence           // flush cache memory
	ebreak          // stop the simulator
	j end_loop


.data
// .align    2 // not supported by qtrvsim yet

array_size:
.word	15
array_start:
.word	5, 3, 4, 1, 15, 8, 9, 2, 10, 6, 11, 1, 6, 9, 12

// Specify location to show in memory window
#pragma qtrvsim focus memory array_size
