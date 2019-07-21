import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime

import pandas as pd
import plotly.graph_objs as go

# import the data and apply some small transformations
df = pd.read_csv("tweets.csv")
df.rename(columns={"date": "timestamp"}, inplace=True)
df["timestamp"] = df["timestamp"].apply(lambda x: datetime.strptime(x[4:10] + x[25:] + x[10:19], '%b %d %Y %H:%M:%S'))
df["date"] = df["timestamp"].apply(lambda x: x.date())
df.dropna(subset=["person"], axis=0, inplace=True)
aggs = {"salience": "mean", "magnitude": "mean", "sentiment_score": "mean"}
df = df.groupby(["date", "keyword", "location", "person"]).agg(aggs)
df.reset_index(drop=False, inplace=True)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# create the options for the dashboard filters
location_checklist_options = []
for location in df["location"].unique():
    location_checklist_options.append({'label': location, 'value': location})
list_of_locations = [entry["value"] for entry in location_checklist_options]

entity_selection_options = []
for entity in df["person"].unique():
    entity_selection_options.append({'label': entity, 'value': entity})
list_of_entities = [entry["value"] for entry in entity_selection_options]

keyword_options = []
for keyword in df["keyword"].unique():
    keyword_options.append({'label': keyword, 'value': keyword})
list_of_keywords = [entry["value"] for entry in keyword_options]

title_of_webpage = "Sentiment analysis of greek politicians"

# colours of the webpage
colours = {'background': '#17599c', 'color': '#FFFFFF'}

# colours of the line graph
colour_map = {"Tsipras":"#a83232","Mitsotakis":"#3244a8"}

app.layout = html.Div(
    style=colours,
    children=
    [
        # title
        html.H1(
            title_of_webpage,
            style={'textAlign':'center'}
            ),

        # container of filters
        html.Div(
            [
                # filter for location of tweet
                html.Div(
                    [
                    html.H4('Location of tweet'),
                    dcc.Checklist(
                        options=location_checklist_options,
                        value=list_of_locations,
                        id='checklist',
                    )
                    ],
                className="one-third column",
                style={'paddingLeft':'25px','textAlign':'left',"paddingBottom":"25px"}
                ),
                # filter for politician
                html.Div(
                    [
                        html.H4('Politician of interest'),
                        dcc.Checklist(
                            id='entity',
                            options=entity_selection_options,
                            value=list_of_entities,
                        ),
                    ],
                    className="one-third column",
                    style={'textAlign': 'middle', "paddingBottom": "25px"}
                ),
                # filter for keyword used
                html.Div(
                    [
                        html.H4('Keyword in tweet'),
                        dcc.Checklist(
                            options=keyword_options,
                            value=list_of_keywords,
                            id='keywords',
                        )
                    ],
                className="one-third column",
                style={'paddingRight':'25px','textAlign':'right', "paddingBottom":"25px"}
                )
            ],
            className='row'
        ),

        # creation of grapg
        html.Div(
            [
                dcc.Graph(
                    style={'height': 400},
                    id='graph-with-checklist'
                )
            ]
        )

    ]
)

# make the graph interactive
@app.callback(
    Output('graph-with-checklist', 'figure'),
    [Input('checklist', 'value'),
     Input('entity', 'value'),
     Input('keywords', 'value')]
)
def update_figure(checklist_location, entity_of_sentiment, keyword_list):
    # apply all filters
    filtered_df = df[df['location'].isin(checklist_location)]
    second_filter_df = filtered_df[filtered_df["person"].isin(entity_of_sentiment)]
    third_filter_df = second_filter_df[second_filter_df["keyword"].isin(keyword_list)]
    final_df = third_filter_df.groupby(["date","person"]).agg({"sentiment_score":"mean"})
    final_df.reset_index(drop=False,inplace=True)

    # small script to fill the missing dates for any person if any
    unique_dates = final_df["date"].unique()
    for name, group in final_df.groupby(["person"]):
        unique_dates_of_group = group["date"].unique()
        dates_to_add = sorted(set(unique_dates) - set(unique_dates_of_group))
        for date in dates_to_add:
            final_df = pd.concat(
                [final_df, pd.DataFrame({"date": [date], "person": [group.iloc[0, 1]], "sentiment_score": [0]})])
    final_df.reset_index(drop=True, inplace=True)

    # create the figure and layout
    figure = go.Figure(
        layout=go.Layout(
            title='Public Sentiment',
            showlegend=True,
            legend=go.layout.Legend(
                x=0,
                y=1.0
            ),
            margin=go.layout.Margin(l=40, r=0, t=40, b=30)
        )
    )
    # create as many lines as needed
    for v in entity_of_sentiment:
        figure.add_trace(
            go.Scatter(
                x=list(final_df["date"].unique()),
                y=list(final_df[final_df["person"] == v]["sentiment_score"]),
                name=v,
                marker={"color":colour_map[v]}
            )
        )
    return figure


if __name__ == '__main__':
    app.run_server(debug=True)
