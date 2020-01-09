from collections import OrderedDict
from scipy.integrate import romberg
from itertools import chain
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import json

import datashader as ds
import datashader.transfer_functions as tf
import pandas as pd
import numpy as np
import base64
import datetime
import io
import re
import sys
from os.path import basename, splitext

from inspect import getsourcefile
from os.path import abspath

src_dir_path = basename(abspath(getsourcefile(lambda:0)))
sys.path.append(src_dir_path + '/../')
from tcx_converter import convert_to_csv

# Layout

external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    "/assets/style.css",
]


app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
server = app.server

def datashader_figs():
    return [
        html.Div(
            id="header",
            children=[
                html.Div(
                    [
                        html.H3(
                            "Visualize millions of points with datashader and Plotly"
                        )
                ],
                    className="eight columns",
                ),
                html.Div([html.Img(id="logo", src=app.get_asset_url("dash-logo.png"))]),
            ],
            className="row",
        ),
        html.Hr(),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            "Click and drag on the plot for high-res view of\
             selected data",
                            id="header-1",
                        ),
                        dcc.Graph(
                            id="graph-1", figure=fig1, config={"doubleClick": "reset"}
                        ),
                    ],
                    className="twelve columns",
                )
            ],
            className="row",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            children=[
                                html.Span(
                                    children=[" points selected"], id="header-2-p"
                                ),
                            ],
                            id="header-2",
                        ),
                        dcc.Graph(id="graph-2", figure=fig2),
                    ],
                    className="twelve columns",
                )
            ],
            className="row",
        ),
    ]

app.layout = html.Div(
    [
        html.Div([
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select File')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                # Allow multiple files to be uploaded
        multiple=True
            ),
            #TODO *datashader_figs()
            html.Div(id='selected-dataframe-container'),
        ]),
    ]
)

POWER_COLNAME = 'Power(Watts)'
CADENCE_COLNAME = 'Cadence(1/min)'
TIME_COLNAME = 'Time(s)'

#
USED_COLNAMES = [POWER_COLNAME, CADENCE_COLNAME, TIME_COLNAME]

TIME_MATCH_STR = 'time'

PERF_COLS_MATCH_STR = [
    'power',
    'cadence',
    'heart'
]

match_str_colname_map = OrderedDict(zip(PERF_COLS_MATCH_STR, USED_COLNAMES))

def import_csv(source, filename, src_type="filepath"):
    if src_type == 'filepath':
        src_in = source
    elif src_type == 'bytestr':
        src_in = io.StringIO(source)
    else:
        raise Exception("only sources of type filepath and bytestring permitted")
    raw_df = pd.read_csv(src_in, comment='#', encoding='utf-8')
    cols = raw_df.columns
    match_sel = [
        next((True for cn in PERF_COLS_MATCH_STR if
            (re.match(cn, col, flags=re.IGNORECASE)) is not None), False) for
        col in cols
    ]
    sel_df = raw_df.iloc[:, match_sel]
    dfTup = (filename, sel_df.rename(columns=match_str_colname_map))
    return dfTup

def import_tcx(source, src_type):
    csv_files = convert_to_csv(source, src_type)
    dfTup = tuple(import_csv(fname, fname) for fname in csv_files)
    return dfTup

# demo data generation
def _generate_data():
    n = 1000000
    max_points = 100000

    np.random.seed(2)
    cols = ["Signal"]  # Column name of signal
    start = 1456297053  # Start time
    end = start + n  # End time

    # Generate a fake signal
    time = np.linspace(start, end, n)
    signal = np.random.normal(0, 0.3, size=n).cumsum() + 50

    # Generate many noisy samples from the signal
    noise = lambda var, bias, n: np.random.normal(bias, var, n)
    data = {c: signal + noise(1, 10 * (np.random.random() - 0.5), n) for c in cols}

    # # Pick a few samples and really blow them out
    locs = np.random.choice(n, 10)

    # print locs
    data["Signal"][locs] *= 2
 
# _generate_data()

def power_stats(fit_df):
    t = fit_df[TIME_COLNAME]
    del_t = t.diff()
    del_t = del_t.iloc[:-1]
    p = fit_df[POWER_COLNAME].iloc[:-1]
    p_df = pd.concat((del_t, p), axis=1).dropna(axis=0)
    energy = p_df.sum(axis=0).sum()
    duration = p_df[TIME_COLNAME].sum()
    p_avg = energy / duration
    return {'average power (Watt)': p_avg, 'duration (s)': duration}



