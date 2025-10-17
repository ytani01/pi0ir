import pytest

from pi0ir import IrAnalyze


class TestAnalyze:
    """Test Analyze."""

    TEST_DIR = "tests"

    @pytest.fixture
    def analyzer(self):
        return IrAnalyze()

    def read_raw_data(self, file: str) -> list:
        """Read raw data file.

        ## file format
        ```
        # comment
        pulse 1234
        space 5678
        pulse 1234
        space 5678
        :
        ```
        """

        with open(f"{self.TEST_DIR}/{file}", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]

        raw_data = []
        for line in lines:
            """
            line format: "pulse 1234" or "space 1234"
            """
            (key_str, val_str) = line.split(maxsplit=1)
            if key_str.startswith("#"):
                # comment line
                continue
            try:
                val = int(val_str)
            except ValueError:
                continue

            if key_str == "pulse":
                raw_data.append([val])
            elif key_str == "space":
                raw_data[-1].append(val)

        return raw_data

    @pytest.mark.parametrize("raw_data_file, e_format", [
        ("raw_data-AEHA-1.txt", "AEHA"),
        ("raw_data-NEC-1.txt", "NEC"),
        ("raw_data-SONY-1.txt", "SONY"),
    ])
    def test_analyze1(self, analyzer, raw_data_file, e_format):
        """Test Analyze."""
        print("\n", raw_data_file, e_format)
        raw_data = self.read_raw_data(raw_data_file)
        # print(raw_data)
        result = analyzer.analyze(raw_data)
        print(analyzer.json_dumps())
        assert result["format"] == e_format
        assert result["buttons"]["button1"] is not None
