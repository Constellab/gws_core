import time
import unittest


class TimingTestResult(unittest.TextTestResult):
    """TestResult that records the wall-clock duration of each test."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timings: list[tuple[str, float]] = []
        self._start_time: float = 0.0

    def startTest(self, test: unittest.TestCase) -> None:
        self._start_time = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test: unittest.TestCase) -> None:
        elapsed = time.perf_counter() - self._start_time
        self.timings.append((test.id(), elapsed))
        super().stopTest(test)


class TimingTextTestRunner(unittest.TextTestRunner):
    """Runner that prints the N slowest tests after the run."""

    resultclass = TimingTestResult

    def __init__(self, *args, durations: int = 25, **kwargs):
        super().__init__(*args, **kwargs)
        self.durations = durations

    def run(self, test):
        result: TimingTestResult = super().run(test)
        if result.timings:
            slowest = sorted(result.timings, key=lambda item: item[1], reverse=True)[
                : self.durations
            ]
            stream = self.stream
            stream.writeln("")
            stream.writeln(f"Slowest {len(slowest)} tests:")
            total = sum(elapsed for _, elapsed in result.timings)
            for test_id, elapsed in slowest:
                pct = (elapsed / total * 100) if total > 0 else 0
                stream.writeln(f"  {elapsed:8.3f}s  ({pct:5.1f}%)  {test_id}")
            stream.writeln(f"Total test time: {total:.3f}s across {len(result.timings)} tests")
        return result
