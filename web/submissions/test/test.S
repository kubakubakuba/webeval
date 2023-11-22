.globl  _start
.option norelax

.text

_start:
	lw a2, 0x400(x0)
	lw a3, 0x404(x0)
	add a4, a2, a3
	sw a4, 0x408(a0)
	ebreak
	nop
