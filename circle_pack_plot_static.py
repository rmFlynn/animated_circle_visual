"""Reformat the data to work with flatly"""
import re
import pandas as pd
import numpy as np
import plotly.express as px
import seaborn as sns
# import libraries
import circlify2 as circlify
from circlify2 import circlify
import matplotlib.pyplot as plt
import pandas as pd

def read_reshape_data(file_names):
    data = pd.concat([pd.read_csv(file_name,
                           delimiter='\t')
                     for file_name in file_names]
                     ,axis=0)
    sampe_colums_re = "^[a-zA-Z]+_M[0-9]_C[0-9]_D[0-6]"
    data.set_index([i for i in data.columns
                    if not re.match("^[a-zA-Z]+_M[0-9]_C[0-9]_D[0-6]", i)],
                   inplace=True)
    data = pd.DataFrame(data.stack())
    data.columns = ['measure']
    data.reset_index(inplace=True)
    level_col = data.columns[-2]
    split_values = data[level_col].str.split('_')
    for i, col in enumerate(['Month', 'Mud', 'Core', 'Depth']):
        data[col] = split_values.apply(lambda x: x[i])
    data['Subsample'] = split_values.apply(
        lambda x: x[4] if len(x) > 4 else np.nan)
    data['Depth'].replace('D5', '5/6', inplace=True)
    data['Depth'].replace('D6', '5/6', inplace=True)
    data['Depth'] = data['Depth'].str.replace('D', '')
    data['Core'] = data['Core'].str.replace('C', '')
    data['Mud'] = data['Mud'].str.replace('M', '')
    data = data[data['Core'] == '1']
    data = data[~data['Depth'].isin(['2', '4'])]
    # data.drop(['#Bin', level_col, 'bin', 'Subsample', 'Core'],
    data = data[['metab', 'taxonomy', 'Month', 'Depth', 'measure']]
    data = data.groupby([i for i in data.columns if i != 'measure']).\
        mean().reset_index()
    return data

def get_color_map(input_seq, dark_to_light=True):
    color_sets = {'blue': px.colors.sequential.Blues,
                  'green': px.colors.sequential.Greens,
                  'red': px.colors.sequential.Reds,
                  'grey': px.colors.sequential.Greys,
                  'gold': px.colors.sequential.Oryel,
                 }
    colordf = pd.DataFrame({"color_string": input_seq.unique()})
    colordf['color_string'] = colordf['color_string'].\
        str.replace('\s+', '', regex=True)
    colordf['base'] = colordf['color_string'].str.\
        replace('\d+', '', regex=True)
    def give_colors(dfr, color):
        dfr = dfr[dfr['base'] == color].copy()
        count = len(dfr)
        if dark_to_light:
            dfr['color_code'] = color_sets[color][-1 * count:]
        else:
            dfr['color_code'] = color_sets[color][:count]
        return dfr

    colordf = pd.concat(
        [give_colors(colordf, color) for color in colordf['base'].unique()])
    colordf.drop('base', axis=1, inplace=True)
    return colordf

def temp_data_func():
    data = read_reshape_data([
        './all_mgens_mean_geTMM_w_metab_Rory_7April2021.tsv',
        './geTMM_ALLMUDS_14Feb2021_MEAN_BIN_counts_ge20_genes_transcribed_'
        'METHANOTROPHS (1).txt'
    ])
    data['Month_num'] = data['Month'].apply(
        lambda x: {'Jul': 7, 'Aug': 8, 'Sept': 9}[x])
    data = pd.merge(
        data,
        pd.DataFrame({'metab': data['metab'].unique(),
                      'color': sns.color_palette(
                          'cubehelix',
                          len(data['metab'].unique()))}),
        on='metab'
    )
    data['all'] = 'all'
    return data

def out_taxonomy(f, data, depth, metab):
    taxonomy_ids = {j:i for i, j in enumerate(data['taxonomy'].unique())}
    for tkey in taxonomy_ids:
        f.write('  plots[' + str(depth) +
              '].clumps[' + str(metab) +
              '].add_fireworks(' + str(taxonomy_ids[tkey]) +
              ', \'' + tkey +
              '\', ' + data[data['taxonomy'] == tkey]['color'].values[0]+
              ', ' + str(
                  {i['Month_num']: i['size']
               for _, i in data[data['taxonomy'] == tkey].iterrows()})+
              ');\n')

def out_metab(f, data, depth):
    metab_ids = {j:i for i, j in enumerate(data['metab'].unique())}
    for mkey in metab_ids:
        f.write('  plots[{}].add_clump({}, \'{}\');\n'.\
              format(depth, metab_ids[mkey], mkey))
        out_taxonomy(f, data[data['metab'] == mkey].copy(), depth,
                     metab_ids[mkey])

def out_depth(f, data):
    f.write("import {Plot, plots} from 'sketch'\n")
    f.write("export function populate_objects(){\n")
    depth_ids = {j:i for i, j in enumerate(['1', '3', '5/6'])}
    for dkey in depth_ids:
        # yield data[data[depth]]
        f.write('  plots[{}] = new Plot({}, "Depth {}");\n'.\
              format(depth_ids[dkey], depth_ids[dkey], dkey))
        out_metab(f, data[data['Depth'] == dkey].copy(), depth_ids[dkey])
    f.write("}")

