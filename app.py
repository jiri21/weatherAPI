import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, Input, Output, State, html, dcc, dash_table, callback
import requests
import json
import pandas as pd

external_stylesheets =['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]

app = Dash(__name__, external_stylesheets =[dbc.themes.BOOTSTRAP])

fig = px.scatter()  #plot for temperature and cloud fraction
fig2 = px.scatter() #plot for pressure and precipitation

FORECAST_INTERVAL_IN_HOURS = 12 
HEADERS = {
        'User-Agent': 'JiriB_cz',
        'From': 'lednice.vm@seznam.cz' 
}


#Convert user input into latitude, longitude
def get_coords_from_name(location):
    direct_geocoding_api_url = "http://api.openweathermap.org/geo/1.0/direct" 
    KEY = '0675256e8871d9171585956976ee70b8'  #SHOULD BE IN env FILE
    params = {
            "APPID": KEY,
            "q":location,
            }

    response = requests.get(direct_geocoding_api_url, params=params)
    if response.status_code == 200:
        data = json.loads(response.content)
        coords = [data[0]["lat"], data[0]["lon"]]
        return coords
    else:
        print('Error in communication with server.')


#Returns GEOGRAPHICAL data 
#geonames ... give DST offset to display data in local time (sunrise, sunset, and other data can be taken from this response)
def get_geo_data(coords_yr):

    geonames_url = 'http://api.geonames.org/timezoneJSON?formatted=true&lat=' + str(coords_yr[0]) + '&lng=' + str(coords_yr[1]) + '&username=' + HEADERS['User-Agent']
    response_geonames = requests.get(geonames_url)
    if response_geonames.status_code == 200: 
        print(f'geonames response = {response_geonames.status_code}')
        return json.loads(response_geonames.content)
    else:
        print('Error in communication with api.geonames.org')
    return json.loads(response_geonames.content)



#Returns WEATHER data 
def get_meteo_data(coords_yr):

    yrno_api_url = 'https://api.met.no/weatherapi/locationforecast/2.0/compact.json?lat=' + str(coords_yr[0]) + '&lon=' + str(coords_yr[1])
    response_yr = requests.get(yrno_api_url, headers=HEADERS)
    if response_yr.status_code == 200: 
        print(f'yr.no response = {response_yr.status_code}')
        return json.loads(response_yr.content)
    else:
        print('Error in communication with api.met.no.')
   

#Extraction of meteo data from response for given time interval
def extract_data(raw_geo_data, raw_meteo_data):
        
    weather_date = []
    weather_pressure = []
    weather_temperature = []
    weather_cloud = []
    weather_precipitation = []

    #find time offset due to daysaving time
    do = pd.tseries.offsets.DateOffset(hours = raw_geo_data['dstOffset'])

    for i in range(FORECAST_INTERVAL_IN_HOURS):
        weather_date.append(pd.to_datetime(raw_meteo_data['properties']['timeseries'][i]['time']) + do)
        weather_pressure.append(raw_meteo_data['properties']['timeseries'][i]['data']['instant']['details']['air_pressure_at_sea_level'])
        weather_temperature.append(raw_meteo_data['properties']['timeseries'][i]['data']['instant']['details']['air_temperature'])
        weather_cloud.append(raw_meteo_data['properties']['timeseries'][i]['data']['instant']['details']['cloud_area_fraction'])
        weather_precipitation.append(raw_meteo_data['properties']['timeseries'][i]['data']['next_1_hours']['details']['precipitation_amount'])
    
    day_forecast = pd.DataFrame(list(zip(weather_date, weather_temperature, weather_pressure, weather_precipitation, weather_cloud)), columns = ['time', 'temperature', 'pressure', 'precipitation', 'cloud_area_fraction'])
    
    return day_forecast


#WEBPAGE LAYOUT

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H1("Weather service"), 
                width=4), 
                justify='center',
                className="h-15",
            ),

        html.Hr(),

        dbc.Row(
            [
                dbc.Col(
                    html.Div(' ')
                ),
                dbc.Col(
                    html.Div(' ')
                ),
            ],
            className="h-15",
        ),

        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            dbc.Input(
                                placeholder='Search a city...',
                                debounce=True,
                                id='textarea-state-example',
                                type='text',
                                value='',
                                style={
                                    'display': 'inline-block',
                                    'background-color': 'white',
                                    'border-color': 'white',
                                    'color': 'black',
                                    'place-holder-color':'blue'
                                }
                            ),
                        )
                    ],
                ),

                dbc.Col(
                    [
                        html.Div(
                            id='textarea-example-output', 
                            style={
                                'whiteSpace': 'pre-line'
                            }
                        ),

                        dbc.Button(
                            "Search", 
                            color="dark", 
                            className="me-1", 
                            id='textarea-state-example-button', 
                            n_clicks=0
                        ),
                    ]
                ),
            
            
                dbc.Col(
                    html.Div(
                        id='textarea-state-example-output', 
                        style={'whiteSpace': 'pre-line'}
                    ),
                ),
            ],
            className="h-25",
        ),
        


        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        id = 'graf_1',
                        figure=fig
                        )          
                ),

                dbc.Col(
                    dcc.Graph(
                        id = 'graf_2',
                        figure=fig2
                    )
                )
            ],
            className="h-45",
        ), 
    ],
    style={"height": "100vh"},
)



