import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace
import pandas as pd
import os

# Import the functions from tablify
# Assuming tablify.py is in the same directory or installed as a module
from tablify import main, build_data_table, json_to_html_table


class TestJsonToHtmlTable:
    """Test cases for json_to_html_table function"""

    def test_simple_data(self):
        """Test conversion of simple JSON data to HTML table"""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        html, headers = json_to_html_table(data)

        assert "myTable" in html
        assert "Alice" in html
        assert "Bob" in html
        assert headers == ["name", "age"] or headers == ["age", "name"]
        assert "<table" in html
        assert "<thead>" in html
        assert "<tbody>" in html

    def test_single_row(self):
        """Test HTML table generation with single row"""
        data = [{"id": 1, "value": "test"}]
        html, headers = json_to_html_table(data)

        assert "test" in html
        assert "1" in html
        assert len(headers) == 2

    def test_multiple_columns(self):
        """Test HTML table with many columns"""
        data = [
            {"col1": "a", "col2": "b", "col3": "c", "col4": "d", "col5": "e"}
        ]
        html, headers = json_to_html_table(data)

        assert len(headers) == 5
        for col in ["col1", "col2", "col3", "col4", "col5"]:
            assert col in html

    def test_special_characters_in_data(self):
        """Test handling of special characters in data"""
        data = [{"text": "Hello & goodbye", "symbol": "<tag>"}]
        html, headers = json_to_html_table(data)

        # Note: Current implementation doesn't escape HTML
        # This test documents current behavior
        assert "Hello & goodbye" in html
        assert "<tag>" in html

    def test_numeric_values(self):
        """Test handling of numeric values"""
        data = [{"int_val": 42, "float_val": 3.14}]
        html, headers = json_to_html_table(data)

        assert "42" in html
        assert "3.14" in html

    def test_none_values(self):
        """Test handling of None values"""
        data = [{"name": "Alice", "email": None}]
        html, headers = json_to_html_table(data)

        assert "Alice" in html
        assert "None" in html

    def test_empty_strings(self):
        """Test handling of empty strings"""
        data = [{"name": "", "value": "test"}]
        html, headers = json_to_html_table(data)

        assert "test" in html


