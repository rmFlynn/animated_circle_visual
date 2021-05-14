"""Reformat the data to work with flatly"""
import re
from typing import BinaryIO
from io import StringIO
import pandas as pd
import numpy as np
import seaborn as sns
# import libraries
import matplotlib.pyplot as plt
import pandas as pd
from circlify import circlify


def read_reshape_data(file_names:list,
                      custom_color:pd.DataFrame = None)-> pd.DataFrame:
    """
    Loads one or several data files

    :param file_names: All csv file that contain data
    :returns: A dataframe reshaped and
    """
    data = pd.concat([pd.read_csv(file_name,
                           delimiter='\t')
                     for file_name in file_names]
                     ,axis=0)
    data.set_index([i for i in data.columns
                    if not re.match("^[a-zA-Z]+_M[0-9]_C[0-9]_D[0-6]", i)],
                   inplace=True)
    data = pd.DataFrame(data.stack())
    data.columns = ['measure']
    data.reset_index(inplace=True)
    split_values = data[data.columns[-2]].str.split('_')
    for i, col in enumerate(['Month', 'Mud', 'Core', 'Depth']):
        data[col] = split_values.apply(lambda x: x[i])
    data['Subsample'] = split_values.apply(
        lambda x: x[4] if len(x) > 4 else np.nan)
    # Combine depths D5 and D6
    data['Depth'].replace('D5', '5/6', inplace=True)
    data['Depth'].replace('D6', '5/6', inplace=True)
    # Remove caricatures
    data[['Depth', 'Core','Mud']] = data[['Depth', 'Core','Mud']].\
        replace({'[A-z]':''}, regex=True)
    data = data[data['Core'] == '1']
    data = data[~data['Depth'].isin(['2', '4'])]
    data = data[['metab', 'taxonomy', 'Month', 'Depth', 'measure']]
    data = data.groupby([i for i in data.columns if i != 'measure']).\
        mean().reset_index()
    data['Month_num'] = data['Month'].apply(
        lambda x: {'Jul': 7, 'Aug': 8, 'Sept': 9}[x])
    # Merge in colors
    if custom_color is None:
        custom_color = pd.DataFrame({'metab': data['metab'].unique(),
                      'color': sns.color_palette(
                          'Set1',
                          len(data['metab'].unique()))})
    data = pd.merge(
        data,
        custom_color,
        on='metab'
    )
    data['all'] = 'all'
    data.sort_values('metab', inplace=True)
    data['measure'] =  data['measure'].apply(lambda x: 0.1 if x <= 0 else x)
    data['show_name'] = data[['Depth', 'Month', 'taxonomy']].\
        apply(lambda x: (
               x == data.\
               sort_values(by='measure', ascending=False).\
               groupby(['Depth', 'Month']).\
               head(3).reset_index()[['Depth', 'Month', 'taxonomy']]
            ).all(axis=1).any(),
            axis=1
    )
    return data



def make_high(data, parents):
    """
    Turn the dataframe into a hierarchy

    :param data:
    :param parents:
    :returns:
    """
    parent = parents[0]
    if len(parents) < 2:
        return [{'id': par,
                  'show_name': data[data[parent] == par]['show_name'].any(),
                 'datum': data[data[parent] == par]['measure'].sum(),
          }
         for par in data[parent].unique()]
    return [{'id': par,
             'datum': data[data[parent] == par]['measure'].sum(),
             'show_name': False,
             'children': make_high(data[data[parent] == par], parents[1:])
      }
     for par in data[parent].unique()]

def make_circles(data: pd.DataFrame) -> list:
    """
    Uses the circlify library to covert data to circles

    :param data:
    :returns:
    """
    # make a hierarchy
    data_high = [make_high(data[  (data['Month'] == mon)
                                & (data['Depth'] == dep)
                                & (data['measure'] > 0)],
                           ['all', 'metab', 'taxonomy'])
                 for mon in ['Jul', 'Aug', 'Sept']
                 for dep in ['1', '3', '5/6']]
    # Make the radius
    data_rad = [data[(data['Month'] == mon) &
                       (data['Depth'] == dep)]['measure'].sum()
                 for mon in ['Jul', 'Aug', 'Sept']
                 for dep in ['1', '3', '5/6']]
    # make circles
    all_circles = [circlify.circlify(
        circ,
        show_enclosure=False,
        target_enclosure=circlify.Circle(x=0, y=0, r=rad)
    ) for circ, rad in zip(data_high, data_rad)]
    return all_circles

