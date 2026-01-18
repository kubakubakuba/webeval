.globl _start
.option norelax

_start:
// Insert your code here
   	addi x1, x0, input   // You cannot use `la` because it contains of two instruction with a hazard.

   
// Don't modify any code below !!!

.data
.org 0x400

input:
	.word 5
output:
	.word 0