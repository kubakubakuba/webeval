.globl  _start
.globl  array_size
.globl  array_start
.option norelax

.text

_start:
    la   a0, array_start   // Load the address of the array
    la   a1, array_size    // Load the address of the array size
    lw   a1, 0(a1)         // Load the array size

    addi a1, a1, -1        // Decrease array size by 1 for loop condition
    li   x5, 1             // Initialize outer loop counter (i) to 1

_insertion_sort_outer:
    blt  x5, a1, end_loop  // Break if outer loop counter (i) >= array size

    mv   x6, x5            // Copy outer loop counter to inner loop counter (j)
    addi x6, x6, -1        // Decrease inner loop counter by 1

    slli x7, x5, 2         // Calculate offset for the key element
    add  x7, x7, a0
    lw   a2, 0(x7)         // Load key element

_insertion_sort_inner:
    bge  x6, zero, _inner_continue  // Break if inner loop counter (j) < 0
    slli x8, x6, 2
    add  x8, x8, a0
    lw   a3, 0(x8)         // Load array[j]

    blt  a2, a3, _inner_continue  // Break if key >= array[j]
    addi x9, x8, 4
    sw   a3, 0(x9)         // Shift array[j] to right
    addi x6, x6, -1        // Decrement inner loop counter (j)
    j    _insertion_sort_inner

_inner_continue:
    slli x10, x6, 2
    add  x10, x10, a0
    addi x10, x10, 4
    sw   a2, 0(x10)        // Insert key at array[j+1]

    addi x5, x5, 1         // Increment outer loop counter (i)
    j    _insertion_sort_outer

end_loop:
    ebreak                 // Stop the simulator
    j    end_loop
    nop

.data
// .align    2 // not supported by QtRVSim yet

array_size:
.word	15
array_start:
.word	5, 3, 4, 1, 15, 8, 9, 2, 10, 6, 11, 1, 6, 9, 12

// Specify location to show in memory window
#pragma qtrvsim focus memory array_start
