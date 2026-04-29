"""Read pytest JUnit XML reports.

`JUnitXmlReader` reads a single XML file. `JUnitXmlReportSet` reads every
`*.xml` file in a folder and aggregates totals across them.
"""

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass
class JUnitFailure:
    test_id: str
    kind: str  # "failure" or "error"
    message: str
    traceback: str

    def to_dict(self) -> dict[str, str]:
        return {
            "test_id": self.test_id,
            "type": self.kind,
            "message": self.message,
            "traceback": self.traceback,
        }


class JUnitXmlReader:
    """Wrap a pytest-generated JUnit XML file and expose totals and failures.

    The reader is tolerant: a missing file or malformed XML produces zero
    counts plus a single synthetic failure entry describing the problem,
    rather than raising.
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._tests_total = 0
        self._tests_failed = 0
        self._tests_errors = 0
        self._tests_skipped = 0
        self._failures: list[JUnitFailure] = []
        self._load_error: str = ""
        self._parse()

    @property
    def path(self) -> str:
        return self._path

    @property
    def name(self) -> str:
        """Stem of the XML filename — e.g. /tmp/foo/gws_core.xml -> 'gws_core'."""
        return os.path.splitext(os.path.basename(self._path))[0]

    @property
    def exists(self) -> bool:
        return os.path.exists(self._path)

    @property
    def parsed_successfully(self) -> bool:
        return self.exists and not self._load_error

    @property
    def tests_total(self) -> int:
        return self._tests_total

    @property
    def tests_failed(self) -> int:
        return self._tests_failed

    @property
    def tests_errors(self) -> int:
        return self._tests_errors

    @property
    def tests_skipped(self) -> int:
        return self._tests_skipped

    @property
    def tests_passed(self) -> int:
        return max(
            0,
            self._tests_total
            - self._tests_failed
            - self._tests_errors
            - self._tests_skipped,
        )

    @property
    def failures(self) -> list[JUnitFailure]:
        return list(self._failures)

    @property
    def is_success(self) -> bool:
        return self.parsed_successfully and self._tests_failed == 0 and self._tests_errors == 0

    def _parse(self) -> None:
        if not self.exists:
            return
        try:
            root = ET.parse(self._path).getroot()
        except ET.ParseError as exc:
            self._load_error = str(exc)
            self._failures.append(
                JUnitFailure(
                    test_id="<junit-xml-parse>",
                    kind="error",
                    message=f"Failed to parse JUnit XML: {exc}",
                    traceback="",
                )
            )
            return

        suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
        for suite in suites:
            self._tests_total += int(suite.get("tests", "0") or 0)
            self._tests_failed += int(suite.get("failures", "0") or 0)
            self._tests_errors += int(suite.get("errors", "0") or 0)
            self._tests_skipped += int(suite.get("skipped", "0") or 0)
            for case in suite.iter("testcase"):
                classname = case.get("classname", "")
                name = case.get("name", "")
                test_id = f"{classname}::{name}" if classname else name
                for kind in ("failure", "error"):
                    node = case.find(kind)
                    if node is not None:
                        self._failures.append(
                            JUnitFailure(
                                test_id=test_id,
                                kind=kind,
                                message=node.get("message", "") or "",
                                traceback=(node.text or "").strip(),
                            )
                        )


class JUnitXmlReportSet:
    """Read every `*.xml` file in a folder and expose aggregated test results.

    Per-file readers are accessible via `reports`; aggregated counts via the
    `tests_*` properties; combined failures via `failures`. Useful for reading
    the directory of XMLs produced by `gws server test-all --junit-dir <dir>`.
    """

    def __init__(self, folder: str) -> None:
        self._folder = folder
        self._reports: list[JUnitXmlReader] = []
        self._load()

    @property
    def folder(self) -> str:
        return self._folder

    @property
    def exists(self) -> bool:
        return os.path.isdir(self._folder)

    @property
    def reports(self) -> list[JUnitXmlReader]:
        return list(self._reports)

    def report(self, name: str) -> JUnitXmlReader | None:
        """Return the per-file report whose filename stem matches `name`."""
        for r in self._reports:
            if r.name == name:
                return r
        return None

    @property
    def tests_total(self) -> int:
        return sum(r.tests_total for r in self._reports)

    @property
    def tests_passed(self) -> int:
        return sum(r.tests_passed for r in self._reports)

    @property
    def tests_failed(self) -> int:
        return sum(r.tests_failed for r in self._reports)

    @property
    def tests_errors(self) -> int:
        return sum(r.tests_errors for r in self._reports)

    @property
    def tests_skipped(self) -> int:
        return sum(r.tests_skipped for r in self._reports)

    @property
    def failures(self) -> list[JUnitFailure]:
        out: list[JUnitFailure] = []
        for r in self._reports:
            out.extend(r.failures)
        return out

    @property
    def reports_total(self) -> int:
        return len(self._reports)

    @property
    def reports_passed(self) -> int:
        return sum(1 for r in self._reports if r.is_success)

    @property
    def reports_failed(self) -> int:
        return sum(1 for r in self._reports if not r.is_success)

    @property
    def is_success(self) -> bool:
        return bool(self._reports) and all(r.is_success for r in self._reports)

    def _load(self) -> None:
        if not self.exists:
            return
        for entry in sorted(os.listdir(self._folder)):
            if entry.lower().endswith(".xml"):
                self._reports.append(JUnitXmlReader(os.path.join(self._folder, entry)))
