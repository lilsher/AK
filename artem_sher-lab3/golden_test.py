import contextlib
import io
import logging
import os
import tempfile

import pytest

import simulation
import translator
from machine.isa import read_code


@pytest.mark.golden_test("golden/*.yml")
def test_main(
    golden,
    caplog,
    DEBUG_LIMIT=200,
    LIMIT=100000,
):
    """
    Test: poetry run pytest . -v
    Update tests: poetry run pytest . -v --update-goldens
    """
    caplog.set_level(logging.DEBUG)

    # Создаём временную папку для тестирования приложения.
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Готовим имена файлов для входных и выходных данных.
        source = os.path.join(tmpdirname, "source.txt")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target = os.path.join(tmpdirname, "target.out")

        # Записываем входные данные в файлы. Данные берутся из теста.
        with open(source, "w") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w") as file:
            file.write(golden["in_stdin"])

        # Запускаем транслятор и собираем весь стандартный вывод в переменную
        # stdout
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target)
            print("============================================================")
            simulation.main(
                target,
                input_stream,
                DEBUG_LIMIT,
                LIMIT,
            )

        # Выходные данные также считываем в переменные.
        code = read_code(target)

        # Проверяем, что ожидания соответствуют реальности.
        assert code == golden.out["out_code"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert caplog.text == golden.out["out_log"]