def get_hierarchy(data:pd.DataFrame) -> dict:
    """
    Count the parents and children

    :param data:
    :returns:
    """
    data_for_high = data[['metab', 'taxonomy']].drop_duplicates()
    assert not data_for_high.\
        set_index('metab').duplicated().any(), "taxonomy not unique to metab"
    return data_for_high.groupby('metab')['taxonomy'].apply(list).to_dict()

class CircleLoca():

    def __init__(self, data):
        """
        Keep and locate circles

        :param data:
        """
        self.all_circles =  make_circles(data)
        self.loc = [{c.ex['id']: (c.x, c.y) for c in cc if c.ex['id']}
                      for cc in self.all_circles]
        self.hierarchy = get_hierarchy(data)

    def move_metab(self, view, metab, new_loc):
        old_loc = self.loc[view][metab]
        dif = tuple(i - j for i,j in zip(new_loc, old_loc))
        for i in self.hierarchy[metab] + [metab]:
            self.loc[3][i] = tuple(i + j for i,j in zip(self.loc[3][i], dif))

    def set_circles(self):
        for i, circs in zip(self.loc, self.all_circles):
            for cir in circs:
                if cir.ex['id'] in i:
                    cir.setxy(*i[cir.ex['id']])
        return self.all_circles

def get_circle_data(all_circles, data) -> pd.DataFrame:
    """
    Reformat data from circlify back to DF

    :param all_circles:
    :param data:
    :returns:
    """
    circ_data = pd.concat([
        pd.DataFrame({
            'month': mon,
            'depth': dep,
            'name':cir.ex['id'],
            'show_name':cir.ex['show_name'],
            'level': 0 if cir.ex['id'] == 'all' else\
            1 if cir.ex['id'] in data['metab'].unique() else 2,
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
            rename(columns={'taxonomy':'name'}),
            pd.DataFrame({'name':['all'],
                          'color':[(0, 0, 0)]}, index=[0])
        ]),
        on='name')
    circ_data.set_index(['depth', 'name', 'level'], inplace=True)
    circ_data = pd.concat([
        pd.DataFrame({
            'depth': [i],
            'name': [j],
            'level': [k],
            'circCor':
            [{c[0]:list(c[1:])
              for c in circ_data.loc[(i, j, k), ['month', 'x', 'y', 'r']].\
              values
              }],
            'color': [circ_data.loc[(i, j, k), 'color'].unique()[0]],
            'show_name': [{c[0]:c[1]
              for c in circ_data.loc[(i, j, k), ['month', 'show_name']].\
                           values
              }],
         },
        index=[0])
         for i, j, k in
         circ_data.index.unique()]
    ).reset_index(drop=True)
    return circ_data

#######################
# Dynamic figure code #
#######################

def write_to_typescript(circ_data: pd.DataFrame, ts_file: BinaryIO) -> None:
    """
    Coverts circle_data into type script code that can be used with the
    interactive visual

    :param circ_data:
    :param ts_file:
    """
    ts_file.write("function populate_objects(){\n")
    # Add circles
    data =  circ_data.copy()
    data['color'] = data['color'].apply(lambda x: [round(i * 255)for i in x])
    for i, dat in data.iterrows():
        ts_file.write("  dataCircles[%i]"
                " = new DataCirc('%s', '%s', %i, color%s, %s, %s, %s)\n"
              %(i, dat['name'], dat['depth'], dat['level'],
                str(tuple(dat['color'])), str(dat['circCor']),
                str(dat['show_name']).lower(), str(dat['label_y'])
              ))
    # Add legend
    for i, dat in data[data['level'] == 1][['name', 'color']].\
             groupby('name').first().reset_index().iterrows():
        ts_file.write("  legend[%i] = new LegendLine('%s', color%s, %i)\n"
              %(i, dat['name'], str(tuple(dat['color'])), i))
    ts_file.write("}\n")

#######################
# Statics figure code #
#######################

def make_fig(in_data, global_lim=True, check_values=False):
    if global_lim:
        lim = in_data['circCor'][in_data['name'] == 'all'].apply(
            lambda x: max([x[k][2] for k in x])).max()
    else:
        lim = None
    fig, axs = plt.subplots(figsize=(16,14), ncols=3, nrows=3)
    for i, mon in enumerate([7, 8, 9]):
        for j, dep in enumerate(['1', '3', '5/6']):
            axs[j, i] = add_cir_ax(axs[j, i], in_data, mon, dep,
                                   lim, check_values)
    for ax, col in zip(axs[0], ['Jul', 'Aug', 'Sept']):
        ax.set_title(col)
    pad = 5
    for ax, row in zip(axs[:,0], ['1', '3', '5/6']):
        ax.annotate(row, xy=(0, 0.5), xytext=(-ax.yaxis.labelpad - pad, 0),
                    xycoords=ax.yaxis.label, textcoords='offset points',
                    size='large', ha='right', va='center')
    return fig, axs

def add_cir_ax(ax, in_data, mon, dep, lim = None, check_values=False):
    data = in_data[in_data['depth'] == dep].copy()
    data = pd.merge(
        data,
        pd.DataFrame(
            data['circCor'].apply(lambda x: x[mon]).values.tolist(),
            index=data.index,
            columns=['x', 'y', 'r']),
        left_index=True,
        right_index=True
    ).drop('circCor', axis=1)
    if lim is None:
        lim =  data['r'].max()
    lim += lim * 0.01
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    data.set_index('level', inplace=True)
    for _, cir in data.loc[[0]].iterrows():
            ax.add_patch(plt.Circle((cir['x'], cir['y']), cir['r'],
                                    alpha=0, linewidth=2, color='White'))
    for _, cir in data.loc[[1]].iterrows():
            ax.add_patch(plt.Circle((cir['x'], cir['y']), cir['r'],
                                    alpha=0.5, linewidth=2,
                                    color=cir['color']))
    for _, cir in data.loc[[2]].iterrows():
            ax.add_patch(plt.Circle((cir['x'], cir['y']), cir['r'],
                                    alpha=0.8, linewidth=2,
                                    color=cir['color']))
    ax.get_xaxis().set_ticks([])

    print(lim)
    # this code removes the y axes but the next set adds log labels
    # log label don't work because stacking dose not work like that
    # when exponents are involved.
    ax.get_yaxis().set_ticks([])
    # y_tix = np.array(range(1, round(np.exp(lim)), 10000))
    # ax.get_yaxis().set_ticks(np.log(y_tix))
    # ax.set_yticklabels(y_tix - 1)
    #ax.plot((-lim, -lim), (-lim, lim), color='white', linewidth=1)

    # ax.get_yaxis().set_ticks([])
    ax.set_frame_on(False)
    if not check_values:
        for _, cir in data[data['show_name'].apply(lambda x: x[mon])].iterrows():
            ax.text(cir['x'], cir['label_y'][mon], cir['name'])
    else:
        for _, cir in data.loc[[2]].iterrows():
            ax.text(cir['x'], cir['y'], "%0.2f" %(np.exp(cir['r']) - 1))
    return ax

###########################
# Label dodge figure code #
###########################

def move_label(arg, olds, pnt=0, spacer = 0.1, move_up=True):
    min_gap = 1
    if len(olds) <= pnt:
        return arg
    if abs(olds[pnt] - arg) < min_gap:
        if move_up:
            arg += spacer
            return move_label(arg, olds, 0, spacer + 0.1, not move_up)
        else:
            arg -= spacer
            return move_label(arg, olds, 0, spacer + 0.1, not move_up)
    else:
        return move_label(arg, olds, pnt + 1, spacer, move_up)

def dodge_labes(labels):
    out=[]
    for i in labels:
        out.append(move_label(i, out))
    return out

def uncollide_labes_one_ax(in_data:pd.DataFrame, dep, mon):
    data = in_data[in_data['depth'] == dep].copy()
    data = data[data['show_name'].apply(lambda x: x[mon])]
    data['y'] = data['circCor'].apply(lambda x: x[mon][1])
    data['r'] = data['circCor'].apply(lambda x: x[mon][2])
    data.sort_values('r', inplace=True)
    data['yn'] = dodge_labes(data['y'].values)
    return {i[0]:i[1] for i in data[['name', 'yn']].values }

def uncollide_labes(circle_data:pd.DataFrame):
    circle_data['label_y'] = [{} for i in range(len(circle_data))]
    for i, mon in enumerate([7, 8, 9]):
        for j, dep in enumerate(['1', '3', '5/6']):
            new_loca = uncollide_labes_one_ax(circle_data, dep, mon)
            for k in new_loca:
                loca = circle_data.loc[
                    (circle_data['depth'] == dep) &
                    (circle_data['name'] == k),
                    'label_y'].values[0]
                loca[mon] = new_loca[k]
                circle_data.loc[(circle_data['depth'] == dep) &
                                (circle_data['name'] == k),
                                'label_y'] = [loca]
    return circle_data

#############
# main code #
#############

def make_static_fig(check_values=False) -> None:
    """Make a MatPlotLib form of the figure"""
    custom_color =pd.read_csv(StringIO(
        "           metab,    color\n"
        "0,         aceto,  #4daf4a\n" # green
        "1,        alkane,  #ff7f00\n" # orange
        "2,         hydro,  #377eb8\n" # hydro=blue
        "3,  methanotroph,  #e41a1c\n" #red
        "4,        methyl,  #984ea3\n" #purple
        "5,         troph,  #ffff33\n"), skipinitialspace=True)
    custom_color['color'] = custom_color['color'].\
        apply(lambda x:tuple(int(x.lstrip('#')[i:i+2], 16) / 255
                             for i in (0, 2, 4)))
    data = read_reshape_data([
        './data/all_mgens_mean_geTMM_w_metab_Rory_7April2021.tsv',
        './data/geTMM_ALLMUDS_14Feb2021_MEAN_BIN_counts_ge20_genes_transcribed_'
        'METHANOTROPHS (1).txt'
    ], custom_color)
    data['measure'] = np.log(data['measure'] + 1)
    # move one circle
    circle_loc = CircleLoca(data)
    temp = circle_loc.loc[3]['methanotroph']
    circle_loc.move_metab(3, 'methanotroph', circle_loc.loc[3]['aceto'])
    circle_loc.move_metab(3, 'aceto', temp)
    all_circles = circle_loc.set_circles()
    circle_data = get_circle_data(all_circles, data)
    circle_data = uncollide_labes(circle_data)

    plt.style.use('dark_background')
    fig, axs = make_fig(circle_data, check_values=check_values)
    fig.savefig('log_circles.svg')
    fig.show()

def make_dynamic_fig() -> None:
    """Output the data too type script for dynamic figure"""
    custom_color =pd.read_csv(StringIO(
        "           metab,    color\n"
        "0,         aceto,  #4daf4a\n" # green
        "1,        alkane,  #ff7f00\n" # orange
        "2,         hydro,  #377eb8\n" # hydro=blue
        "3,  methanotroph,  #e41a1c\n" #red
        "4,        methyl,  #984ea3\n" #purple
        "5,         troph,  #ffff33\n"), skipinitialspace=True)
    custom_color['color'] = custom_color['color'].\
        apply(lambda x:tuple(int(x.lstrip('#')[i:i+2], 16) / 255
                             for i in (0, 2, 4)))
    data = read_reshape_data([
        './data/all_mgens_mean_geTMM_w_metab_Rory_7April2021.tsv',
        './data/geTMM_ALLMUDS_14Feb2021_MEAN_BIN_counts_ge20_genes_'
        'transcribed_METHANOTROPHS (1).txt'
    ], custom_color)
    data['measure'] = np.log(data['measure'] + 1)
    # move one circle
    circle_loc = CircleLoca(data)
    x = circle_loc.loc[3]['methanotroph']
    circle_loc.move_metab(3, 'methanotroph', circle_loc.loc[3]['aceto'])
    circle_loc.move_metab(3, 'aceto', x)
    all_circles = circle_loc.set_circles()
    circle_data = get_circle_data(all_circles, data)
    circle_data = uncollide_labes(circle_data)

    with open('./interactive_visual/sketch/data.ts', 'w') as f:
        write_to_typescript(circle_data, f)

def test_a_line(mon, dep):
    data = read_reshape_data([
        './data/all_mgens_mean_geTMM_w_metab_Rory_7April2021.tsv',
        './data/geTMM_ALLMUDS_14Feb2021_MEAN_BIN_counts_ge20_genes_'
        'transcribed_METHANOTROPHS (1).txt'
    ])
    return data[
        (data['Month_num'] == mon) &
        (data['Depth'] == dep)
    ].sort_values('measure').tail(3)
    # "           metab,    color\n"
    # "0,         aceto,  #4daf4a\n" # green
    # "1,        alkane,  #ff7f00\n" # orange
    # "2,         hydro,  #377eb8\n" # hydro=blue
    # "3,  methanotroph,  #e41a1c\n" #red
    # "4,        methyl,  #984ea3\n" #purple
    # "5,         troph,  #ffff33\n"

test_a_line(7, '1')

def make_test_fig() -> None:
    """Make a MatPlotLib form of the figure"""
    data = read_reshape_data([
        './data/test.tsv',
    ])
    data['measure'] = np.log(data['measure'] + 1)

    circle_loc = CircleLoca(data)
    all_circles = circle_loc.set_circles()
    circle_data = get_circle_data(all_circles, data)
    circle_data = uncollide_labes(circle_data)

    plt.style.use('dark_background')
    fig, axs = make_fig(circle_data)
    fig.savefig('log_circles.svg')
    fig.show()

make_test_fig()
data
if __name__ ==  '__main__':
make_static_fig()
    make_dynamic_fig()

