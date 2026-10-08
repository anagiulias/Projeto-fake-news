import zipfile,csv
from pathlib import Path
z=zipfile.ZipFile('/mnt/data/size_normalized_texts.zip')
out=Path('/mnt/data/noticias_rotuladas_tratadas_eda.csv')
counts={0:0,1:0}
with out.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['texto_modelo','label','arquivo_origem'])
 for name in sorted(z.namelist()):
  if not name.endswith('.txt'):continue
  label=1 if '/fake/' in name else 0 if '/true/' in name else None
  if label is None:continue
  raw=z.read(name)
  try:t=raw.decode('utf-8-sig')
  except UnicodeDecodeError:t=raw.decode('latin-1')
  t=t.strip()
  if t:w.writerow([t,label,name]);counts[label]+=1
print('CSV',out,'counts',counts)
