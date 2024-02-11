/*******************************************************************
uart-calc-add.c

Template for simple task of serial minimal calculator (add operation
only for now) which receives two decimal unsigned numbers from serial
input (each terminated by new line) and prints sum of these two to
serial output terminated by single newline character.

The riscv64-unknown-elf-gcc compiler is required to build the code
  https://cw.fel.cvut.cz/wiki/courses/b35apo/documentation/start

The included Makefile can be used to build the project and run it
in the qtrvsim_cli simulator variant. To run ELF binary in qtrvsim_gui
use make to compile binary or run on command line
  riscv64-unknown-elf-gcc -ggdb -nostartfiles -nostdlib -static -mabi=ilp32 -march=rv32i -fno-lto -o uart-calc-add crt0local.S uart-calc-add.c -lgcc

Place file on path work/uart-calc-add/uart-calc-add.c in your
subject personal GIT repository.

Licence: Public Domain
 *******************************************************************/

#define _POSIX_C_SOURCE 200112L

#include <stdint.h>

/*
 * Next macros provides location of knobs and LEDs peripherals
 * implemented on QtRVSim simulator.
 *
 * More information can be found on page
 *   https://github.com/cvut/qtrvsim
 */


/*
 * Base address of the region where simple serial port (UART)
 * implementation is mapped in emulated RISC-V address space
 */
#define SERIAL_PORT_BASE   0xffffc000

/*
 * Byte offset of the 32-bit receive status register
 * of the serial port
 */
#define SERP_RX_ST_REG_o         0x00
/*
 * Mask of the bit which inform that received character is ready
 to be read by CPU.
 */
#define SERP_RX_ST_REG_READY_m    0x1
/*
 * Byte offset of the UART received data register.
 * When the 32-bit word is read the least-significant (LSB)
 * eight bits are represet last complete byte received from terminal.
 */

#define SERP_RX_DATA_REG_o        0x04
/*
 * Byte offset of the 32-bit transition status register
 * of the serial port
 */
#define SERP_TX_ST_REG_o         0x08
/*
 * Mask of the bit which inform that peripheral is ready to accept
 * next character to send. If it is zero, then peripheral is
 * busy by sending of previous character.
 */
#define SERP_TX_ST_REG_READY_m    0x1

/*
 * Byte offset of the UART transmit register.
 * When the 32-bit word is written the least-significant (LSB)
 * eight bits are send to the terminal.
 */
#define SERP_TX_DATA_REG_o        0x0c

/*
 * Base address of the region where knobs and LEDs peripherals
 * are mapped in the emulated RISC-V physical memory address space.
 */
#define SPILED_REG_BASE      0xffffc100

/* Valid address range for the region */
#define SPILED_REG_SIZE      0x00000100

/*
 * Byte offset of the register which controls individual LEDs
 * in the row of 32 yellow LEDs. When the corresponding bit
 * is set (value 1) then the LED is lit.
 */
#define SPILED_REG_LED_LINE_o           0x004

/*
 * The register to control 8 bit RGB components of brightness
 * of the first RGB LED
 */
#define SPILED_REG_LED_RGB1_o           0x010

/*
 * The register to control 8 bit RGB components of brightness
 * of the second RGB LED
 */
#define SPILED_REG_LED_RGB2_o           0x014

/*
 * The register which combines direct write to RGB signals
 * of the RGB LEDs, write to the keyboard scan register
 * and control of the two additional individual LEDs.
 * The direct write to RGB signals is orred with PWM
 * signal generated according to the values in previous
 * registers.
 */
#define SPILED_REG_LED_KBDWR_DIRECT_o   0x018

/*
 * Register providing access to unfiltered encoder channels
 * and keyboard return signals.
 */
#define SPILED_REG_KBDRD_KNOBS_DIRECT_o 0x020

/*
 * The register representing knobs positions as three
 * 8-bit values where each value is incremented
 * and decremented by the knob relative turning.
 */
#define SPILED_REG_KNOBS_8BIT_o         0x024

/*
 * The main entry into example program
 */
int main(int argc, char *argv[])
{

  /* the space for your code */

  return 0;
}

