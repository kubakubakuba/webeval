// The task is to process random value value injected into input_val
// unsigned integer variable and print corresponding hexadecimal value
// terminated by line feed (LF, '\n', 0x0a) character to the serial
// port (UART).

// Test algorithm in qtrvsim_gui program.
// Every CPU configuration conforming RISC-V architecture can be chosen.
// Test script select pipelined configuration with hazard unit but without
// cache.

// The script loads number to print into input_val global variable
// and the implemented algorithm converts it to series of 8 hexadecimal
// digits finalized by LF ('\n', 0x0a) character. Lowercase digits a to f
// are expected for nibbles within range 10 to 15.

// Directives to make interesting windows visible
#pragma qtrvsim show registers
#pragma qtrvsim show memory


// Serial port/terminal registers
// There is mirror of this region at address 0xffff0000
// to match QtSpim and Mars emulators

.equ SERIAL_PORT_BASE,      0xffffc000 // base address of serial port region

.equ SERP_RX_ST_REG,        0xffffc000 // Receiver status register
.equ SERP_RX_ST_REG_o,          0x0000 // Offset of RX_ST_REG
.equ SERP_RX_ST_REG_READY_m,       0x1 // Data byte is ready to be read
.equ SERP_RX_ST_REG_IE_m,          0x2 // Enable Rx ready interrupt

.equ SERP_RX_DATA_REG,      0xffffc004 // Received data byte in 8 LSB bits
.equ SERP_RX_DATA_REG_o,        0x0004 // Offset of RX_DATA_REG

.equ SERP_TX_ST_REG,        0xffffc008 // Transmitter status register
.equ SERP_TX_ST_REG_o,          0x0008 // Offset of TX_ST_REG
.equ SERP_TX_ST_REG_READY_m,       0x1 // Transmitter can accept next byte
.equ SERP_TX_ST_REG_IE_m,          0x2 // Enable Tx ready interrupt

.equ SERP_TX_DATA_REG,      0xffffc00c // Write word to send 8 LSB bits to terminal
.equ SERP_TX_DATA_REG_o,        0x000c // Offset of TX_DATA_REG

.option norelax

.globl    input_val

.text
.globl _start

_start:

	la   a0, input_val
	lw   a0, 0(a0) // number to print in hexadecimal to serial port

//Insert your code there

//Final infinite loop
end_loop:
	fence           // flush cache memory
	ebreak          // stop the simulator
	j end_loop
	nop


.data
// .align    2 // not supported by QtRVSim yet

input_val:
	.word 0x12345678

// Specify location to show in memory window
#pragma qtrvsim focus memory input_val