max_points = 100000

# read power - t csv
df = pd.read_csv('~/hobby_projects/tcx_to_csv/20180111T151701Z_Biking.csv', header=0, skiprows=9)

import pandas as pd


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    stringBuff = decoded.decode('utf-8')
    tcx_bytestring = bytes(bytearray(stringBuff, encoding = 'utf-8'))
    try:
        if 'tcx' in filename:
            # Assume that the user uploaded a TCX file
            dfTup = import_tcx(tcx_bytestring, src_type="string")
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            dfTup = tuple(import_csv(tcx_bytestring, filename, src_type="bytestr"))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return dfTup


# # Default plot ranges:
def _plot_ranges():
    x_range = (start, end)
    y_range = (1.2 * signal.min(), 1.2 * signal.max())
# _plot_ranges()

def setup_plot_canvas(empty=True):
    global cols
    cols = [POWER_COLNAME]
    # data = {c: signal + noise(1, 10 * (np.random.random() - 0.5), n) for c in cols}

    global time_start
    time_start = df[TIME_COLNAME].values[0]
    global time_end
    time_end = df[TIME_COLNAME].values[-1]

    global x_range
    x_range = (time_start, time_end)
    global y_range
    y_range = (0, df[POWER_COLNAME].max())

    global cvs
    cvs = ds.Canvas(x_range=(time_start, time_end), y_range=y_range)

    global aggs
    aggs = OrderedDict((c, cvs.line(df, TIME_COLNAME, c)) for c in cols)
    global img
    img = tf.shade(aggs[POWER_COLNAME])

    global arr
    arr = np.array(img)
    global z
    z = arr.tolist()

    # axes
    global dims
    dims = len(z[0]), len(z)

    global x
    x = np.linspace(x_range[0], x_range[1], dims[0])
    global y
    y = np.linspace(y_range[0], y_range[1], dims[0])

if df is not None:
    setup_plot_canvas()

fig1 = {
    "data": [
        {
            "x": x,
            "y": y,
            "z": z,
            "type": "heatmap",
            "showscale": False,
            "colorscale": [[0, "rgba(255, 255, 255,0)"], [1, "#a3a7b0"]],
        }
    ],
    "layout": {
        "margin": {"t": 50, "b": 20},
        "height": 250,
        "xaxis": {
            "showline": True,
            "zeroline": False,
            "showgrid": False,
            "showticklabels": True,
            "color": "#a3a7b0",
        },
        "yaxis": {
            "fixedrange": True,
            "showline": True,
            "zeroline": False,
            "showgrid": False,
            "showticklabels": True,
            "ticks": "",
            "color": "#a3a7b0",
        },
        "plot_bgcolor": "#23272c",
        "paper_bgcolor": "#23272c",
    },
}

fig2 = {
    "data": [
        {
            "x": x,
            "y": y,
            "z": z,
            "type": "heatmap",
            "showscale": False,
            "colorscale": [[0, "rgba(255, 255, 255,0)"], [1, "#75baf2"]],
        }
    ],
    "layout": {
        "margin": {"t": 50, "b": 20},
        "height": 250,
        "xaxis": {
            "fixedrange": True,
            "showline": True,
            "zeroline": False,
            "showgrid": False,
            "showticklabels": True,
            "color": "#a3a7b0",
        },
        "yaxis": {
            "fixedrange": True,
            "showline": True,
            "zeroline": False,
            "showgrid": False,
            "showticklabels": True,
            "ticks": "",
            "color": "#a3a7b0",
        },
        "plot_bgcolor": "#23272c",
        "paper_bgcolor": "#23272c",
    },
}


# Callbacks

