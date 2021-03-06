import base64
import datetime
import io
import re
import sys

from os.path import basename, splitext
from collections import OrderedDict
from itertools import chain
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
from dash.exceptions import PreventUpdate
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import simplejson as json

import datashader as ds
import datashader.transfer_functions as tf
import pandas as pd
import numpy as np

from inspect import getsourcefile

sys.path.append("./tcx_to_csv")

from tcx_converter import convert_to_csv
from hiddendivdownloaderbutton import HiddenDivDownloaderButton

# Layout

external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    "/assets/style.css",
]

INVISIBLE = {"display": "none"}

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
        html.Hr(),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.P(
                                    "Click and drag segment to calculate average power",
                                    className="caption",
                                    id="header-1",
                                ),
                                dcc.Graph(
                                    id="graph-1", config={"doubleClick": "reset"}
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
                                    className="caption",
                                    id="header-2",
                                ),
                                dcc.Graph(id="graph-2", style=INVISIBLE),
                            ],
                            className="twelve columns",
                        )
                    ],
                    className="row", 
                ),
            ],
            id="graphing-container",
            style=INVISIBLE,
        ),
    ]


POWER_COLNAME = "Power(Watts)"
CADENCE_COLNAME = "Cadence(1/min)"
TIME_COLNAME = "Time(s)"

USED_COLNAMES = [POWER_COLNAME, CADENCE_COLNAME, TIME_COLNAME]

TIME_MATCH_STR = "time"

PERF_COLS_MATCH_STR = ["time", "power", "cadence", "heart"]

match_str_colname_map = OrderedDict(zip(PERF_COLS_MATCH_STR, USED_COLNAMES))


def _parseSelectedJSON(option_id, jsonStr):
    csvStr = json.loads(jsonStr)[option_id]
    csvBuff = io.StringIO(csvStr)
    return pd.read_csv(csvBuff)


def csvify_dfs(dfDictL):
    newL = {filename: df.to_csv() for (filename, df) in dfDictL}
    return json.dumps(newL, ignore_nan=True)


def jsonify_dfs(dfDictL):
    newL = {filename: df.to_dict() for (filename, df) in dfDictL}
    return json.dumps(newL, ignore_nan=True)


def import_csv(source, filename, src_type="filepath"):
    if src_type == "filepath":
        src_in = source
    elif src_type == "bytestr":
        src_in = io.StringIO(source)
    else:
        raise Exception("only sources of type filepath and bytestring permitted")
    raw_df = pd.read_csv(src_in, comment="#", encoding="utf-8")
    cols = raw_df.columns
    match_sel = [
        next(
            (
                True
                for cn in PERF_COLS_MATCH_STR
                if (re.match(cn, col, flags=re.IGNORECASE)) is not None
            ),
            False,
        )
        for col in cols
    ]
    sel_df = raw_df.iloc[:, match_sel]
    dfTup = (
        splitext(basename(filename))[0],
        sel_df.rename(columns=match_str_colname_map),
    )
    return dfTup


def import_tcx_mem(source):
    csv_files = convert_to_csv(source, src_type="string")
    dfTup = tuple(import_csv(csvStr, fname, "bytestr") for fname, csvStr in csv_files)
    return dfTup


# Default plot ranges:
def _plot_ranges(start, end, signal):
    x_range = (start, end)
    y_range = (1.2 * signal.min(), 1.2 * signal.max())
    return (x_range, y_range)


def power_stats(fit_df):
    t = fit_df[TIME_COLNAME]
    del_t = t.diff()
    del_t = del_t.iloc[:-1]
    p = fit_df[POWER_COLNAME].iloc[:-1]
    p_df = pd.concat((del_t, p), axis=1).dropna(axis=0)
    energy = p_df[POWER_COLNAME]
    duration = p_df[TIME_COLNAME]
    p_avg = np.average(energy, weights=duration)
    return {"average power (Watt)": p_avg, "duration (s)": duration}


