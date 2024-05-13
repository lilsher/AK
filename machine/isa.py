import json
from enum import Enum

BITS = 32
MIN_SIGN = -(2 ** (BITS - 1))
MAX_SIGN = 2 ** (BITS - 1) - 1
MAX_UNSIGNED = 2**BITS - 1


class Opcode(Enum):
    HALT = 0
    JUMP = 1
    JZ = 2
    NOP = 3
    RET = 4

    LOAD = 10
    SAVE = 11
    LOAD_AC = 12
    PUSH = 13
    SET_DA = 14
    SAVE_AC = 15

    ADD = 20
    SUB = 21
    MOD = 22
    INC = 23
    CMP = 24

    INPUT = 30
    OUTPUT = 31

    STRING = 40
    NUMBER = 41
    BUFFER = 42
    VECTOR = 43


opcode_name = [e.name for e in Opcode]
opcode_values = [e.value for e in Opcode]


def write_code(filename: str, code: list):
    with open(filename, "w", encoding="utf-8") as file:
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        file.write("[" + ",\n ".join(buf) + "]")


def read_code(filename: str):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())
    return code
