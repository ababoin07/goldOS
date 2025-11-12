# Custom CPU Specification

## Architecture
- **Endian:** Big-endian  
- **Registers:** 16 total (0–15)  
  - Registers **0–14** are general-purpose  
  - Register **15** is **read-only accumulator** (used for results)  
- **Word size:** 4 bytes (32 bits)  
- **Addressing:** 0-indexed byte addresses  
- **Instruction size:** 10 bytes (`op0 op1 a0 a1 a2 a3 b0 b1 b2 b3`)

## General Instruction Format
| Bytes | Meaning |
|--------|---------|
| `op0 op1` | Opcode (2 bytes) |
| `a0 a1 a2 a3` | Operand A (4 bytes) |
| `b0 b1 b2 b3` | Operand B (4 bytes) |

> ⚠️ Only the lowest byte of A or B (`a3`, `b3`) is used for register indices unless otherwise noted.

## 0x0000 – Reserved
**0x00 00:** Intentionally omitted to prevent execution of uninitialized memory.

## 0x0001 – 0x0004: Data Movement

**0x00 01 – LD***  
Load 4 bytes from memory into a register.  
- **A:** Memory address  
- **B:** Destination register (only `b3` used, clamped to 14)

**0x00 02 – LC***  
Load a 4-byte constant into a register.  
- **A:** Constant value  
- **B:** Destination register (only `b3` used, clamped to 14)

**0x00 03 – DR***  
Dump a register into memory.  
- **A:** Register index (only `a3` used, clamped to 14)  
- **B:** Memory address

**0x00 04 – CPY**  
Copy one register into another.  
- **A:** Source register (`a3`)  
- **B:** Destination register (`b3`)

## 0x0005 – 0x0009: Bitwise Operations
All results stored in **register 15 (accumulator)**.

| Opcode | Name | Operation |
|--------|------|-----------|
| 0x00 05 | OR* | `r15 = ra | rb` |
| 0x00 06 | AND | `r15 = ra & rb` |
| 0x00 07 | XOR | `r15 = ra ^ rb` |
| 0x00 08 | NAND | `r15 = ~(ra & rb)` |
| 0x00 09 | NOR | `r15 = ~(ra | rb)` |

## 0x000A – 0x000F: Arithmetic Operations
All results stored in **register 15 (accumulator)**.

| Opcode | Name | Operation |
|--------|------|-----------|
| 0x00 0A | NOT | `r15 = ~ra` |
| 0x00 0B | ADD | `r15 = ra + rb` |
| 0x00 0C | SUB | `r15 = ra - rb` |
| 0x00 0D | MUL | `r15 = ra * rb` |
| 0x00 0E | DIV | `r15 = ra / rb` |
| 0x00 0F | EXP | `r15 = ra ^ rb` |

## 0x0020 – 0x0023: Control Flow

**0x00 20 – JMP**  
Jump to absolute memory address.  
- **A:** Target address (in bytes)

**0x00 21 – JMR**  
Relative jump (current PC + signed A).  
- **A:** Signed offset (two’s complement)  

**0x00 22 – CMP**  
Conditional jump (absolute).  
If `r[a3] != 0`, jump to address in **B**.  

**0x00 23 – CMR**  
Conditional relative jump.  
If `r[a3] != 0`, jump to `PC + signed(B)`.

## 0x0030 – 0x0032: Stack Operations

**0x00 30 – PSH (Push)**  
Push a register’s value onto the stack.  
- **A:** Register to push (`a3`)  

**0x00 31 – POP**  
Pop the top of the stack into a register.  
- **A:** Destination register (`a3`)  

**0x00 32 – MOVSP**  
Adjust the stack pointer (SP).  
- **A:** Signed offset (two’s complement)  

## 0x0033 – 0x0034: Function Control

**0x00 33 – CALL**  
Push current PC to stack and jump to address in **A**.  
- **A:** Absolute address  

**0x00 34 – RET**  
Pop return address from stack and jump back.

## 0x0040 – 0x0045: Comparisons
Result stored in **register 15**:  
- `0xFFFFFFFF` if condition true  
- `0x00000000` otherwise  

| Opcode | Name | Condition |
|--------|------|-----------|
| 0x00 40 | GT | `ra > rb` |
| 0x00 41 | LT | `ra < rb` |
| 0x00 42 | EQ | `ra == rb` |
| 0x00 43 | NE | `ra != rb` |
| 0x00 44 | GE | `ra >= rb` |
| 0x00 45 | LE | `ra <= rb` |

## 0x0050 – 0x0051: Indirect Memory Access

**0x00 50 – LDI (Load Indirect)**  
Load value from address stored in register.  
- **A:** Register containing address  
- **B:** Destination register  

**0x00 51 – STI (Store Indirect)**  
Store value from register into memory at address in another register.  
- **A:** Source register (value)  
- **B:** Register containing address  

## Registers Summary
| Index | Purpose |
|-------|---------|
| 0–14 | General-purpose registers |
| 15 | Accumulator (read-only for arithmetic and logical results) |
| SP | Stack pointer (implementation-specific, not one of 0–15) |
| PC | Program counter (increments automatically) |

## Notes
- All arithmetic is **32-bit unsigned**, unless otherwise specified.  
- Signed values use **two’s complement** representation.  
- Program counter (PC) moves in **bytes**, not instructions.  
- Out-of-range register indices are **clamped to 14**.  
- Memory alignment is **not required** (but recommended for performance).