max_points = 100000

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    stringBuff = decoded.decode("utf-8")
    bytestring = bytes(bytearray(stringBuff, encoding="utf-8"))
    try:
        if "tcx" in filename:
            # Assume that the user uploaded a TCX file
            dfTup = import_tcx_mem(bytestring)
        if "csv" in filename:
            # Assume that the user uploaded a CSV file
            dfTup = tuple(import_csv(bytestring, filename, src_type="bytestr"))
    except Exception as e:
        print("error parsing contents")
        raise e
    return dfTup


def setup_plot_canvas(df):
    cols = [POWER_COLNAME]
    time_start = df[TIME_COLNAME].values[0]
    time_end = df[TIME_COLNAME].values[-1]

    x_range = (time_start, time_end)
    y_range = (0, df[POWER_COLNAME].max())

    cvs = ds.Canvas(x_range=(time_start, time_end), y_range=y_range)

    aggs = OrderedDict((c, cvs.line(df, TIME_COLNAME, c)) for c in cols)
    img = tf.shade(aggs[POWER_COLNAME])

    arr = np.array(img)
    z = arr.tolist()

    # axes
    dims = len(z[0]), len(z)

    x = np.linspace(x_range[0], x_range[1], dims[0])
    y = np.linspace(y_range[0], y_range[1], dims[0])

    return (x, y, z)


def generateFig(x, y, z, scope):
    fullFig = scope != "full"
    fig = {
        "data": [
            {
                "x": x,
                "y": y,
                "z": z,
                "type": "heatmap",
                "showscale": False,
                "colorscale": [
                    [0, "rgba(255, 255, 255,0)"],
                    [1, ("#a3a7b0" if fullFig else "#75baf2")],
                ],
            }
        ],
        "layout": {
            "margin": {"t": 50, "b": 20},
            "height": 250,
            "xaxis": {
                "fixedrange": fullFig,
                "showline": True,
                "title": "Time (s)",
                "zeroline": False,
                "showgrid": True,
                "showticklabels": True,
                "color": "#a3a7b0",
                "automargin": True
            },
            "yaxis": {
                "fixedrange": True,
                "showline": True,
                "title": "Power (W)",
                "zeroline": False,
                "showgrid": True,
                "showticklabels": True,
                "ticks": "",
                "color": "#a3a7b0",
            },
            "plot_bgcolor": "#FFFFFF",
            "paper_bgcolor": "#FFFFFF",
        },
    }
    return fig


app.layout = html.Div(
    [
        html.Div(
            [
                dcc.Upload(
                    id="data-upload",
                    className="data-upload non-dropdown",
                    children=html.Div(["Drag and Drop or ", html.A("Select File")]),
                    style={
                        "height": "10rem",
                        "lineHeight": "10rem",
                        "borderWidth": "2px",
                        "padding": "1.5rem",
                        "fontWeight": "700",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                    },
                    # Allow multiple files to be uploaded
                    multiple=True,
                ),
                html.Div(
                    id="selected-dataframe-container",
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                            id="loaded-dataframes", searchable=False, style=INVISIBLE,
                                        ),
                                        html.Div(
                                            [
                                                HiddenDivDownloaderButton(
                                                    id="downloadable-div-store", label="Download CSV"
                                                ),
                                            ],
                                            id="button-div",
                                            className="non-dropdown",
                                            style={"display": "flex", "justify-content": "flex-end"},
                                        )
                                    ],
                                    className="twelve columns",
                                ),
                                # html.Button(id='plot-imported-btn', n_clicks=0, children='Plot'),
                                # html.Button(id='downloadable-div-store', n_clicks=0, children='Download CSV'),
                            ],
                            className="row",
                        ),
                        html.Div(id="activity-ids", style=INVISIBLE),
                        html.Div(id="dummy-callback-target", style=INVISIBLE),
                        *datashader_figs(),
                    ],
                ),
            ]
        ),
    ]
)

# Callbacks

app.clientside_callback(
    ClientsideFunction(
            namespace='clientside',
            function_name='focusPlots'
    ),
Output("dummy-callback-target", "title"), #Callback needs an output, so this is dummy
[Input("graph-2", "style")], #This triggers the javascript callback
)