#CALLBACK FUNCTIONS TO UPDATE WEBPAGE SECTIONS

#update weather info (text field in upper right)
@app.callback(
    Output('textarea-state-example-output', 'children'),
    Input('textarea-state-example-button', 'n_clicks'),
    State('textarea-state-example', 'value')
)
def update_output(n_clicks, value):
    if n_clicks > 0:

        coords = get_coords_from_name(value)
        geonames_data = get_geo_data(coords)
        weather_data = get_meteo_data(coords)

        weather_info = str(weather_data['properties']['timeseries'][0]['data']['instant']['details']['air_temperature']) + ' °C' + '\n' + \
                         'current conditions: ' + str(weather_data['properties']['timeseries'][0]['data']['next_1_hours']['summary']['symbol_code']) + '\n' + \
                         'forecast 6 hours: ' + str(weather_data['properties']['timeseries'][0]['data']['next_6_hours']['summary']['symbol_code']) + '\n' + \
                         'forecast 12 hours: ' + str(weather_data['properties']['timeseries'][0]['data']['next_12_hours']['summary']['symbol_code']) + '\n' + \
                         'wind speed: ' + str(weather_data['properties']['timeseries'][0]['data']['instant']['details']['wind_speed']) + ' m/s' + '\n' + \
                         'wind direction: ' + str(weather_data['properties']['timeseries'][0]['data']['instant']['details']['wind_from_direction'])
        
        return  value + ', ' + str(geonames_data['countryCode']) + '\n{}'.format(weather_info) #'Temperature: '.format(weather_yr['properties']['timeseries'][0]['data']['instant']['details']['air_temperature'])


#UPDATE WEATHER FORECAST GRAPHS
#update graph 1 - temperature, cloud fraction
@app.callback(
    Output('graf_1', 'figure'),
    Input('textarea-state-example-button', 'n_clicks'),
    State('textarea-state-example', 'value')
)
def update_graph1(n_clicks, value):
    
    #forecast_interval_in_hours = 12 
    coords = get_coords_from_name(value)
    fig = px.scatter()

    if n_clicks > 0:

        geonames_data = get_geo_data(coords)
        weather_data = get_meteo_data(coords)

        forecast = extract_data(geonames_data, weather_data)

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(x=forecast['time'], y=forecast['cloud_area_fraction'], name="cloud fraction"),
            secondary_y=False,
        )

        fig.add_trace(
            go.Scatter(x=forecast['time'], y=forecast["temperature"], name="temperature"),
            secondary_y=True,
        )

        fig.update_layout(
            title_text="Day weather forecast"
        )

        fig.update_xaxes(title_text="hour")
        fig.update_yaxes(title_text="<b>Cloud fraction</b> Pa", secondary_y=False)
        fig.update_yaxes(title_text="<b>Temperature</b> °C", secondary_y=True)
    
    return fig


#update graph 2 - pressure and precipitation
@app.callback(
    Output('graf_2', 'figure'),
    Input('textarea-state-example-button', 'n_clicks'),
    State('textarea-state-example', 'value')
)
def update_graph2(n_clicks, value):
    
    #forecast_interval_in_hours = 12 
    coords = get_coords_from_name(value)
    fig = px.scatter()

    if n_clicks > 0:

        geonames_data = get_geo_data(coords)
        weather_data = get_meteo_data(coords)
        
        forecast = extract_data(geonames_data, weather_data)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=forecast['time'], y=forecast['pressure'], name="pressure"),
            secondary_y=False,
        )
        fig.add_trace(
            go.Bar(x=forecast['time'], y=forecast["precipitation"], name="precipitation"),
            secondary_y=True,
        )
        fig.update_layout(
            title_text="Day weather forecast"
        )
        fig.update_xaxes(title_text="hour")

        fig.update_yaxes(title_text="<b>Pressure</b> Pa", secondary_y=False)
        fig.update_yaxes(title_text="<b>Precipitation</b> °C", secondary_y=True)
    
    return fig




if __name__ == "__main__":
     app.run_server(debug = True, port = 5006)
