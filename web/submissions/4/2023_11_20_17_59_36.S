.globl  _start
.globl  array_size
.globl  array_start
.option norelax

.text

_start:
    la   a0, array_start    // Load address of the array
    lw   a1, array_size     // Load array size
    lw   a1, 0(a1)          // Get the actual size

    addi a1, a1, -1         // Decrement size for 0 indexing
    addi t0, a0, 4          // t0 = &array[1]

loop_outer:
    beq  a1, zero, end_loop // Exit loop if index is 0

    mv   t2, t0             // t2 = current element address
    lw   t3, 0(t2)          // t3 = current element value
    addi t2, t2, -4         // t2 = address of previous element

loop_inner:
    lw   t4, 0(t2)          // t4 = previous element value
    bge  t4, t3, insert     // Break if previous <= current
    sw   t4, 4(t2)          // Shift previous element right
    addi t2, t2, -4         // Move to the next previous element
    bge  t2, a0, loop_inner // Check if within array bounds

insert:
    sw   t3, 4(t2)          // Insert current element in correct position

    addi t0, t0, 4          // Move to the next element
    addi a1, a1, -1         // Decrement outer loop index
    j    loop_outer         // Repeat outer loop

end_loop:
    ebreak                  // Stop the simulator
    nop

.data
array_size:
    .word  15               // Array size
array_start:
    .word  5, 3, 4, 1, 15, 8, 9, 2, 10, 6, 11, 1, 6, 9, 12

// Specify location to show in memory window
#pragma qtrvsim focus memory array_start