@app.callback(
    Output("header-2", "children"),
    [Input("graph-1", "relayoutData")],
    [
        State("loaded-dataframes", "value"),
        State("downloadable-div-store", "hiddenDivData"),
    ],
)
def selectionRange(selection, value, jsonStr):
    if (
        selection is None
        or "xaxis.range[0]" not in selection
        or "xaxis.range[1]" not in selection
    ):
        # number = "0"
        number_print = None
    else:
        df = _parseSelectedJSON(value, jsonStr)
        x0 = selection["xaxis.range[0]"]
        x1 = selection["xaxis.range[1]"]
        sub_df = df[(df[TIME_COLNAME] >= x0) & (df[TIME_COLNAME] <= x1)]
        selection_stats = power_stats(sub_df)
        power = list(selection_stats.items())[0][1]
        num_pts = len(sub_df)
        if num_pts < max_points:
            number = "{:,}".format(
                abs(int(selection["xaxis.range[1]"]) - int(selection["xaxis.range[0]"]))
            )
            # number_print = " points selected between {0:,.4} and {1:,.4}".format(
            number_print = dcc.Markdown(
                "Average power **{0}s..{1}s**: **{2:,.4} Watts**".format(
                    *(
                        round(selection[sel_range], 0)
                        for sel_range in ["xaxis.range[0]", "xaxis.range[1]"]
                    ),
                    round(power, 2)
                )
            )
    return number_print


@app.callback(
    [Output("graph-2", "figure"), Output("graph-2", "style")],
    [Input("graph-1", "relayoutData")],
    [
        State("loaded-dataframes", "value"),
        State("downloadable-div-store", "hiddenDivData"),
    ],
)
def selectionHighlight(selection, value, jsonStr):
    if value is None:
        raise PreventUpdate
    df = _parseSelectedJSON(value, jsonStr)
    fig_args = setup_plot_canvas(df)
    fig2 = generateFig(*fig_args, scope="selection")
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
            fig2["layout"]["shapes"] = [shape]
        else:
            fig2["layout"]["shapes"] = []
    else:
        fig2["layout"]["shapes"] = []
    return (fig2, None)


@app.callback(
    Output("downloadable-div-store", "filename"), [Input("loaded-dataframes", "value")]
)
def updateDownloadFName(filename):
    return filename


@app.callback(
    [Output("graph-1", "figure"), Output("graphing-container", "style")],
    [Input("graph-1", "relayoutData"), Input("loaded-dataframes", "value")],
    [State("downloadable-div-store", "hiddenDivData")],
)
def draw_undecimated_data(selection, value, jsonStr):
    if value is None:
        raise PreventUpdate
    df = _parseSelectedJSON(value, jsonStr)
    fig_args = setup_plot_canvas(df)
    fig1 = generateFig(*fig_args, scope="full")
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
    return (high_res, None)


@app.callback(
    [Output("loaded-dataframes", "options"), Output("loaded-dataframes", "style")], [Input("activity-ids", "children")]
)
def update_options(storedJSON):
    if not storedJSON:
        raise PreventUpdate
    optionL = json.loads(storedJSON)
    return ([{"label": id, "value": id} for id in optionL], None)


@app.callback(
    [
        Output("activity-ids", "children"),
        Output("selected-dataframe-container", "style"),
        Output("downloadable-div-store", "hiddenDivData"),
    ],
    [Input("data-upload", "contents")],
    [State("data-upload", "filename"), State("data-upload", "last_modified")],
)
def process_uploaded(list_of_contents, list_of_names, list_of_dates):
    # to_iterable = lambda a: a if isinstance(a, tuple) else (a,)
    if list_of_contents is None:
        return (None, INVISIBLE, None)
    else:
        try:
            dfTupList = [
                parse_contents(c, n, d)
                for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)
            ]
            dfTupList = list(chain(*dfTupList))
        except Exception as e:
            raise e
            print(e)
            return None
        df_optionL = [data_id for (data_id, _) in dfTupList]
        optionJSON = json.dumps(df_optionL)
        # return (optionJSON, None, jsonify_dfs(dfTupList))
        return (optionJSON, None, csvify_dfs(dfTupList))


if __name__ == "__main__":
    app.run_server(debug=True)