class TestBuildDataTable:
    """Test cases for build_data_table function"""

    def test_basic_functionality(self):
        """Test basic data table building"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
            ]
            options = Namespace(includeHeaders=None)

            build_data_table(options, data, output_path)

            assert (output_path.parent / "output.json").exists()
            assert (output_path.parent / "output.csv").exists()
            assert (output_path.parent / "output.xlsx").exists()
            assert (output_path.parent / "output.html").exists()

    def test_all_file_formats_generated(self):
        """Test that all output formats are created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data"
            data = [{"id": 1, "value": "test"}]
            options = Namespace(includeHeaders=None)

            build_data_table(options, data, output_path)

            json_file = output_path.with_suffix('.json')
            csv_file = output_path.with_suffix('.csv')
            xlsx_file = output_path.with_suffix('.xlsx')
            html_file = output_path.with_suffix('.html')

            assert json_file.exists()
            assert csv_file.exists()
            assert xlsx_file.exists()
            assert html_file.exists()

    def test_json_output_content(self):
        """Test JSON output file content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
            ]
            options = Namespace(includeHeaders=None)

            build_data_table(options, data, output_path)

            with open(output_path.with_suffix('.json'), 'r') as f:
                output_data = json.load(f)

            assert len(output_data) == 2
            assert output_data[0]['name'] in ["Alice", "Bob"]

    def test_csv_output_content(self):
        """Test CSV output file content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
            ]
            options = Namespace(includeHeaders=None)

            build_data_table(options, data, output_path)

            df = pd.read_csv(output_path.with_suffix('.csv'))
            assert len(df) == 2
            assert 'name' in df.columns or 'age' in df.columns

    def test_xlsx_output_exists(self):
        """Test that XLSX file is created properly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [{"col1": "value1"}]
            options = Namespace(includeHeaders=None)

            build_data_table(options, data, output_path)

            xlsx_file = output_path.with_suffix('.xlsx')
            assert xlsx_file.exists()
            df = pd.read_excel(xlsx_file)
            assert len(df) == 1

    def test_html_output_contains_datatable_script(self):
        """Test that HTML output includes DataTables library"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [{"name": "Alice"}]
            options = Namespace(includeHeaders=None)

            build_data_table(options, data, output_path)

            with open(output_path.with_suffix('.html'), 'r') as f:
                html_content = f.read()

            assert "datatables.net" in html_content
            assert "jQuery" in html_content
            assert "col-toggle" in html_content

    def test_include_headers_filter(self):
        """Test filtering columns with includeHeaders"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [
                {"name": "Alice", "age": 30, "city": "NYC"},
                {"name": "Bob", "age": 25, "city": "LA"},
            ]
            options = Namespace(includeHeaders="name, age")

            build_data_table(options, data, output_path)

            df = pd.read_csv(output_path.with_suffix('.csv'))
            assert "name" in df.columns
            assert "age" in df.columns
            assert "city" not in df.columns

    def test_include_headers_with_extra_spaces(self):
        """Test includeHeaders parsing with extra spaces"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [{"col1": "a", "col2": "b", "col3": "c"}]
            options = Namespace(includeHeaders="  col1  ,  col2  ")

            build_data_table(options, data, output_path)

            df = pd.read_csv(output_path.with_suffix('.csv'))
            assert "col1" in df.columns
            assert "col2" in df.columns

    def test_include_headers_nonexistent_column(self):
        """Test handling of nonexistent columns in filter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [{"name": "Alice", "age": 30}]
            options = Namespace(includeHeaders="name, nonexistent")

            build_data_table(options, data, output_path)

            df = pd.read_csv(output_path.with_suffix('.csv'))
            assert "name" in df.columns
            assert "nonexistent" not in df.columns

    def test_empty_data_raises_error(self):
        """Test that empty data raises ValueError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            options = Namespace(includeHeaders=None)

            with pytest.raises(ValueError, match="Input JSON is null"):
                build_data_table(options, [], output_path)

    def test_none_data_raises_error(self):
        """Test that None data raises ValueError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            options = Namespace(includeHeaders=None)

            with pytest.raises(ValueError, match="Input JSON is null"):
                build_data_table(options, None, output_path)

    def test_html_column_toggle_checkboxes(self):
        """Test that HTML includes column toggle checkboxes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
            ]
            options = Namespace(includeHeaders=None)

            build_data_table(options, data, output_path)

            with open(output_path.with_suffix('.html'), 'r') as f:
                html_content = f.read()

            assert "columnToggle" in html_content
            assert "checkbox" in html_content
            assert "checked" in html_content

    def test_data_with_missing_keys(self):
        """Test handling of rows with missing keys"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [
                {"name": "Alice", "age": 30, "email": "alice@example.com"},
                {"name": "Bob", "age": 25},  # missing email
            ]
            options = Namespace(includeHeaders="name, age, email")

            build_data_table(options, data, output_path)

            df = pd.read_csv(output_path.with_suffix('.csv'))
            assert len(df) == 2
            assert pd.isna(df.loc[1, 'email']) or (df.loc[1, 'email'] is None)


class TestMain:
    """Test cases for main function"""

    def test_main_with_single_file(self):
        """Test main function with single JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            inputdir = Path(tmpdir) / "input"
            outputdir = Path(tmpdir) / "output"
            inputdir.mkdir()
            outputdir.mkdir()

            # Create input file
            input_data = [{"name": "Alice", "age": 30}]
            with open(inputdir / "data.json", "w") as f:
                json.dump(input_data, f)

            options = Namespace(
                pattern="*.json",
                outputFileStem="merged",
                includeHeaders=None
            )

            main(options, inputdir, outputdir)

            assert (outputdir / "merged.json").exists()
            assert (outputdir / "merged.csv").exists()

    def test_main_with_multiple_files(self):
        """Test main function merging multiple JSON files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            inputdir = Path(tmpdir) / "input"
            outputdir = Path(tmpdir) / "output"
            inputdir.mkdir()
            outputdir.mkdir()

            # Create multiple input files
            with open(inputdir / "file1.json", "w") as f:
                json.dump([{"name": "Alice", "age": 30}], f)

            with open(inputdir / "file2.json", "w") as f:
                json.dump([{"name": "Bob", "age": 25}], f)

            options = Namespace(
                pattern="*.json",
                outputFileStem="merged",
                includeHeaders=None
            )

            main(options, inputdir, outputdir)

            with open(outputdir / "merged.json", "r") as f:
                result = json.load(f)

            assert len(result) >= 2

    def test_main_deduplicates_records(self):
        """Test that main function removes duplicates"""
        with tempfile.TemporaryDirectory() as tmpdir:
            inputdir = Path(tmpdir) / "input"
            outputdir = Path(tmpdir) / "output"
            inputdir.mkdir()
            outputdir.mkdir()

            # Create files with duplicate data
            duplicate_record = {"name": "Alice", "age": 30}
            with open(inputdir / "file1.json", "w") as f:
                json.dump([duplicate_record], f)

            with open(inputdir / "file2.json", "w") as f:
                json.dump([duplicate_record], f)

            options = Namespace(
                pattern="*.json",
                outputFileStem="merged",
                includeHeaders=None
            )

            main(options, inputdir, outputdir)

            with open(outputdir / "merged.json", "r") as f:
                result = json.load(f)

            assert len(result) == 1

    def test_main_with_non_list_json_raises_error(self):
        """Test that non-list JSON raises ValueError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            inputdir = Path(tmpdir) / "input"
            outputdir = Path(tmpdir) / "output"
            inputdir.mkdir()
            outputdir.mkdir()

            # Create input file with dict instead of list
            with open(inputdir / "data.json", "w") as f:
                json.dump({"name": "Alice"}, f)

            options = Namespace(
                pattern="*.json",
                outputFileStem="merged",
                includeHeaders=None
            )

            with pytest.raises(ValueError, match="does not contain a list"):
                main(options, inputdir, outputdir)

    def test_main_with_custom_pattern(self):
        """Test main function with custom file pattern"""
        with tempfile.TemporaryDirectory() as tmpdir:
            inputdir = Path(tmpdir) / "input"
            outputdir = Path(tmpdir) / "output"
            inputdir.mkdir()
            outputdir.mkdir()

            # Create files with different extensions
            with open(inputdir / "data.json", "w") as f:
                json.dump([{"name": "Alice"}], f)

            with open(inputdir / "other.txt", "w") as f:
                json.dump([{"name": "Bob"}], f)

            options = Namespace(
                pattern="*.json",
                outputFileStem="merged",
                includeHeaders=None
            )

            main(options, inputdir, outputdir)

            # Should only process .json files
            with open(outputdir / "merged.json", "r") as f:
                result = json.load(f)

            assert any(item.get("name") == "Alice" for item in result)

    def test_main_preserves_data_integrity(self):
        """Test that main preserves data integrity through merge"""
        with tempfile.TemporaryDirectory() as tmpdir:
            inputdir = Path(tmpdir) / "input"
            outputdir = Path(tmpdir) / "output"
            inputdir.mkdir()
            outputdir.mkdir()

            input_data = [
                {"id": 1, "name": "Alice", "score": 95.5},
                {"id": 2, "name": "Bob", "score": 87.3},
            ]

            with open(inputdir / "data.json", "w") as f:
                json.dump(input_data, f)

            options = Namespace(
                pattern="*.json",
                outputFileStem="merged",
                includeHeaders=None
            )

            main(options, inputdir, outputdir)

            with open(outputdir / "merged.json", "r") as f:
                result = json.load(f)

            assert len(result) == 2
            assert any(item["name"] == "Alice" and item["score"] == 95.5 for item in result)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_unicode_characters(self):
        """Test handling of unicode characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [
                {"name": "François", "city": "Montréal"},
                {"name": "张三", "city": "北京"},
            ]
            options = Namespace(includeHeaders=None)

            build_data_table(options, data, output_path)

            df = pd.read_csv(output_path.with_suffix('.csv'))
            assert len(df) == 2

    def test_very_large_dataset(self):
        """Test handling of large datasets"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [{"id": i, "value": f"value_{i}"} for i in range(1000)]
            options = Namespace(includeHeaders=None)

            build_data_table(options, data, output_path)

            df = pd.read_csv(output_path.with_suffix('.csv'))
            assert len(df) == 1000

    def test_special_json_values(self):
        """Test handling of special JSON values like booleans"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [
                {"active": True, "deleted": False, "value": 0},
            ]
            options = Namespace(includeHeaders=None)

            build_data_table(options, data, output_path)

            df = pd.read_csv(output_path.with_suffix('.csv'))
            assert len(df) == 1

    def test_nested_json_structure(self):
        """Test handling of nested JSON structures"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            data = [
                {"name": "Alice", "address": {"city": "NYC", "zip": "10001"}},
            ]
            options = Namespace(includeHeaders=None)

            # This may create a column with dict representation
            build_data_table(options, data, output_path)

            assert (output_path.with_suffix('.csv')).exists()

    def test_duplicate_handling_with_different_order(self):
        """Test that duplicates are handled correctly regardless of key order"""
        with tempfile.TemporaryDirectory() as tmpdir:
            inputdir = Path(tmpdir) / "input"
            outputdir = Path(tmpdir) / "output"
            inputdir.mkdir()
            outputdir.mkdir()

            with open(inputdir / "file1.json", "w") as f:
                json.dump([{"name": "Alice", "age": 30}], f)

            with open(inputdir / "file2.json", "w") as f:
                json.dump([{"age": 30, "name": "Alice"}], f)

            options = Namespace(
                pattern="*.json",
                outputFileStem="merged",
                includeHeaders=None
            )

            main(options, inputdir, outputdir)

            with open(outputdir / "merged.json", "r") as f:
                result = json.load(f)

            # Should detect as duplicates due to sort_keys=True
            assert len(result) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])