#@app.callback( Output("header-2-p", "children"), [Input("graph-1", "relayoutData")],)
def selectionRange(selection):
    if (
        selection is not None
        and "xaxis.range[0]" in selection
        and "xaxis.range[1]" in selection
    ):
        x0 = selection["xaxis.range[0]"]
        x1 = selection["xaxis.range[1]"]
        sub_df = df[(df[TIME_COLNAME] >= x0) & (df[TIME_COLNAME] <= x1)]
        selection_stats = power_stats(sub_df)
        power = list(selection_stats.items())[0][1]
        print(selection_stats)
        num_pts = len(sub_df)
        if num_pts < max_points:
            number = "{:,}".format(
                abs(int(selection["xaxis.range[1]"]) - int(selection["xaxis.range[0]"]))
            )
            # number_print = " points selected between {0:,.4} and {1:,.4}".format(
            number_print = " Your average power for period {0:,.4}s..{1:,.4}s was {2:,.4} Watts".format(
                selection["xaxis.range[0]"], selection["xaxis.range[1]"], power
            )
        else:
            number = "{:,}".format(
                abs(int(selection["xaxis.range[1]"]) - int(selection["xaxis.range[0]"]))
            )
            number_print = " points selected. Select less than {0:}k \
            points to invoke high-res scattergl trace".format(
                max_points / 1000
            )
    else:
        number = "0"
        number_print = " points selected"
    return number_print
    # return number, number_print


# @app.callback(Output("graph-2", "figure"), [Input("graph-1", "relayoutData")])
def selectionHighlight(selection):
    new_fig2 = fig2.copy()
    if (
        selection is not None
        and "xaxis.range[0]" in selection
        and "xaxis.range[1]" in selection
    ):
        x0 = selection["xaxis.range[0]"]
        x1 = selection["xaxis.range[1]"]
        sub_df = df[(df[TIME_COLNAME] >= x0) & (df[TIME_COLNAME] <= x1)]
        num_pts = len(sub_df)
        if num_pts < max_points:
            shape = dict(
                type="rect",
                xref="x",
                yref="paper",
                y0=0,
                y1=1,
                x0=x0,
                x1=x1,
                line={"width": 0},
                fillcolor="rgba(165, 131, 226, 0.10)",
            )
            new_fig2["layout"]["shapes"] = [shape]
        else:
            new_fig2["layout"]["shapes"] = []
    else:
        new_fig2["layout"]["shapes"] = []
    # return new_fig2
    return None


# @app.callback(Output("graph-1", "figure"), [Input("graph-1", "relayoutData"), Input('loaded-dataframes', 'value')])
def draw_undecimated_data(selection, value):
    if value is None:
        raise PreventUpdate
    df = value[1]
    if (
        selection is not None
        and "xaxis.range[0]" in selection
        and "xaxis.range[1]" in selection
        and len(
            df[
                (df[TIME_COLNAME] >= selection["xaxis.range[0]"])
                & (df[TIME_COLNAME] <= selection["xaxis.range[1]"])
            ]
        )
        < max_points
    ):
        x0 = selection["xaxis.range[0]"]
        x1 = selection["xaxis.range[1]"]
        sub_df = df[(df[TIME_COLNAME] >= x0) & (df[TIME_COLNAME] <= x1)]
        num_pts = len(sub_df)
        new_fig1 = fig1.copy()
        high_res_data = [
            dict(
                x=sub_df[TIME_COLNAME],
                y=sub_df[POWER_COLNAME],
                type="scattergl",
                marker=dict(sizemin=1, sizemax=30, color="#a3a7b0"),
            )
        ]
        high_res_layout = new_fig1["layout"]
        high_res = dict(data=high_res_data, layout=high_res_layout)
    else:
        high_res = fig1.copy()
    return high_res

def jsonify_dfs(dfDictL):
    # newL = [{d['filename']: d['df'].to_dict()} for d in dfDictL]
    newL = [{filename: df.to_dict()} for (filename, df) in dfDictL]
    return json.dumps(newL)

@app.callback(Output('selected-dataframe-container', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def process_uploaded(list_of_contents, list_of_names, list_of_dates):
    #to_iterable = lambda a: a if isinstance(a, tuple) else (a,)
    if list_of_contents is not None:
        try:
            dfTupList = [
                parse_contents(c, n, d) for c, n, d in
                zip(list_of_contents, list_of_names, list_of_dates)
            ]
            dfTupList = list(chain(*dfTupList))
            print(dfTupList)
        except Exception as e:
            print("excepted: stuff")
            print(e)
            return None
        return [
            dcc.Dropdown(
                id='loaded-dataframes',
                options=[{'label': splitext(basename(filename))[0], 'value': filename} for (filename, df)
                        in dfTupList]
            ),
            html.Div(id='activity-jsons', children=jsonify_dfs(dfTupList), style={'display': 'none'})
        ]


if __name__ == "__main__":
    app.run_server(debug=True)
