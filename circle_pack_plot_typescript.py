"""Reformat the data to work with flatly"""
import re
import pandas as pd
import numpy as np
import plotly.express as px
import seaborn as sns
# import libraries
from circlify import circlify
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


# sns.palplot(sns.color_palette('Set1', n_colors=len(data['metab'].unique()),
#                                   ))
# plt.show()
# sns.color_palette( 'cubehelix', 10).as_hex()
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
                          'Set1',
                          len(data['metab'].unique()))}),
        on='metab'
    )
    data['all'] = 'all'
    return data

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
        label = circle.ex["id"]
        ax.add_patch( plt.Circle((x, y), r, alpha=0.5, linewidth=2,
                                 color=hex_cl1.loc[circle.ex["id"], 'color']))
        ax.annotate(label, (x,y ) ,va='center', ha='center', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', pad=.5))
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


all_circles = [circlify.circlify(
    circ,
    show_enclosure=False,
    target_enclosure=circlify.Circle(x=0, y=0, r=rad)
) for circ, rad in zip(data_high, data_scale)]

hex_cl1 = data[['metab', 'color']].drop_duplicates().set_index('metab')
hex_cl2 = data[['taxonomy', 'color']].drop_duplicates().set_index('taxonomy')

# 'aceto', 'alkane', 'hydro', 'methanotroph', 'methyl', 'troph'

loc = [{c.ex['id']: (c.x, c.y) for c in cc if c.ex['id'] in data['metab'].unique()} for cc in all_circles]
x = loc[3]['methanotroph']
loc[3]['methanotroph'] = loc[3]['aceto']
loc[3]['aceto'] = x
for loc, cc in zip(loc, all_circles):
    for c in cc:
        if c.ex['id'] in loc:
            c.setxy(*loc[c.ex['id']])


circ_data = pd.concat([
    pd.DataFrame({
        'month': mon,
        'depth': dep,
        'name':cir.ex['id'],
        'level': 0 if cir.ex['id'] in data['metab'].unique() else 1,
        'x':cir.x,
        'y':cir.y,
        'r':cir.r
    }, index=[(i * 3) + j])
    for i, mon in enumerate([7, 8, 9])
    for j, dep in enumerate(['1', '3', '5/6'])
    for cir in all_circles[(i * 3) + j]
]).reset_index(drop=True)

circ_data = pd.merge(
    circ_data,
    pd.concat([
        data[['metab', 'color']].drop_duplicates().\
        rename(columns={'metab':'name'}),
        data[['taxonomy', 'color']].drop_duplicates().\
        rename(columns={'taxonomy':'name'})]),
    on='name')

circ_data.set_index(['depth', 'name', 'level'], inplace=True)
circ_data = pd.concat([
    pd.DataFrame({
        'depth': [i],
        'name': [j],
        'level': [k],
        'circCor':
        [{j[0]:list(j[1:])
          for j in circ_data.loc[(i, j, k), ['month', 'x', 'y', 'r']].values
          }],
        'color': [[round(m * 255) for m in circ_data.loc[(i, j, k), 'color'].unique()[0]]]
     },
    index=[0])
     for i, j, k in
     circ_data.index.unique()]
).reset_index(drop=True)

with open('./typescript/sketch/data.ts', 'w') as f:
    f.write("function populate_objects(){\n")
    for i, dat in circ_data.iterrows():
        f.write("  dataCircles[%i]"
                " = new DataCirc('%s', '%s', %i, color%s, %s)\n"
              %(i, dat['name'], dat['depth'], dat['level'],
                str(tuple(dat['color'])), str(dat['circCor'])
              ))
    f.write("}\n")
















