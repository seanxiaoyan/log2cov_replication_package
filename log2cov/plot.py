import pandas as pd
import numpy as np
from webcolors import hex_to_rgb
from plotly.offline import download_plotlyjs, init_notebook_mode, plot
import plotly_express as px 
import plotly.graph_objects as go # Import the graphical object


init_notebook_mode(connected=True) 


Node_label = ["Docker_Must","Docker_May","Docker_No","Nginx_Must","Nginx_May","Nginx_No", "Must_Must","Must_May","Must_No","May_Must","May_May","May_No","No_Must","No_May","No_No"]
Node_dict = {y:x for x,y in enumerate(Node_label)}

source = ["Docker_Must","Docker_Must","Docker_Must","Docker_May","Docker_May","Docker_May",
"Docker_No","Docker_No","Docker_No","Nginx_Must","Nginx_Must","Nginx_Must",
"Nginx_May","Nginx_May","Nginx_May",
"Nginx_No","Nginx_No","Nginx_No"]

target = ["Must_Must",'Must_May','Must_No','May_Must','May_May','May_No','No_Must',
'No_May','No_No',     'Must_Must','May_Must','No_Must','Must_May','May_May','No_May','Must_No','May_No','No_No']


values = [1510,0,19,0,4026,3998,35,7060,3662,           1510,0,35,0,4026,7060,19,3998,3662]
source_Node = [Node_dict[x] for x in source]
target_Node = [Node_dict[x] for x in target]

fig = go.Figure( 
    data=[go.Sankey( # The plot we are interest
        # This part is for the Node information
        node = dict( 
            label = Node_label
        ),
        # This part is for the link information
        link = dict(
            source = source_Node,
            target = target_Node,
            value = values
        ))])
# With this save the plots 
plot(fig,
     image_filename='sankey_plot_1', 
     image='png', 
     image_width=1000, 
     image_height=600
)
# And shows the plot
fig.show()