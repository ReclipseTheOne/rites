"""Smoke tests for every rites module.

Run directly (`python test.py`); exits non-zero on the first failure so it
doubles as the CI gate across the Python version matrix. The goal is breadth
(import + exercise every public surface) rather than exhaustive correctness.
"""

import os
import tempfile

import rites

from rites.bitchain import BitChain
from rites.chrono import Chrono
from rites.logger import Logger, get_logger, get_sec_logger, get_tertiary_logger
from rites.rituals import Math, Printer, Spells


def test_package():
    assert isinstance(rites.version(), str) and rites.version()
    rites.about()  # just make sure it runs without raising
    print("[OK] rites (version/about)")


def test_bitchain():
    a = BitChain("1100")          # 12
    b = BitChain("1010")          # 10
    assert int(a) == 12
    assert a.to_bin() == "1100"
    assert int(a & b) == (12 & 10)
    assert int(a | b) == (12 | 10)
    assert int(a ^ b) == (12 ^ 10)
    assert int(~a) == (~12 & 0b1111)
    assert int(a << 2) == 48
    assert int(a >> 1) == 6
    assert a.slice(0, 2).to_bin() == "00"
    assert isinstance(a.to_bytes(), bytes)
    assert a.to_hex() == hex(12)
    assert int(a.mask(b, op="AND")) == (12 & 10)
    assert int(BitChain.apply_mask(a, b, op="OR")) == (12 | 10)
    print("[OK] bitchain.BitChain")


def test_chrono():
    chrono = Chrono()
    chrono.stopwatch(print=False)
    chrono.stopwatch(print=False)
    assert len(chrono.get_stopwatch_tabs()) == 2
    chrono.reset_stopwatch_tabs()
    assert chrono.get_stopwatch_tabs() == []

    @chrono.time_function("work")
    def work():
        return sum(range(1000))

    @chrono.time_function_ns()
    def work_ns():
        return sum(range(1000))

    work()
    work_ns()
    stats = chrono.get_function_timings("work")
    assert stats["count"] == 1
    assert "work_ns" in chrono.get_function_timings()
    chrono.reset_function_timings()
    assert chrono.get_function_timings() == {}
    print("[OK] chrono.Chrono")


def test_logger():
    with tempfile.TemporaryDirectory() as tmp:
        # handles_zipping disabled so we don't depend on atexit ordering vs tmp cleanup
        logger = Logger(tmp, log_name="Test", handles_zipping=False)
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.debug("debug message")
        logger.success("success message")
        logger.add_custom("trace", "TRC", 80, 80, 80)
        logger.custom("trace", "custom message")
        assert os.path.exists(os.path.join(tmp, "latest.log"))

        # chainable toggles
        logger.disable().enable().should_print(False).should_log(False)

    # factory helpers
    assert isinstance(get_logger(tempfile.gettempdir()), Logger)
    assert isinstance(get_sec_logger(tempfile.gettempdir()), Logger)
    # tertiary logger logs nowhere (path="") and disables file logging
    get_tertiary_logger().info("no-op")
    print("[OK] logger.Logger (+ factory helpers)")


def test_printer():
    p = Printer()
    p.print_info("info")
    p.print_warning("warning")
    p.print_error("error")
    p.print_debug("debug")
    p.print_success("success")
    p.add_style("note", "NTE", 120, 200, 255)
    p.print_custom("note", "custom styled line")
    assert p.get_style("note").word == "NTE"
    assert p.get_color("gray") is not None
    print("[OK] rituals.Printer")


def test_math():
    assert Math.split_into_primes(360) == [2, 2, 2, 3, 3, 5]
    assert Math.equalize_matrix([[1], [2, 3]]) == [[1, 0], [2, 3]]

    CN = Math.ComplexNumber
    s = CN(1, 2) + CN(3, 4)
    assert (s.real, s.imaginary) == (4, 6)
    assert str(CN(2, -3)) == "2 - 3i"
    assert isinstance(CN(2, 1) ** 2, CN)
    assert isinstance(Math.ComplexNumber.add_of(CN(1, 1), CN(2, 2)), CN)
    assert str(CN.fromString("3+4i")) == "3 + 4i"

    assert str(Math.Sqrt(8)) == "2√2"
    assert Math.Sqrt.aprox(9) == 3.0

    A = Math.Matrix([[1, 2], [3, 4]])
    assert (A + A).matrix == [[2, 4], [6, 8]]
    assert (A * A).matrix == [[7, 10], [15, 22]]
    assert (2 * A).matrix == [[2, 4], [6, 8]]
    assert A.transpose().matrix == [[1, 3], [2, 4]]
    assert Math.Matrix.unit_matrix(2).matrix == [[1, 0], [0, 1]]
    assert A.diagonal() == [1, 4]
    assert A.secondary_diagonal() == [2, 3]
    assert (A ** 2).matrix == (A * A).matrix
    assert Math.Matrix.diagonal_of([[1, 2], [3, 4]]) == [1, 4]
    assert str(A)  # exercise the pretty-printer
    print("[OK] rituals.Math (ComplexNumber/Sqrt/Matrix)")


def test_spells():
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("a.txt", "b.txt"):
            with open(os.path.join(tmp, name), "w") as f:
                f.write("x")
        assert Spells.get_file_count(tmp) == 2
        assert len(Spells.get_file_paths(tmp)) == 2

    # type enforcement (debug=False avoids the colored print path)
    Spells.enforce(5, int, debug=False)  # passes silently
    try:
        Spells.enforce("nope", int, debug=False)
    except TypeError:
        pass
    else:
        raise AssertionError("Spells.enforce did not raise on type mismatch")
    print("[OK] rituals.Spells")


def main():
    tests = [
        test_package,
        test_bitchain,
        test_chrono,
        test_logger,
        test_printer,
        test_math,
        test_spells
    ]
    for test in tests:
        test()
    print("\nAll module smoke tests passed.")


if __name__ == "__main__":
    main()
