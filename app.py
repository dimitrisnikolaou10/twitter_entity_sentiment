import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime

import pandas as pd
import plotly.graph_objs as go

df = pd.read_csv("tweets.csv")
df.rename(columns={"date": "timestamp"}, inplace=True)
df["timestamp"] = df["timestamp"].apply(lambda x: datetime.strptime(x[4:10] + x[25:] + x[10:19], '%b %d %Y %H:%M:%S'))
df["date"] = df["timestamp"].apply(lambda x: x.date())
df.dropna(subset=["object_of_sentiment"], axis=0, inplace=True)
aggs = {"salience": "mean", "magnitude": "mean", "sentiment_score": "mean"}
df = df.groupby(["date", "keyword", "location", "object_of_sentiment"]).agg(aggs)
df.reset_index(drop=False, inplace=True)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

location_checklist_options = []
for location in df["location"].unique():
    location_checklist_options.append({'label': location, 'value': location})

entity_selection_options = []
for entity in df["object_of_sentiment"].unique():
    entity_selection_options.append({'label': entity, 'value': entity})

title_of_webpage = "Sentiment analysis of greek politicians"

colours = {'background': '#17599c', 'color': '#FFFFFF'}

app.layout = html.Div(
    style=colours,
    children=
    [
        html.H1(
            title_of_webpage,
            style={'textAlign':'center'}
            ),

        html.Div(
            [
                html.Div(
                    [
                    html.H4('Location of tweet'),
                    dcc.Checklist(
                        options=location_checklist_options,
                        value=[location_checklist_options[0]["value"]],
                        id='checklist',
                    )
                    ],
                className="one-half column",
                style={'paddingLeft':'25px','textAlign':'left',"paddingBottom":"25px"}
                ),
                html.Div(
                    [
                    html.H4('Politician of interest'),
                    dcc.RadioItems(
                        id='entity',
                        options=entity_selection_options,
                        value=entity_selection_options[0]["value"],
                    ),
                    ],
                className="one-half column",
                style={'paddingRight':'25px','textAlign':'right', "paddingBottom":"25px"}
)
            ],
            className='row'
        ),

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

@app.callback(
    Output('graph-with-checklist', 'figure'),
    [Input('checklist', 'value'),
     Input('entity', 'value')]
)
def update_figure(checklist_location, entity_of_sentiment):
    filtered_df = df[df['location'].isin(checklist_location)]
    second_filter_df = filtered_df[filtered_df["object_of_sentiment"] == entity_of_sentiment]
    figure = go.Figure(
        data=[
            go.Scatter(
                x=list(second_filter_df["date"]),
                y=list(second_filter_df["sentiment_score"]),
                name='Sentiment'
                # marker=go.Scatter.Marker(
                #     color='rgb(55, 83, 109)'
                # )
            )
        ],
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
    return figure


if __name__ == '__main__':
    app.run_server(debug=True)
