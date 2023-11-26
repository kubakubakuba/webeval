.globl  _start

_start:
	lw a0, 0x400(x0)
	lw a1, 0x404(x0)
	add a2, a0, a1
	sw a2, 0x408(x0)
	ebreak
	nop
