import logging

from machine.datapath import Datapath
from machine.isa import Opcode


class ControlUnit:
    code: list = None
    program_counter: int = None
    buf_program_counter: int = None
    instruction_register: dict = None
    step_counter: int = None

    datapath: Datapath = None

    is_interrupted: bool = False
    interrupt_vec: dict = None
    input_symbol: int = None

    _tick: int = None
    _cur_opcode: Opcode = Opcode.NOP

    def __init__(self, code: list, datapath: Datapath, interrupt: dict):
        self.code = code
        self.program_counter = 0
        self.step_counter = 0
        self.datapath = datapath
        self.interrupt_vec = interrupt
        self._tick = 0

    def tick(self):
        self._tick += 1

    def cur_tick(self):
        return self._tick

    def signal_latch_pc(self, next: bool):
        if next:
            self.program_counter += 1
        else:
            self.program_counter = self.instruction_register["value"]

    def signal_latch_bpc(self):
        self.buf_program_counter = self.program_counter

    def signal_latch_sc(self, next: bool):
        if next:
            self.step_counter += 1
        else:
            self.step_counter = 0

    def signal_latch_ir(self):
        instr = self.code[self.program_counter]
        self.instruction_register = instr
        self._cur_opcode = Opcode[instr["opcode"]]

    def set_input(self, value):
        self.input_symbol = value

    def interrupt(self):
        logging.info("Interrupt!")
        self.is_interrupted = True
        self.datapath.interrupt()
        self.signal_latch_bpc()
        self.program_counter = self.interrupt_vec["value"]

    def restore(self):
        self.is_interrupted = False
        self.datapath.restore()
        self.program_counter = self.buf_program_counter

    def decode_and_execute(self):
        if self.step_counter == 0:
            if self.input_symbol is not None and not self.is_interrupted:
                self.interrupt()
                return

            self.signal_latch_ir()
            self.signal_latch_pc(next=True)
            self.signal_latch_sc(next=True)

        elif self.step_counter == 1:
            if self._cur_opcode == Opcode.HALT:
                raise StopIteration()

            elif self._cur_opcode == Opcode.NOP:
                self.signal_latch_pc(next=True)
                self.signal_latch_sc(next=False)

            elif self._cur_opcode == Opcode.JUMP:
                self.signal_latch_pc(next=False)
                self.signal_latch_sc(next=False)

            elif self._cur_opcode == Opcode.JZ:
                if self.datapath.zero():
                    self.signal_latch_pc(next=False)
                self.signal_latch_sc(next=False)

            elif self._cur_opcode == Opcode.RET:
                self.restore()
                self.signal_latch_sc(next=False)

            elif self._cur_opcode in [
                Opcode.LOAD,
                Opcode.SAVE,
                Opcode.SET_DA,
                Opcode.ADD,
                Opcode.SUB,
                Opcode.MOD,
            ]:
                self.datapath.signal_latch_da(self.instruction_register["value"])
                self.signal_latch_sc(next=True)

            elif self._cur_opcode == Opcode.LOAD_AC:
                self.datapath.signal_latch_da(self.datapath.accumulator)
                self.signal_latch_sc(next=True)

            elif self._cur_opcode == Opcode.SAVE_AC:
                self.datapath.signal_wr()
                self.signal_latch_sc(next=False)

            elif self._cur_opcode == Opcode.PUSH:
                self.datapath.signal_latch_acc(
                    from_memory=False, val=self.instruction_register["value"]
                )
                self.signal_latch_sc(next=False)

            elif self._cur_opcode == Opcode.INC:
                self.datapath.signal_alu(Opcode.ADD, 1)
                self.signal_latch_sc(next=False)

            elif self._cur_opcode == Opcode.CMP:
                self.datapath.signal_alu(Opcode.CMP, self.instruction_register["value"])
                self.signal_latch_sc(next=False)

            elif self._cur_opcode == Opcode.INPUT:
                self.datapath.signal_input(self.input_symbol)
                self.input_symbol = None
                self.signal_latch_sc(next=False)

            elif self._cur_opcode == Opcode.OUTPUT:
                self.datapath.signal_output()
                self.signal_latch_sc(next=False)

            else:
                raise ValueError(
                    f"Wrong opcode: {self._cur_opcode} at step {self.step_counter}"
                )

        elif self.step_counter == 2:
            if self._cur_opcode in [Opcode.LOAD, Opcode.LOAD_AC]:
                self.datapath.signal_latch_acc()

            elif self._cur_opcode == Opcode.SAVE:
                self.datapath.signal_wr()

            elif self._cur_opcode == Opcode.SET_DA:
                self.datapath.signal_latch_da(
                    self.code[self.datapath.data_address]["value"]
                )

            elif self._cur_opcode in [Opcode.ADD, Opcode.SUB, Opcode.MOD]:
                self.datapath.signal_alu(opcode=self._cur_opcode)

            else:
                raise ValueError(
                    f"Wrong opcode: {self._cur_opcode} at step {self.step_counter}"
                )

            self.signal_latch_sc(next=False)

        else:
            raise ValueError(f"Invalid step counter: {self.step_counter}")

    def __repr__(self):
        return (
            f"Tick: {self._tick:4} {self._cur_opcode.name:7} SC: {self.step_counter:3} PC: {self.program_counter:3} "
            f"AC: {self.datapath.accumulator:4} DA: {self.datapath.data_address:3} ZERO: {self.datapath.zero():1} "
            f"INTERRUPTED: {self.is_interrupted:1}"
        )
