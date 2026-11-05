from pathlib import Path
import json,html,shutil,zipfile,hashlib
import render_approved
R=Path(__file__).resolve().parents[1];E=html.escape
BASE='https://raw.githubusercontent.com/OlgaKraven/2026-2027-09.02.07-rvmp-pp-pm.05-sem07/main/site/downloads/'
STYLE='''@font-face{font-family:Golos;src:url(assets/fonts/GolosText-Regular.ttf)}@font-face{font-family:Golos;src:url(assets/fonts/GolosText-Bold.ttf);font-weight:700}*{box-sizing:border-box}body{margin:0;background:#e9e9ec;color:#1c1c1c;font:15px/1.65 Golos,Arial,sans-serif}nav{max-width:736px;margin:16px auto;background:#fff;padding:12px 22px}nav a{margin-right:16px;color:#a50b12}article{max-width:736px;margin:18px auto;background:#fff}header{padding:34px 38px 28px;background:#1c1c1c;color:white;border-bottom:6px solid #ed131c}header h1{font-size:35px;line-height:1.15;letter-spacing:-1px;margin:22px 0 0}header small{font-size:12px}.content{padding:24px 30px 28px}.step{display:grid;grid-template-columns:38px 1fr;gap:11px;margin:0 0 17px}.num{height:32px;min-width:38px;border:1.5px solid #ed131c;border-radius:18px;text-align:center;font-size:12px;line-height:29px;background:white}.block{padding:20px 21px;border-radius:14px;background:#f4f4f6}.block h2{font-size:18px;line-height:1.35;margin:0 0 12px}.block p{margin:0 0 10px;overflow-wrap:anywhere}pre{font:12px/1.65 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:15px;border:1px solid #dfe1e5;border-radius:7px}img{display:block;max-width:100%;height:auto}figcaption{font-size:13px;line-height:1.6}a{color:#a50b12}@media(max-width:570px){header{padding:29px 22px 24px}header h1{font-size:30px}.content{padding:23px 16px 24px}.step{grid-template-columns:27px 1fr;gap:8px}.num{min-width:27px;font-size:11px}.block{padding:17px 15px}}'''
def web(specs,name,title):
    s=['<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+E(title)+'</title><style>'+STYLE+'</style><nav><a href="index.html">Материалы</a><a href="lessons.html">Методика</a><a href="areas.html">Варианты</a></nav>']
    for page in specs:
        s.append('<article><header><small>ПП ПМ.05 · Серверная часть сервиса заявок</small><h1>'+E(page['title'])+'</h1></header><div class="content">')
        for i,b in enumerate(page['blocks'],1):
            s.append('<div class="step"><span class="num">'+str(i)+'</span><section class="block"><h2>'+E(b['title'])+'</h2>')
            if b['kind']=='code':s.append('<pre>'+E(b['text'])+'</pre>')
            elif b['kind']=='image':
                if b.get('clip'):
                    from PIL import Image as PILImage
                    iw,ih=PILImage.open(R/b['path']).size;c=b['clip']
                    region=f"position:relative;overflow:hidden;aspect-ratio:{c['w']}/{c['h']}"
                    pos=f"position:absolute;max-width:none;width:{iw/c['w']*100}%;left:{-c['x']/c['w']*100}%;top:{-c['y']/c['h']*100}%"
                    s.append('<figure><a href="'+E(b['path'])+'"><div style="'+region+'"><img style="'+pos+'" src="'+E(b['path'])+'" alt="'+E(b['text'])+'"></div></a><figcaption>'+E(b['text'])+'</figcaption></figure>')
                else:s.append('<figure><img src="'+E(b['path'])+'" alt="'+E(b['text'])+'"><figcaption>'+E(b['text'])+'</figcaption></figure>')
            elif b['kind']=='link':s.append('<a href="'+E(b['url'])+'">'+E(b['text'])+'</a>')
            else:s.extend('<p>'+E(p)+'</p>' for p in b['text'].split('\n\n'))
            s.append('</section></div>')
        s.append('</div></article>')
    (R/'site'/name).write_text(''.join(s)+'</html>',encoding='utf-8')
def build():
    d=json.loads((R/'content/materials.json').read_text(encoding='utf-8'))
    render_approved.pdf(R,R/'site/downloads/assignment.pdf',d,'assignment')
    render_approved.pdf(R,R/'site/downloads/guide.pdf',d,'guide')
    for branch,pages in d['branches'].items():
        render_approved.pdf(R,R/f'site/downloads/{branch}.pdf',{'assignment':[],'guide':pages},'assignment')
        web(pages,branch+'.html','Инструкция '+branch.upper())
    (R/'site/assets/fonts').mkdir(parents=True,exist_ok=True)
    shutil.copytree(R/'assets/fonts',R/'site/assets/fonts',dirs_exist_ok=True)
    for f in (R/'evidence/windows').glob('*.png'):
        target=R/'site/evidence/windows'/f.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
    web(d['assignment']+d['guide'],'lessons.html','Задание и методические рекомендации')
    web(d['areas'],'areas.html','Список предметных областей')
    links=[('Задание и методические рекомендации','assignment.pdf'),('Список предметных областей','guide.pdf'),('Выбранная ветка Flask: инструкция','flask.pdf'),('Выбранная ветка Flask: исходники образца','flask.zip'),('Выбранная ветка PHP: инструкция','php.pdf'),('Выбранная ветка PHP: исходники образца','php.zip'),('Тестовый проект серверных проверок','tests.zip'),('Отчет о выполнении.docx','Отчет%20о%20выполнении.docx')]
    web([{'title':'Серверная часть сервиса заявок','blocks':[{'kind':'link','title':label,'text':label,'url':BASE+file} for label,file in links]}],'index.html','Серверная часть сервиса заявок')
    (R/'README.md').write_text('# Производственная практика ПМ.05\n\nСерверная часть сервиса заявок · РВМП · 7 семестр\n\n[Открыть материалы](https://olgakraven.github.io/2026-2027-09.02.07-rvmp-pp-pm.05-sem07/).\n\n'+'\n'.join('- ['+label+']('+BASE+file+')' for label,file in links)+'\n',encoding='utf-8')
    docs=R/'docs';docs.mkdir(exist_ok=True)
    for name,title,specs in [('assignment','Задание и методические рекомендации',d['assignment']+d['guide']),('subject_areas','Список предметных областей',d['areas'])]:
        s=['# '+title]
        for page in specs:
            s+=['','## '+page['title']]
            for b in page['blocks']:
                s+=['','### '+b['title']]
                if b['kind']=='image':s+=['!['+b['text']+'](../'+b['path']+')']
                elif b['kind']=='link':s+=['['+b['text']+']('+b['url']+')']
                elif b['kind']=='code':s+=['```',b['text'],'```']
                else:s+=[b['text']]
        (docs/(name+'.md')).write_text('\n'.join(s)+'\n',encoding='utf-8')
    (R/'content/original-areas.json').write_text(json.dumps(d.pop('original_areas'),ensure_ascii=False,indent=2),encoding='utf-8')
    (R/'content/course.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(R/'site/downloads/tests.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in (R/'test-project').glob('*'):
            if f.is_file() and f.name!='results.json':z.write(f,'tests/'+f.name)
    # Keep older direct file links consistent with the current source.
    for f in (R/'demo').rglob('*'):
        if f.is_file() and '__pycache__' not in str(f):
            rel=str(f.relative_to(R/'demo')).replace('\\','/')
            name=rel.replace('/','-') if '/' in rel else rel
            if name!='README.md':shutil.copyfile(f,R/'site/downloads'/name)
    with zipfile.ZipFile(R/'site/downloads/Service-center-demo.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in (R/'demo').rglob('*'):
            if f.is_file() and '__pycache__' not in str(f):z.write(f,'demo/'+str(f.relative_to(R/'demo')).replace('\\','/'))
    (R/'site/downloads/report-template.md').write_text('# Отчёт о выполнении\n\nИспользовать чистую форму [Отчет о выполнении.docx]('+BASE+'Отчет%20о%20выполнении.docx).\n',encoding='utf-8')
    files={str(p.relative_to(R/'site')).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'site').rglob('*')) if p.is_file() and p.name!='manifest.json'}
    (R/'site/manifest.json').write_text(json.dumps({'schema_version':1,'files':files},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Four PDFs, separate instructions, current site and source pages built')
if __name__=='__main__':build()
