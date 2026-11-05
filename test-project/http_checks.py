"""Black-box checks of the chosen local service. Use an isolated practice DB."""
import argparse,getpass,json,os,re,time
from pathlib import Path
import requests
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--branch',choices=['flask','php'],required=True);p.add_argument('--case',type=Path,required=True);p.add_argument('--admin',default='adminpm05');a=p.parse_args()
case=json.loads(a.case.read_text(encoding='utf-8'));base=a.base.rstrip('/');password=os.environ.get('PP05_ADMIN_PASSWORD') or getpass.getpass('Учебный пароль администратора: ')
results=[]
def url(page,tid=0):
    if a.branch=='php':return base+'/index.php?page='+{'detail':'ticket','list':'list'}.get(page,page)+(f'&id={tid}' if page in ('review','detail') else '')
    return base+{'list':'/','detail':f'/ticket/{tid}','review':f'/ticket/{tid}/review'}.get(page,'/'+page)
def check(name,ok):
    results.append({'case':name,'pass':bool(ok)});print(('PASS ' if ok else 'FAIL ')+name)
    if not ok:raise AssertionError(name)
def post(s,page,data,tid=0,csrf=True):
    page_for_token='list' if page in ('review','logout') else page
    r=s.get(url(page_for_token,tid),timeout=10)
    found=re.search(r'name="csrf" value="([^"]+)"',r.text)
    values={'csrf':found[1] if found else ''} if csrf else {};values.update(data)
    return s.post(url(page,tid),data=values,allow_redirects=False,timeout=10)
one,two,admin=requests.Session(),requests.Session(),requests.Session()
suffix=str(time.time_ns())[-9:];login1='client'+suffix;login2='second'+suffix
reg={'login':login1,'password':'Practice123','full_name':'Учебный Клиент','phone':'8(999)123-45-67','email':'client@example.test'}
try:
    for key,value in [('login','abc'),('password','1234567'),('full_name','User'),('full_name','   '),('phone','123'),('email','wrong')]:
        r=post(one,'register',{**reg,key:value});check('registration rejects '+key,r.status_code==200 and 'Проверьте введённые данные' in r.text)
    check('valid registration',post(one,'register',reg).status_code==302)
    r=post(one,'register',reg);check('unique login',r.status_code==200 and 'логин уже занят' in r.text)
    check('CSRF',post(one,'login',reg,csrf=False).status_code==400)
    r=post(one,'login',{'login':login1,'password':'Wrong123'});check('wrong password',r.status_code==200 and 'Неверный логин' in r.text)
    check('login client',post(one,'login',reg).status_code==302)
    check('second registration',post(two,'register',{**reg,'login':login2}).status_code==302)
    check('second login',post(two,'login',{'login':login2,'password':reg['password']}).status_code==302)
    check('admin login',post(admin,'login',{'login':a.admin,'password':password}).status_code==302)
    r=post(one,'new',case['invalid']);check('individual rule',r.status_code==200 and 'Проверьте введённые данные' in r.text)
    for key,value in [('service_id','999999'),('equipment','xx'),('equipment','x'*121),('symptom','no'),('symptom','x'*2001)]:
        r=post(one,'new',{**case['valid'],key:value});check('ticket rejects '+key,r.status_code==200 and 'Проверьте введённые данные' in r.text)
    r=post(one,'new',{**case['valid'],'user_id':'999999','status':'Завершена','role':'admin'});check('create',r.status_code==302)
    location=r.headers.get('Location','');match=re.search(r'(?:ticket/|id=)(\d+)',location);check('ticket identifier',match is not None);tid=int(match[1])
    r=one.get(url('detail',tid),timeout=10);check('own read and initial status',r.status_code==200 and f'Заявка №{tid} · Новая' in r.text)
    check('foreign read',two.get(url('detail',tid),timeout=10).status_code==404)
    check('client status forbidden',post(one,'detail',{'status':'В работе','technician_id':'1'},tid).status_code==403)
    check('review before completion',post(one,'review',{'body':'Спасибо за работу'},tid).status_code==409)
    r=post(admin,'detail',{'status':'Завершена','technician_id':'1','result':'Проверка результата'},tid);check('no skipped status',r.status_code==200 and 'Недопустимый переход' in r.text)
    r=post(admin,'detail',{'status':'В работе','technician_id':'999999'},tid);check('active technician',r.status_code==200 and 'Назначьте действующего' in r.text)
    r=post(admin,'detail',{'status':'В работе','technician_id':'1'},tid);check('start work',r.status_code==200 and f'Заявка №{tid} · В работе' in r.text)
    r=post(admin,'detail',{'status':'Завершена','technician_id':'1','result':''},tid);check('completion needs result',r.status_code==200 and 'Для завершения опишите результат' in r.text)
    r=post(admin,'detail',{'status':'Завершена','technician_id':'1','result':'Диагностика выполнена, дефект устранён'},tid);check('complete',r.status_code==200 and f'Заявка №{tid} · Завершена' in r.text)
    check('foreign review',post(two,'review',{'body':'Чужой отзыв'},tid).status_code==404)
    check('short review',post(one,'review',{'body':'x'},tid).status_code==400)
    check('completed own review',post(one,'review',{'body':'Спасибо за выполненную работу'},tid).status_code==302)
    check('single review',post(one,'review',{'body':'Повторный отзыв'},tid).status_code==409)
    check('logout',post(one,'logout',{}).status_code==302)
finally:
    Path('results.json').write_text(json.dumps({'variant':case['variant'],'branch':a.branch,'checks':results},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'{len(results)} checks passed; also compare SQL row counts and complete the manual browser route.')
