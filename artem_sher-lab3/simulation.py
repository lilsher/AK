import argparse
import logging

from machine.control_unit import ControlUnit
from machine.datapath import Datapath
from machine.isa import read_code


def simulation(
    code: list,
    input_buffer: list,
    debug_limit: int,
    limit: int,
):
    """
    Prepare datapath and control unit

    Stop at:
    1. Halt -> StopIteration
    2. End of input -> EOFError
    3. Exceed the ticks limit
    """

    interrupt = code.pop(0)

    datapath = Datapath(code)
    control_unit = ControlUnit(code, datapath, interrupt)

    logging.debug(repr(control_unit))
    instructions = 0
    try:
        while control_unit.cur_tick() < limit:
            # check for interruption
            if input_buffer and control_unit.cur_tick() >= input_buffer[0][0]:
                control_unit.set_input(input_buffer.pop(0)[1])

            # instruction handling
            if control_unit.step_counter == 0:
                instructions += 1
            control_unit.decode_and_execute()
            if control_unit.cur_tick() < debug_limit:
                logging.debug(control_unit)
            elif control_unit.cur_tick() == debug_limit:
                logging.warning("Debug limit exceeded!")

            control_unit.tick()

    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if control_unit.cur_tick() >= limit:
        logging.warning("Limit exceeded!")
        pass

    output = "".join(
        map(lambda x: chr(x) if x < 256 else str(x), datapath.output_buffer)
    )
    logging.info(f"output_buffer: {output}")

    return output, instructions, control_unit.cur_tick()


def main(
    code_file: str,
    input_file: str,
    debug_limit: int,
    limit: int,
):
    code = read_code(code_file)
    input_buffer = []
    if input_file:
        with open(input_file, "r") as f:
            for line in f.readlines():
                tick, symbol = line.split()
                tick = int(tick)
                symbol = ord(symbol)
                input_buffer.append((tick, symbol))
            if input_buffer:
                input_buffer.append((tick + 100, 0))

    logging.info("Start simulation")
    output, instructions, ticks = simulation(
        code,
        input_buffer,
        debug_limit,
        limit,
    )
    logging.info("End simulation")

    print(output)
    print(f"Instructions: {instructions} Ticks: {ticks}")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)  # DEBUG | INFO

    parser = argparse.ArgumentParser(description="Симуляция процессора")
    parser.add_argument("code_file", help="Имя файла бинарным с кодом")
    parser.add_argument(
        "input_file", nargs="?", help="Имя входного файла (опционально)"
    )
    parser.add_argument(
        "--debug_limit", type=int, default=200, help="Лимит отладки (по умолчанию 200)"
    )
    parser.add_argument(
        "--limit", type=int, default=100000, help="Лимит тиков (по умолчанию 100000)"
    )

    args = parser.parse_args()

    main(
        args.code_file,
        args.input_file,
        args.debug_limit,
        args.limit,
    )