def make_high(data, parents):
    parent = parents[0]
    if len(parents) < 2:
        return [{'id': par,
                 'datum': data[data[parent] == par]['measure'].sum(),
          }
         for par in data[parent].unique()]
    return [{'id': par,
             'datum': data[data[parent] == par]['measure'].sum(),
             'children': make_high(data[data[parent] == par], parents[1:])
      }
     for par in data[parent].unique()]

def add_cir_ax(ax, circles, lim = None):
    if lim is None:
        lim = max(
            max(
                abs(circle.x) + circle.r,
                abs(circle.y) + circle.r,
            )
            for circle in circles
        )
    lim += lim * 0.01
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    # Print circle the highest level (continents):
    for circle in circles:
        if circle.level != 2:
          continue
        x, y, r = circle
        ax.add_patch( plt.Circle((x, y), r, alpha=0.5, linewidth=2,
                                 color=hex_cl1.loc[circle.ex["id"], 'color']))
    hex_cl1.loc['aceto', 'color']
    for circle in circles:
        if circle.level != 3:
          continue
        x, y, r = circle
        label = circle.ex["id"]
        ax.add_patch( plt.Circle((x, y), r, alpha=0.5, linewidth=2,
                                 color=hex_cl2.loc[circle.ex["id"], 'color']))
    for circle in circles:
        if circle.level != 2:
          continue
        x, y, r = circle
        label = circle.ex["id"]
    return ax


def make_fig(all_circles, lim=None):
    fig, axs = plt.subplots(figsize=(16,14), ncols=3, nrows=3)
    # for i in range(3):
    #    for j in range(3):
    #        axs[i,j].axis('off')
    for i, mon in zip(range(3), ['Jul', 'Aug', 'Sept']):
        for j, dep in zip(range(3), ['1', '3', '5/6']):
            axs[j, i] = add_cir_ax(axs[j, i], all_circles[i*3 + j], lim)
    for ax, col in zip(axs[0], ['Jul', 'Aug', 'Sept']):
        ax.set_title(col)
    pad = 5
    for ax, row in zip(axs[:,0], ['1', '3', '5/6']):
        ax.annotate(row, xy=(0, 0.5), xytext=(-ax.yaxis.labelpad - pad, 0),
                    xycoords=ax.yaxis.label, textcoords='offset points',
                    size='large', ha='right', va='center')
    return fig, axs

data = temp_data_func()
data.sort_values('metab', inplace=True)
data['measure'] =  data['measure'].apply(lambda x: 0.1 if x <= 0 else x)
data_high = [make_high(data[  (data['Month'] == mon)
                            & (data['Depth'] == dep)
                            & (data['measure'] > 0)],
                       ['all', 'metab', 'taxonomy'])
             for mon in ['Jul', 'Aug', 'Sept']
             for dep in ['1', '3', '5/6']]

data_scale = [data[(data['Month'] == mon) &
                   (data['Depth'] == dep)]['measure'].sum()
             for mon in ['Jul', 'Aug', 'Sept']
             for dep in ['1', '3', '5/6']]

old_loca = {c.ex['id']: (c.x, c.y) for c in all_circles[0] if c.ex['id'] in data['metab'].unique()}
def get_old(x):
    if x in old_loca:
        return old_loca[x]
    return None, None

get_old('troph')

all_circles = [circlify.circlify(
    circ,
    show_enclosure=False,
    target_enclosure=circlify.Circle(x=0, y=0, r=rad, xo=None, yo=None)
) for circ, rad in zip(data_high, data_scale)]

[ circ[0]['id'] for circ, rad in zip(data_high, data_scale)]

hex_cl1 = data[['metab', 'color']].drop_duplicates().set_index('metab')
hex_cl2 = data[['taxonomy', 'color']].drop_duplicates().set_index('taxonomy')

fig, axs = make_fig(all_circles)
fig.show()

fig.savefig('unscaled_circles.png')


data_scale = [data[(data['Month'] == mon) &
                   (data['Depth'] == dep)]['measure'].sum()
             for mon in ['Jul', 'Aug', 'Sept']
             for dep in ['1', '3', '5/6']]

all_circles = [circlify.circlify(
    circ,
    show_enclosure=False,
    target_enclosure=circlify.Circle(x=0, y=0, r=rad)
) for circ, rad in zip(data_high, data_scale)]

fig, axs = make_fig(all_circles, lim=max(data_scale))
fig.savefig('scaled_circles.png')

data = temp_data_func()
data['measure'] = np.log(data['measure'] + 1)
data_scale = [data[(data['Month'] == mon) &
                   (data['Depth'] == dep)]['measure'].sum()
             for mon in ['Jul', 'Aug', 'Sept']
             for dep in ['1', '3', '5/6']]

all_circles = [circlify.circlify(
    circ,
    show_enclosure=False,
    target_enclosure=circlify.Circle(x=0, y=0, r=rad)
) for circ, rad in zip(data_high, data_scale)]

fig, axs = make_fig(all_circles, lim=max(data_scale))
fig.savefig('log_circles.png')
fig.show()








