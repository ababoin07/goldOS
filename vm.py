"""
Custom CPU Virtual Machine
==========================

Architecture:
- 16 registers (0-14 general-purpose, 15 = accumulator read-only)
- Big-endian, 4-byte words
- Memory addressed by bytes, max 4 GiB
- 10-byte instructions: op0 op1 a0 a1 a2 a3 b0 b1 b2 b3
- Stack support and function calls
- Indirect memory access (pointers)

Instruction set implemented:
- Data movement: LD*, LC*, DR*, CPY
- Arithmetic/logic: ADD, SUB, MUL, DIV, EXP, NOT, AND, OR*, XOR, NAND, NOR
- Control flow: JMP, JMR, CMP, CMR
- Stack: PSH, POP, MOVSP
- Functions: CALL, RET
- Comparisons: GT, LT, EQ, NE, GE, LE
- Indirect memory: LDI, STI

Usage:
python vm.py program.bin
"""

import sys
import struct

# -------------------------------
# VM Configuration
# -------------------------------

NUM_REGS = 16
ACC = 15
MEM_SIZE = 2**20  # Example 1 MiB memory, can go up to 2^32 in principle

# -------------------------------
# Helper Functions
# -------------------------------

def read_u32_be(b):
    """Read 4 bytes big-endian as unsigned int"""
    return struct.unpack(">I", b)[0]

def read_s32_be(b):
    """Read 4 bytes big-endian as signed int"""
    return struct.unpack(">i", b)[0]

def clamp_reg(r):
    """Clamp register index to 14"""
    return min(r, 14)

# -------------------------------
# VM Class
# -------------------------------

