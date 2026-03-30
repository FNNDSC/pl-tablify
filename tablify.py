#!/usr/bin/env python

from pathlib import Path
from argparse import ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter
from chris_plugin import chris_plugin, PathMapper
import json
import pandas as pd
import openpyxl


__version__ = '1.0.0'

DISPLAY_TITLE = r"""
       _        _        _     _ _  __       
      | |      | |      | |   | (_)/ _|      
 _ __ | |______| |_ __ _| |__ | |_| |_ _   _ 
| '_ \| |______| __/ _` | '_ \| | |  _| | | |
| |_) | |      | || (_| | |_) | | | | | |_| |
| .__/|_|       \__\__,_|_.__/|_|_|_|  \__, |
| |                                     __/ |
|_|                                    |___/ 
"""


parser = ArgumentParser(description='A ChRIS plugin to generate interactive tables from structured data files.',
                        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-p', '--pattern', default='**/*.json', type=str,
                    help='input file filter glob')
parser.add_argument('-i', '--includeHeaders', default='', type=str,
                    help='comma separated headers to be displayed in the output table')
parser.add_argument('-V', '--version', action='version',
                    version=f'%(prog)s {__version__}')


# The main function of this *ChRIS* plugin is denoted by this ``@chris_plugin`` "decorator."
# Some metadata about the plugin is specified here. There is more metadata specified in setup.py.
#
# documentation: https://fnndsc.github.io/chris_plugin/chris_plugin.html#chris_plugin
@chris_plugin(
    parser=parser,
    title='A ChRIS plugin to generate interactive tables from structured data files. ',
    category='',                 # ref. https://chrisstore.co/plugins
    min_memory_limit='100Mi',    # supported units: Mi, Gi
    min_cpu_limit='1000m',       # millicores, e.g. "1000m" = 1 CPU core
    min_gpu_limit=0              # set min_gpu_limit=1 to enable GPU
)
def main(options: Namespace, inputdir: Path, outputdir: Path):
    """
    *ChRIS* plugins usually have two positional arguments: an **input directory** containing
    input files and an **output directory** where to write output files. Command-line arguments
    are passed to this main method implicitly when ``main()`` is called below without parameters.

    :param options: non-positional arguments parsed by the parser given to @chris_plugin
    :param inputdir: directory containing (read-only) input files
    :param outputdir: directory where to write output files
    """

    print(DISPLAY_TITLE)

    # Typically it's easier to think of programs as operating on individual files
    # rather than directories. The helper functions provided by a ``PathMapper``
    # object make it easy to discover input files and write to output files inside
    # the given paths.
    #
    # Refer to the documentation for more options, examples, and advanced uses e.g.
    # adding a progress bar and parallelism.
    mapper = PathMapper.file_mapper(inputdir, outputdir, glob=options.pattern)
    for input_file, output_file in mapper:
        with open(input_file, "r") as f:
            data = json.load(f)
        #df = pd.DataFrame(data)
        include = getattr(options, "includeHeaders", None)

        if include and include.strip():
            columns = [col.strip() for col in include.split(",") if col.strip()]
        else:
            columns = list(data[0].keys())
        filtered_data = [
            {key: row.get(key) for key in columns if key in row}
            for row in data
        ]
        filtered_df = pd.DataFrame(filtered_data)
        filtered_df.to_csv(output_file.with_suffix('.csv'), index=False)
        filtered_df.to_excel(output_file.with_suffix('.xlsx'), index=False, engine="openpyxl")


        html_table, headers = json_to_html_table(filtered_data)
        checkboxes = "<div id='columnToggle'>"
        for i, col in enumerate(headers):
            checkboxes += f"""
            <label>
                <input type="checkbox" class="col-toggle" data-column="{i}" checked> {col}
            </label><br>
            """
        checkboxes += "</div>"
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
        <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
        </head>
        <body>

        <h3>Select Columns:</h3>
        {checkboxes}

        <br><br>

        {html_table}

        <script>
        $(document).ready(function() {{
            var table = $('#myTable').DataTable();

            $('.col-toggle').on('change', function() {{
                var column = table.column($(this).data('column'));
                column.visible(!column.visible());
            }});
        }});
        </script>

        </body>
        </html>
        """
        op_file_path = output_file.with_suffix('.html')

        with open(op_file_path, "w") as f:
            f.write(full_html)


def json_to_html_table(data):
    headers = data[0].keys()

    html = "<table id='myTable' class='display'>\n<thead>\n<tr>"

    # headers
    for h in headers:
        html += f"<th>{h}</th>"
    html += "</tr>\n</thead>\n<tbody>\n"

    # rows
    for row in data:
        html += "<tr>"
        for h in headers:
            html += f"<td>{row[h]}</td>"
        html += "</tr>\n"

    html += "</tbody>\n</table>"
    return html, list(headers)


if __name__ == '__main__':
    main()
