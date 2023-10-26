import pandas as pd
import re
import requests
import matplotlib.pyplot as plt
import numpy as np
import locale
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def get_html(url: str):
    r = requests.get(url)

    if r.status_code == 200:
        html = r.content
        return html
    
def get_president_timeline():
    url = 'https://pt.wikipedia.org/wiki/Lista_de_presidentes_do_Brasil#Linha_do_tempo'
    html = get_html(url)

    df = pd.read_html(html)[0]
    df.columns = ['numero','nome','foto','periodo','partido','vice','referencias','eleicao']
    df = df[['numero','nome','periodo']]
    filtered_rows = [idx for idx,row in enumerate(df['numero']) if re.fullmatch(r"^\d+$", row)]
    df = df.iloc[filtered_rows,:].reset_index(drop=True)

    df['periodo'] = df['periodo'].str.split("(").str[0]
    df['periodo'] = df['periodo'].str.replace('de ','',regex=False).str.replace('º','',regex=False).str.replace('°','',regex=False)
    df['inicio'] = df['periodo'].str.split(' – ').str[0]
    df['fim'] = df['periodo'].str.split(' – ').str[1]
    df.loc[len(df)-1,'fim'] = pd.to_datetime("today").strftime('%d %B %Y')
    df['inicio'] = pd.to_datetime(df['inicio'], format = '%d %B %Y')
    df['fim'] = df['fim'].str.strip()
    df['fim'] = pd.to_datetime(df['fim'], format = '%d %B %Y')

    df = df[['numero','nome','inicio','fim']]
    df = df.drop_duplicates().reset_index(drop=True)

    df = df.sort_values(by=['numero', 'inicio'])

    df = df.groupby(['numero', 'nome']).agg({
        'inicio': 'min',
        'fim': 'max'
    })

    df = df.sort_values('inicio').reset_index()

    reelections = df['nome'].value_counts()
    reelection_idx = reelections[reelections > 1].index

    reelections_df = df[df['nome'].isin(reelection_idx)]
    reelected_presidents = list(reelections_df['nome'].unique())

    name_to_y_value = {name: i for i, name in enumerate(df['nome'].unique())}

    colors = plt.cm.jet(np.linspace(0, 1, len(name_to_y_value)))
    name_to_color = {name: colors[i] for i, name in enumerate(name_to_y_value)}

    fig, ax = plt.subplots(figsize=(15, 7))

    xlabels = []
    labeled_presidents = set()  

    for index, row in df.iterrows():
        y_value = name_to_y_value[row["nome"]]
        x_label_value = row['fim'] + pd.Timedelta(300, unit = 'D')
        xlabels.append(x_label_value)
        ax.plot([row["inicio"], row["fim"]], [y_value, y_value], color=name_to_color[row["nome"]], marker="o", label=row["nome"])
        if row["nome"] not in labeled_presidents:
            if row['nome'] in reelected_presidents:
                labeled_presidents.add(row["nome"])
            else:
                ax.text(x_label_value, y_value, row["nome"], color='black', va='center', ha='left', fontsize=7)
        else:
            ax.text(x_label_value, y_value, row["nome"], color='black', va='center', ha='left', fontsize=7)

    ax.yaxis.set_visible(False)

    ax.set_xlabel('')
    ax.set_title("Linha do Tempo dos Presidentes")
    ax.grid(True, which="both", axis="x", linestyle="--")

    ax.set_xlim(min(xlabels) - pd.Timedelta(2000, unit = 'D') , max(xlabels) + pd.Timedelta(5000, unit = 'D'))

    handles, labels = ax.get_legend_handles_labels()
    ax.legend('')
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.tight_layout()
    plt.show()
    return fig

def get_chancellor_timeline():
    url = 'https://pt.wikipedia.org/wiki/Lista_de_ministros_das_Rela%C3%A7%C3%B5es_Exteriores_do_Brasil'
    html = get_html(url)

    dfs = pd.read_html(html)
    df = pd.DataFrame()
    for sub_df in dfs:
        if len(sub_df.columns) == 6:
            sub_df.columns = ['numero','foto','nome','inicio','fim','chefe de governo']
            df = pd.concat([df, sub_df])

    df = df[['numero','nome','inicio','fim','chefe de governo']]

    filtered_rows = [idx for idx,row in enumerate(df['numero']) if row != '—']
    df = df.iloc[filtered_rows,:].reset_index(drop=True)

    for col in ['inicio','fim']:
        df[col] = df[col].str.replace('de ','',regex=False).str.replace('º','',regex=False).str.replace('°','',regex=False)

    df = df.dropna().reset_index(drop=True)

    df.loc[len(df)-1,'fim'] = pd.to_datetime("today").strftime('%d %B %Y')
    df['inicio'] = pd.to_datetime(df['inicio'], format = '%d %B %Y')
    df['fim'] = df['fim'].str.strip()
    df['fim'] = pd.to_datetime(df['fim'], format = '%d %B %Y')

    mask = df['nome'].str.contains('[',regex=False)
    df.loc[mask,'nome'] = df.loc[mask,'nome'].str.split('[').str[0]

    df = df.drop_duplicates().reset_index(drop=True)

    df = df.sort_values(by=['numero', 'inicio'])

    df = df.groupby(['numero', 'nome']).agg({
        'inicio': 'min',
        'fim': 'max'
    })

    df = df.sort_values('inicio').reset_index()

    reelections = df['nome'].value_counts()
    presidents = dict(zip(reelections.index, reelections.values))
    presidents_status = dict(zip(reelections.index, [0]*len(reelections)))

    name_to_y_value = {name: i for i, name in enumerate(df['nome'].unique())}

    colors = plt.cm.jet(np.linspace(0, 1, len(name_to_y_value)))
    name_to_color = {name: colors[i] for i, name in enumerate(name_to_y_value)}

    fig, ax = plt.subplots(figsize=(15, 7))

    xlabels = []

    for index, row in df.iterrows():
        y_value = name_to_y_value[row["nome"]]
        x_label_value = row['fim'] + pd.Timedelta(300, unit = 'D')
        xlabels.append(x_label_value)
        ax.plot([row["inicio"], row["fim"]], [y_value, y_value], color=name_to_color[row["nome"]], marker="o", markersize=2, label=row["nome"])

        presidents_status[row['nome']] += 1
        if presidents_status[row['nome']] == presidents[row['nome']]:
            ax.text(x_label_value, y_value, row["nome"], color='black', va='center', ha='left', fontsize=4)

    ax.yaxis.set_visible(False)

    ax.set_xlabel('')
    ax.set_title("Linha do Tempo dos Chanceleres")
    ax.grid(True, which="both", axis="x", linestyle="--")

    ax.set_xlim(min(xlabels) - pd.Timedelta(2000, unit = 'D') , max(xlabels) + pd.Timedelta(5000, unit = 'D'))

    handles, labels = ax.get_legend_handles_labels()
    ax.legend('')
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.tight_layout()
    plt.show()
    return fig
