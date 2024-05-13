import logging

from machine.isa import Opcode


class Datapath:
    code: list = None
    data_address: int = None
    accumulator: int = None
    buf_accumulator: int = None

    is_zero: bool = False

    output_buffer: list[int] = None

    immediate_value: int = None
    input_value: str = None

    def __init__(self, code):
        self.code = code
        self.data_address = 0
        self.accumulator = 0
        self.output_buffer = []
        self.immediate_value = 0

    def signal_latch_acc(self, from_memory: bool = True, val: int = None):
        if from_memory:
            self.accumulator = self.code[self.data_address]["value"]
        else:
            self.accumulator = val

        self.set_zero()

    def signal_latch_buf_acc(self):
        self.buf_accumulator = self.accumulator

    def signal_latch_da(self, val: int):
        self.data_address = val

    def signal_wr(self):
        self.code[self.data_address]["value"] = self.accumulator

    def signal_alu(self, opcode: Opcode, val: int = None):
        if val is None:
            val = self.code[self.data_address]["value"]

        if opcode == Opcode.ADD:
            self.accumulator += val
        elif opcode == Opcode.SUB:
            self.accumulator -= val
        elif opcode == Opcode.MOD:
            self.accumulator %= val
        elif opcode == Opcode.CMP:
            self.is_zero = self.accumulator == val
            return
        else:
            raise ValueError(f"Invalid alu opcode: {opcode}")

        self.set_zero()

    def signal_input(self, symbol):
        if symbol is None:
            raise EOFError("End of input file")
        logging.info(f"input: {chr(symbol) if symbol else ''}")
        self.signal_latch_acc(from_memory=False, val=symbol)

    def signal_output(self):
        symbol = self.accumulator
        self.output_buffer.append(symbol)
        logging.info(
            f"output: {''.join(map(lambda x: chr(x) if x < 256 else str(x), self.output_buffer))} << {symbol}"
        )

    def interrupt(self):
        self.signal_latch_buf_acc()

    def restore(self):
        self.signal_latch_acc(from_memory=False, val=self.buf_accumulator)

    def set_zero(self):
        self.is_zero = self.accumulator == 0

    def zero(self):
        return self.is_zero
