"""Auditoria reproduzível do balanceamento temático REAL de treinar_classificador.py.
Executar: python 05_auditoria_kmeans_treino.py --dataset noticias_rotuladas_tratadas.csv --treino-script treinar_classificador.py --saida Tratamento-dados
O arquivo CSV precisa ter texto_modelo, label, arquivo_origem.
"""
import argparse, importlib.util, json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

p=argparse.ArgumentParser()
p.add_argument('--dataset',required=True)
p.add_argument('--treino-script',required=True)
p.add_argument('--saida',default='Tratamento-dados')
a=p.parse_args()
saida=Path(a.saida); (saida/'imagens').mkdir(parents=True,exist_ok=True); (saida/'relatorios').mkdir(parents=True,exist_ok=True)
script=Path(a.treino_script).resolve()
import sys
sys.path.insert(0,str(script.parent))
spec=importlib.util.spec_from_file_location('treino_eda',script)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
# Usa as rotinas de validação e split originais, sem reescrevê-las.
m.CAMINHO_DATASET=Path(a.dataset).resolve()
# Redireciona os CSVs gerados para a pasta de relatórios.
m.CAMINHO_DATASET_BALANCEADO=saida/'relatorios'/'noticias_rotuladas_balanceadas_auditoria.csv'
m.CAMINHO_FALSAS_NAO_AMOSTRADAS=saida/'relatorios'/'falsas_nao_amostradas_auditoria.csv'
dados=m.carregar_dataset()
grupos=m.construir_grupos_sem_vazamento(dados)
treino_original,teste,_,_=m.dividir_treino_teste(dados,grupos)
balanceado,restantes,_=m.criar_dataset_balanceado(treino_original)
# Reconstitui as contagens anteriores pela concatenação da seleção com as falsas restantes.
antes=pd.concat([balanceado,restantes],ignore_index=True)
assert len(antes)==len(treino_original)
assert len(teste)+len(treino_original)==len(dados)
assert len(balanceado.loc[balanceado.label==0])==len(balanceado.loc[balanceado.label==1])

def tabela(df):
    return pd.crosstab(df['tema_cluster'],df['label']).reindex(index=range(int(antes.tema_cluster.max())+1),columns=[0,1],fill_value=0)
a0=tabela(antes); a1=tabela(balanceado)
comparacao=pd.DataFrame({'verdadeiras_antes':a0[0], 'falsas_antes':a0[1], 'verdadeiras_depois':a1[0], 'falsas_depois':a1[1]})
comparacao['fracao_falsa_antes']=a0[1]/a0.sum(axis=1).replace(0,np.nan)
comparacao['fracao_falsa_depois']=a1[1]/a1.sum(axis=1).replace(0,np.nan)
comparacao.to_csv(saida/'relatorios'/'comparacao_clusters_antes_depois.csv',encoding='utf-8-sig',index_label='cluster')

fig,axes=plt.subplots(2,1,figsize=(13,9),sharex=True,layout='constrained')
for ax,t,titulo in [(axes[0],a0,'Treino original — antes do balanceamento'),(axes[1],a1,'Treino selecionado — após cotas por cluster')]:
    x=np.arange(len(t)); ax.bar(x,t[0],label='Verdadeiras'); ax.bar(x,t[1],bottom=t[0],label='Falsas')
    ax.set_ylabel('Número de textos'); ax.set_title(titulo); ax.legend()
axes[1].set_xticks(np.arange(len(a0))); axes[1].set_xticklabels(a0.index,rotation=90)
axes[1].set_xlabel('Cluster temático (identificador automático)')
fig.savefig(saida/'imagens'/'kmeans_antes_depois_contagens.png',dpi=180);plt.close(fig)
fig,axes=plt.subplots(2,1,figsize=(13,8),sharex=True,layout='constrained')
for ax,t,titulo in [(axes[0],a0,'Antes'),(axes[1],a1,'Depois')]:
    pct=t.div(t.sum(axis=1).replace(0,np.nan),axis=0)*100
    x=np.arange(len(t)); ax.bar(x,pct[0],label='Verdadeiras'); ax.bar(x,pct[1],bottom=pct[0],label='Falsas')
    ax.set_ylim(0,100);ax.set_ylabel('% dentro do cluster');ax.set_title(titulo);ax.legend()
axes[1].set_xticks(np.arange(len(a0)));axes[1].set_xticklabels(a0.index,rotation=90)
axes[1].set_xlabel('Cluster temático')
fig.savefig(saida/'imagens'/'kmeans_antes_depois_percentuais.png',dpi=180);plt.close(fig)
resumo={'dataset_total':len(dados),'treino_antes':len(treino_original),'treino_depois':len(balanceado),'teste_intocado':len(teste),'falsas_nao_amostradas_treino':len(restantes),'clusters':int(antes.tema_cluster.nunique()),'observacao':'Amostragem uniforme somente da classe falsa; as verdadeiras são preservadas. Clusters ajustados apenas no treino.'}
(saida/'relatorios'/'auditoria_kmeans.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(resumo,ensure_ascii=False,indent=2))