class VM:
    def __init__(self, memory_size=MEM_SIZE):
        self.memory = bytearray(memory_size)
        self.regs = [0] * NUM_REGS
        self.pc = 0
        self.sp = memory_size  # Stack grows downward
        self.running = True
        self.ops = {
            0x0001: self.op_ld,
            0x0002: self.op_lc,
            0x0003: self.op_dr,
            0x0004: self.op_cpy,
            0x0005: self.op_or,
            0x0006: self.op_and,
            0x0007: self.op_xor,
            0x0008: self.op_nand,
            0x0009: self.op_nor,
            0x000A: self.op_not,
            0x000B: self.op_add,
            0x000C: self.op_sub,
            0x000D: self.op_mul,
            0x000E: self.op_div,
            0x000F: self.op_exp,
            0x0020: self.op_jmp,
            0x0021: self.op_jmr,
            0x0022: self.op_cmp,
            0x0023: self.op_cmr,
            0x0030: self.op_psh,
            0x0031: self.op_pop,
            0x0032: self.op_movsp,
            0x0033: self.op_call,
            0x0034: self.op_ret,
            0x0040: self.op_gt,
            0x0041: self.op_lt,
            0x0042: self.op_eq,
            0x0043: self.op_ne,
            0x0044: self.op_ge,
            0x0045: self.op_le,
            0x0050: self.op_ldi,
            0x0051: self.op_sti,
        }

    # -------------------------------
    # Helper to fetch instruction
    # -------------------------------
    def fetch(self):
        if self.pc + 10 > len(self.memory):
            self.running = False
            return None, None, None
        instr = self.memory[self.pc:self.pc+10]
        opcode = (instr[0] << 8) | instr[1]
        a = instr[2:6]
        b = instr[6:10]
        return opcode, a, b

    # -------------------------------
    # Main run loop
    # -------------------------------
    def run(self):
        while self.running:
            opcode, a_bytes, b_bytes = self.fetch()
            if opcode is None:
                break
            self.pc += 10
            op_func = self.ops.get(opcode, None)
            if op_func is None:
                print(f"Unknown opcode {opcode:04X} at {self.pc-10}")
                self.running = False
            else:
                op_func(a_bytes, b_bytes)

    # -------------------------------
    # Instruction Implementations
    # -------------------------------

    # Data movement
    def op_ld(self, a, b):
        addr = read_u32_be(a)
        reg = clamp_reg(b[3])
        self.regs[reg] = read_u32_be(self.memory[addr:addr+4])

    def op_lc(self, a, b):
        const = read_u32_be(a)
        reg = clamp_reg(b[3])
        self.regs[reg] = const

    def op_dr(self, a, b):
        reg = clamp_reg(a[3])
        addr = read_u32_be(b)
        self.memory[addr:addr+4] = struct.pack(">I", self.regs[reg])

    def op_cpy(self, a, b):
        src = clamp_reg(a[3])
        dst = clamp_reg(b[3])
        self.regs[dst] = self.regs[src]

    # Bitwise operations (results -> r15)
    def op_or(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self.regs[ACC] = self.regs[r] | self.regs[s]

    def op_and(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self.regs[ACC] = self.regs[r] & self.regs[s]

    def op_xor(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self.regs[ACC] = self.regs[r] ^ self.regs[s]

    def op_nand(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self.regs[ACC] = ~(self.regs[r] & self.regs[s]) & 0xFFFFFFFF

    def op_nor(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self.regs[ACC] = ~(self.regs[r] | self.regs[s]) & 0xFFFFFFFF

    def op_not(self, a, b):
        r = clamp_reg(a[3])
        self.regs[ACC] = ~self.regs[r] & 0xFFFFFFFF

    # Arithmetic operations
    def op_add(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self.regs[ACC] = (self.regs[r] + self.regs[s]) & 0xFFFFFFFF

    def op_sub(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self.regs[ACC] = (self.regs[r] - self.regs[s]) & 0xFFFFFFFF

    def op_mul(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self.regs[ACC] = (self.regs[r] * self.regs[s]) & 0xFFFFFFFF

    def op_div(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self.regs[ACC] = self.regs[r] // max(self.regs[s],1)  # avoid div by zero

    def op_exp(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self.regs[ACC] = pow(self.regs[r], self.regs[s], 2**32)

    # Control flow
    def op_jmp(self, a, b):
        self.pc = read_u32_be(a)

    def op_jmr(self, a, b):
        offset = read_s32_be(a)
        self.pc += offset

    def op_cmp(self, a, b):
        reg = clamp_reg(a[3])
        addr = read_u32_be(b)
        if self.regs[reg] != 0:
            self.pc = addr

    def op_cmr(self, a, b):
        reg = clamp_reg(a[3])
        offset = read_s32_be(b)
        if self.regs[reg] != 0:
            self.pc += offset

    # Stack operations
    def op_psh(self, a, b):
        reg = clamp_reg(a[3])
        self.sp -= 4
        self.memory[self.sp:self.sp+4] = struct.pack(">I", self.regs[reg])

    def op_pop(self, a, b):
        reg = clamp_reg(a[3])
        self.regs[reg] = read_u32_be(self.memory[self.sp:self.sp+4])
        self.sp += 4

    def op_movsp(self, a, b):
        offset = read_s32_be(a)
        self.sp += offset

    # Function calls
    def op_call(self, a, b):
        addr = read_u32_be(a)
        self.sp -=4
        self.memory[self.sp:self.sp+4] = struct.pack(">I", self.pc)
        self.pc = addr

    def op_ret(self, a, b):
        self.pc = read_u32_be(self.memory[self.sp:self.sp+4])
        self.sp +=4

    # Comparisons
    def _set_acc(self, cond):
        self.regs[ACC] = 0xFFFFFFFF if cond else 0

    def op_gt(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self._set_acc(self.regs[r] > self.regs[s])

    def op_lt(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self._set_acc(self.regs[r] < self.regs[s])

    def op_eq(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self._set_acc(self.regs[r] == self.regs[s])

    def op_ne(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self._set_acc(self.regs[r] != self.regs[s])

    def op_ge(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self._set_acc(self.regs[r] >= self.regs[s])

    def op_le(self, a, b):
        r = clamp_reg(a[3])
        s = clamp_reg(b[3])
        self._set_acc(self.regs[r] <= self.regs[s])

    # Indirect memory
    def op_ldi(self, a, b):
        addr_reg = clamp_reg(a[3])
        dst_reg = clamp_reg(b[3])
        addr = self.regs[addr_reg]
        self.regs[dst_reg] = read_u32_be(self.memory[addr:addr+4])

    def op_sti(self, a, b):
        src_reg = clamp_reg(a[3])
        addr_reg = clamp_reg(b[3])
        addr = self.regs[addr_reg]
        self.memory[addr:addr+4] = struct.pack(">I", self.regs[src_reg])

# -------------------------------
# Main
# -------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python vm.py program.bin")
        sys.exit(1)

    vm = VM()
    with open(sys.argv[1], "rb") as f:
        prog = f.read()
        vm.memory[:len(prog)] = prog

    vm.run()
    print("Execution finished.")
    print("Registers:")
    for i, val in enumerate(vm.regs):
        print(f"r{i:02} = {val:#010x}")
