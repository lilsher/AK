import argparse

from machine.isa import Opcode, MAX_SIGN, MIN_SIGN, MAX_UNSIGNED, BITS, write_code


def get_meaningful_token(line: str) -> str:
    return line.split(";", 1)[0].strip()


def translate_data_part(token: str):
    variable, str_opcode, arg = token.split(" ", 2)
    opcode = Opcode[str_opcode]
    assert opcode in [
        Opcode.NUMBER,
        Opcode.STRING,
        Opcode.BUFFER,
        Opcode.VECTOR,
    ], f"Wrong instruction in data part {token}"

    if opcode == Opcode.NUMBER:
        num = int(arg)
        assert MIN_SIGN <= num <= MAX_SIGN, f"Wrong instruction argument: {token}"
        if num < 0:
            num = MAX_UNSIGNED + num
        tokens = [num]
    elif opcode == Opcode.STRING:
        tokens = [len(arg)] + [ord(c) for c in arg]
    elif opcode == Opcode.BUFFER:
        num = int(arg)
        assert 1 <= num <= MAX_UNSIGNED, f"Wrong instruction argument: {token}"
        tokens = [0] * num
    elif opcode == Opcode.VECTOR:
        tokens = [arg]
    else:
        raise ValueError(f"Wrong opcode: {opcode}")

    return variable, opcode, tokens


def translate_code_part(token: str):
    if " " in token:  # instruction with argument
        sub_tokens = token.split(" ")
        assert (
            len(sub_tokens) == 2
        ), f"Invalid instruction, check arguments amount: {token}"
        opcode = Opcode[sub_tokens[0]]
        arg = sub_tokens[1]
        if arg.isdigit():
            arg = int(arg)
            assert MIN_SIGN <= arg < MAX_SIGN, f"{BITS}-bit numbers only {token}"
            if arg < 0:
                arg = MAX_UNSIGNED + arg

        return opcode, arg
    else:  # instruction without argument
        opcode = Opcode[token]
        return opcode, None


def translate_stage_1(text: str):
    variables = {}
    labels = {}
    interrupt = None
    instructions = []

    code_stage = True

    for line in text.splitlines():
        token = get_meaningful_token(line)
        assert not (not code_stage and token == ".code"), ".code in wrong place"
        if token == "" or token == ".code:":
            continue

        if token == ".data:":
            code_stage = False
            continue

        if not code_stage:
            variable, opcode, data_part = translate_data_part(token)
            # handle interrupt
            if opcode == Opcode.VECTOR:
                interrupt = {
                    "name": variable,
                    "opcode": opcode.name,
                    "value": data_part[0],
                }
                continue

            assert variable not in variables, f"Redefinition of variable: {variable}"
            variables[variable] = len(instructions)
            for d in data_part:
                instructions.append(
                    {"index": len(instructions), "opcode": opcode.name, "value": d}
                )
        else:
            if token.endswith(":"):  # label
                label = token.strip(":")
                assert label not in labels, f"Redefinition of label: {label}"
                labels[label] = len(instructions)
            else:
                opcode, arg = translate_code_part(token)
                instructions.append(
                    {"index": len(instructions), "opcode": opcode.name, "value": arg}
                )

    return labels, variables, interrupt, instructions


def translate_stage_2(
    labels: dict, variables: dict, interrupt: dict, instructions: list
):
    if interrupt is not None:
        arg = interrupt["value"]
        assert arg in labels, f"Wrong label {arg}"
        interrupt["value"] = labels[arg]

    code = [interrupt]
    for ind, instr in enumerate(instructions):
        arg = instr["value"]
        if isinstance(arg, str):
            if arg in labels:
                arg = labels[arg]
            elif arg in variables:
                arg = variables[arg]
            else:
                raise ValueError(f"Wrong arg: {arg}")

            instr["value"] = arg
            code.append(instr)
        elif isinstance(arg, int):
            assert 0 <= arg <= MAX_UNSIGNED, f"{BITS}-bit numbers only {instr}"
            code.append(instr)
        elif arg is None:
            code.append(instr)
        else:
            raise ValueError(f"Wrong instruction argument: {arg}")

    return code


def translate(text: str):
    labels, variables, interrupt, instr = translate_stage_1(text)
    code = translate_stage_2(labels, variables, interrupt, instr)

    return code


def main(source: str, target: str):
    with open(source, "r") as f:
        text = f.read()

    code = translate(text)

    write_code(target, code)
    print("LoC:", len(text.split("\n")), "code_instr:", len(code))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Трансляция кода")
    parser.add_argument("source_file", help="Имя файла с кодом")
    parser.add_argument("target_file", help="Имя выходного файла")

    args = parser.parse_args()

    main(args.source_file, args.target_file)
