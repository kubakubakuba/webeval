// Test algorithm in qtrvsim_gui program
// Select the CPU core configuration to
//    Pipelined without hazard unit and cache
// This option select version where RAW dependencies which leads
// to hazards are not resolved in hardware, you need to schedule
// instruction execution according to the pipeline structure
// (classical 5-stage RISC-V) such way, that no dependency results
// in a hazard

// The script loads number of the last Fibonacci series element to compute
// into fibo_limit variable and expects computed series in memory starting
// at address fibo_series, the series has to be followed by at least
// one zero element

// Directives to make interesting windows visible
#pragma qtrvsim show registers
#pragma qtrvsim show memory

.option norelax

.globl    fibo_limit
.globl    fibo_series

.text
.globl _start

_start:

	la   a0, fibo_series // la is pseudoinstruction expanded
	la   a1, fibo_limit  // into two instructions with dependency
	                     // look for replacements in seminaries
	lw   a1, 0(a1) // number of elements in the array

//Insert your code here

//Final infinite loop
end_loop:
	fence           // flush cache memory
	ebreak          // stop the simulator
	j end_loop
	nop

.data
// .align    2 // not supported by QtRVSim yet

fibo_limit:
	.word 15
fibo_series:
	.skip 1000*4

// Specify location to show in memory window
#pragma qtrvsim focus memory fibo_limit
