import zipfile,re,unicodedata,json
from pathlib import Path
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer,CountVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize
from scipy.stats import chi2_contingency
ROOT=Path('/mnt/data/eda_fakebr'); Z='/mnt/data/size_normalized_texts.zip'
rows=[]
with zipfile.ZipFile(Z) as z:
 for n in z.namelist():
  if not n.endswith('.txt'):continue
  label=n.split('/')[1]
  if label not in ('fake','true'):continue
  b=z.read(n)
  try:t=b.decode('utf-8-sig')
  except UnicodeDecodeError:t=b.decode('latin1')
  rows.append(dict(id=Path(n).stem,classe=label,texto=t,caracteres=len(t),palavras=len(re.findall(r'\b\w+\b',t,flags=re.UNICODE))))
df=pd.DataFrame(rows).sort_values(['classe','id']).reset_index(drop=True)
counts=df.classe.value_counts(); print('counts',counts.to_dict()); print('empty',sum(df.palavras==0));print('duplicates',df.texto.duplicated().sum())
summary=df.groupby('classe')[['palavras','caracteres']].agg(['count','mean','median','std','min','max']).round(2);summary.to_csv(ROOT/'estatisticas_comprimento.csv')
df[['id','classe','palavras','caracteres']].to_csv(ROOT/'metadados_textos.csv',index=False)
plt.rcParams.update({'font.size':11,'figure.dpi':130,'savefig.dpi':170})
fig,ax=plt.subplots(figsize=(7,4)); colors=['#D97757','#278C87']; vals=[counts['fake'],counts['true']];bars=ax.bar(['Falsas','Verdadeiras'],vals,color=colors)
for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+15,f'{v} ({v/len(df):.2%})',ha='center')
ax.set_ylim(0,max(vals)*1.16);ax.set_ylabel('Quantidade de notícias');ax.set_title('Distribuição das classes');fig.tight_layout();fig.savefig(ROOT/'01_distribuicao_classes.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,4.5))
for ax,col,title in zip(axs,['palavras','caracteres'],['Número de palavras','Número de caracteres']):
 data=[df.loc[df.classe==c,col].values for c in ['fake','true']]
 ax.boxplot(data,tick_labels=['Falsas','Verdadeiras'],showfliers=False,patch_artist=True,boxprops={'facecolor':'#cbd5e1'})
 ax.set_title(title);ax.set_ylabel('Contagem')
fig.suptitle('Distribuição dos comprimentos por classe (sem exibir outliers)');fig.tight_layout();fig.savefig(ROOT/'02_comprimento_boxplots.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,4))
for ax,col in zip(axs,['palavras','caracteres']):
 for c,color in zip(['fake','true'],colors):ax.hist(df.loc[df.classe==c,col],bins=35,alpha=.5,density=True,label='Falsas' if c=='fake' else 'Verdadeiras',color=color)
 ax.set_xlabel(col.capitalize());ax.set_ylabel('Densidade');ax.legend()
fig.tight_layout();fig.savefig(ROOT/'03_distribuicao_comprimentos.png');plt.close(fig)
stop='a o as os de da do das dos em no na nos nas um uma uns umas e é que por para com sem sobre ao aos à às se sua seu suas seus foi são ser como mais mas já também não este esta estes estas isso isto aquele aquela eles elas ele ela há ter tem têm entre após até muito ainda ou onde quando porque pelo pela pelos pelas desde durante contra sob cada qual quais quem lhe lhes eu tu nós vocês você me te nos vos minha meu minhas meus todo toda todos todas outro outra outros outras mesmo mesma mesmos mesmas esse essa esses essas num numa nuns numas está estão era eram foram sendo sido pode podem poderia deve devem haver havia houve dia dias ano anos segundo disse diz afirma afirmou notícia noticias notícias texto site reportagem jornal portal publicado publicada publicação informou informações informação'.split()
stop=[''.join(ch for ch in unicodedata.normalize('NFKD',w) if not unicodedata.combining(ch)) for w in stop]
vectorizer=CountVectorizer(strip_accents='unicode',lowercase=True,token_pattern=r'(?u)\b[^\W\d_][\w-]{2,}\b',stop_words=stop,ngram_range=(1,2),min_df=5,max_df=.85,binary=True)
X=vectorizer.fit_transform(df.texto);vocab=np.array(vectorizer.get_feature_names_out());idxf=(df.classe=='fake').values; idxt=~idxf
# smoothed document prevalence log odds; avoid rare artifacts with min_df
nf=np.asarray(X[idxf].sum(axis=0)).ravel();nt=np.asarray(X[idxt].sum(axis=0)).ravel();pf=(nf+1)/(idxf.sum()+2);pt=(nt+1)/(idxt.sum()+2);logodds=np.log(pf/(1-pf))-np.log(pt/(1-pt))
terms=pd.DataFrame({'termo':vocab,'documentos_falsas':nf,'documentos_verdadeiras':nt,'prevalencia_falsas':pf,'prevalencia_verdadeiras':pt,'log_odds_falsas_vs_verdadeiras':logodds})
terms.sort_values('log_odds_falsas_vs_verdadeiras',ascending=False).to_csv(ROOT/'termos_discriminantes.csv',index=False)
# separate frequent vocabulary unigram counts (token counts)
cv=CountVectorizer(strip_accents='unicode',lowercase=True,token_pattern=r'(?u)\b[^\W\d_][\w-]{2,}\b',stop_words=stop,min_df=3,max_df=.9)
C=cv.fit_transform(df.texto);v=np.array(cv.get_feature_names_out());f=np.asarray(C[idxf].sum(axis=0)).ravel();t=np.asarray(C[idxt].sum(axis=0)).ravel();freq=pd.DataFrame({'termo':v,'falsas':f,'verdadeiras':t,'total':f+t}).sort_values('total',ascending=False);freq.to_csv(ROOT/'vocabulario_frequente.csv',index=False)
fig,axs=plt.subplots(1,2,figsize=(14,5))
for ax,c,arr in zip(axs,['Falsas','Verdadeiras'],[f,t]):
 ix=np.argsort(arr)[-15:];ax.barh(v[ix],arr[ix],color=colors[0] if c=='Falsas' else colors[1]);ax.set_title('Palavras mais frequentes — '+c);ax.set_xlabel('Ocorrências')
fig.tight_layout();fig.savefig(ROOT/'04_vocabulario_frequente.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(14,5))
for ax,side,mask,col in [(axs[0],'Falsas',logodds>0,colors[0]),(axs[1],'Verdadeiras',logodds<0,colors[1])]:
 subset=terms.loc[mask & ((terms.documentos_falsas+terms.documentos_verdadeiras)>=12)].copy()
 subset['score']=subset.log_odds_falsas_vs_verdadeiras.abs();subset=subset.nlargest(15,'score').iloc[::-1]
 ax.barh(subset.termo,subset.score,color=col);ax.set_title('Termos associados a '+side);ax.set_xlabel('|log-odds| (presença por documento)')
fig.tight_layout();fig.savefig(ROOT/'05_termos_discriminantes.png');plt.close(fig)
# unsupervised thematic clusters. Fit jointly and cross-tab class, not balancing.
tfidf=TfidfVectorizer(strip_accents='unicode',lowercase=True,stop_words=stop,ngram_range=(1,2),min_df=4,max_df=.85,max_features=18000,sublinear_tf=True)
T=tfidf.fit_transform(df.texto);svd=TruncatedSVD(n_components=40,random_state=42);emb=normalize(svd.fit_transform(T));print('SVD variance',svd.explained_variance_ratio_.sum())
# fixed k exploratory not claim optimized or match training script
km=MiniBatchKMeans(n_clusters=8,random_state=42,n_init=10,batch_size=256,max_iter=150);cl=km.fit_predict(emb);df['cluster_exploratorio']=cl
ct=pd.crosstab(df.cluster_exploratorio,df.classe).reindex(columns=['fake','true'],fill_value=0);ct.to_csv(ROOT/'clusters_por_classe.csv')
fig,ax=plt.subplots(figsize=(9,5));ct.rename(columns={'fake':'Falsas','true':'Verdadeiras'}).plot(kind='bar',stacked=True,color=colors,ax=ax);ax.set_title('Composição das classes por cluster temático exploratório (K=8)');ax.set_xlabel('Cluster');ax.set_ylabel('Número de textos');ax.legend();fig.tight_layout();fig.savefig(ROOT/'06_clusters_classes_absoluto.png');plt.close(fig)
fig,ax=plt.subplots(figsize=(9,5));(ct.div(ct.sum(axis=1),axis=0)*100).rename(columns={'fake':'Falsas','true':'Verdadeiras'}).plot(kind='bar',stacked=True,color=colors,ax=ax);ax.set_title('Composição percentual de classes por cluster (K=8)');ax.set_xlabel('Cluster');ax.set_ylabel('% dentro do cluster');ax.legend();fig.tight_layout();fig.savefig(ROOT/'07_clusters_classes_percentual.png');plt.close(fig)
chi,p,dof,expected=chi2_contingency(ct);n=ct.values.sum();cramer=np.sqrt(chi/(n*min(ct.shape[0]-1,ct.shape[1]-1)))
# top descriptive terms per cluster by TF-IDF mean (not causal labels)
words=np.array(tfidf.get_feature_names_out());records=[]
for k in range(8):
 mean=np.asarray(T[cl==k].mean(axis=0)).ravel();top=words[np.argsort(mean)[-12:][::-1]];records.append({'cluster':k,'n':int((cl==k).sum()),'falsas':int(ct.loc[k,'fake']),'verdadeiras':int(ct.loc[k,'true']),'termos_top':', '.join(top)})
pd.DataFrame(records).to_csv(ROOT/'interpretacao_clusters.csv',index=False)
# 2d SVD projection for illustration only
fig,ax=plt.subplots(figsize=(8,6));ax.scatter(emb[idxt,0],emb[idxt,1],s=9,alpha=.45,label='Verdadeiras',color=colors[1]);ax.scatter(emb[idxf,0],emb[idxf,1],s=9,alpha=.45,label='Falsas',color=colors[0]);ax.set_xlabel('Componente latente 1');ax.set_ylabel('Componente latente 2');ax.set_title('Projeção 2D dos textos (SVD de TF-IDF; apenas ilustrativa)');ax.legend();fig.tight_layout();fig.savefig(ROOT/'08_projecao_textos.png');plt.close(fig)
df[['id','classe','palavras','caracteres','cluster_exploratorio']].to_csv(ROOT/'metadados_com_clusters.csv',index=False)
result={'n':len(df),'classes':counts.to_dict(),'duplicatas_exatas':int(df.texto.duplicated().sum()),'vazios':int((df.palavras==0).sum()),'chi2':float(chi),'p':float(p),'cramers_v':float(cramer),'svd_variancia':float(svd.explained_variance_ratio_.sum()),'stats':{c:{col:{stat:float(df.loc[df.classe==c,col].agg(stat)) for stat in ['mean','median','std','min','max']} for col in ['palavras','caracteres']} for c in ['fake','true']}}
(ROOT/'resultados.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2));print('clusters\n',ct.to_string());print('terms\n',pd.DataFrame(records).to_string(index=False))
