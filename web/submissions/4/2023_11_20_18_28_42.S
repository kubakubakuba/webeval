.globl  _start
.globl  array_size
.globl  array_start
.option norelax

.text

_start:
    la   a0, array_start    // Load address of the array
    lw   a1, array_size     // Load array size
    lw   a1, 0(a1)          // Get the actual size
    ebreak
    nop

.data
array_size:
    .word  15               // Array size
array_start:
    .word  5, 3, 4, 1, 15, 8, 9, 2, 10, 6, 11, 1, 6, 9, 12

// Specify location to show in memory window
#pragma qtrvsim focus memory array_start
