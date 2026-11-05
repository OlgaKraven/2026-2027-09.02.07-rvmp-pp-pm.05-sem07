from pathlib import Path
from copy import deepcopy
import shutil,hashlib,zipfile,json
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Mm
from docx.enum.table import WD_ROW_HEIGHT_RULE
import report_parts as parts
R=Path(__file__).resolve().parents[1]
MASTER=R/'forms/template/Отчет о выполнении.docx'
def text(e):return ''.join(t.text or '' for t in e.iter(qn('w:t')))
def labels(table,values,tag):
    original=deepcopy(table.rows[1]._tr)
    while len(table.rows)<len(values)+1:table._tbl.append(deepcopy(original))
    while len(table.rows)>len(values)+1:table._tbl.remove(table.rows[-1]._tr)
    for i,value in enumerate(values,1):
        for j,cell in enumerate(table.rows[i].cells):
            for k,c in enumerate(cell._tc.xpath('.//w:sdt')):
                c.find('w:sdtPr/w:tag',c.nsmap).set(qn('w:val'),f'{tag}_{i}_{j}_{k}')
                ts=list(c.find(qn('w:sdtContent')).iter(qn('w:t')));ts[0].text=value if j==0 else '____________'
                for t in ts[1:]:t.text=''
            if j==0 and not cell._tc.xpath('.//w:sdt'):
                ts=cell._tc.xpath('.//w:t');ts[0].text=value
                for t in ts[1:]:t.text=''
    for row in table.rows:row.height=Mm(10);row.height_rule=WD_ROW_HEIGHT_RULE.AT_LEAST
def build():
    assert hashlib.sha256(MASTER.read_bytes()).hexdigest()=='5b91286458395ae589ded859021f287ce50cca1148cc5b29226b6fb1cb5373c4'
    target=R/'forms/Отчет о выполнении.docx';shutil.copyfile(MASTER,target);doc=Document(target)
    for c in doc.element.xpath('.//w:sdt'):
        tag=c.find('w:sdtPr/w:tag',c.nsmap)
        if tag is not None and tag.get(qn('w:val'))=='practice_name':
            ts=list(c.find(qn('w:sdtContent')).iter(qn('w:t')));ts[0].text='Серверная часть сервиса заявок (ПМ.05)'
            for t in ts[1:]:t.text=''
    labels(doc.tables[0],['Номер и предметная область','Свой набор vNN и case.json','domain.json и схема собственной БД','Выбранная инструкция Flask либо PHP'],'inputs')
    labels(doc.tables[1],['Операционная система и редактор','Выбранный язык и библиотеки','MySQL/MariaDB и DBeaver','Браузер и адрес сервера'],'environment')
    labels(doc.tables[2],['Учебный сервис → своя область','Услуги и исполнители → свои справочники','Поля и правило → свои имена и ожидания','Номер заявки → фактический id своего клиента'],'mapping')
    final=['Выбрана одна серверная ветка','Поля и связи соответствуют области','Регистрация и сессия проверены','Своё правило реализовано и объяснено','Чужая заявка недоступна','Клиент не меняет статус','Переходы и исполнитель проверены','История атомарна и точна','Отзыв разрешён только владельцу после завершения','Прямые запросы и границы проверены','Чистая БД и повтор проверены','Репозиторий и документы доступны']
    labels(doc.tables[-1],final,'final')
    stages=[('Проектирование и данные','Зафиксировать свою область, выбранный стек, сущности и связи; объяснить справочники и типы.',['ER своей базы данных','Исходные справочники и поля варианта']),('Серверная регистрация и вход','Показать отказ ошибочных данных и успешный вход после исправления.',['Ошибка регистрации','Исправление и вход клиента']),('Собственное правило заявки','Записать ошибочный и допустимый случай до изменения; объяснить своё условие и повтор.',['Своё правило в редакторе','Отказ и восстановление своей заявки']),('Доступ к своим данным','Показать личный список и прямой запрос другого клиента к чужой записи.',['Мои заявки и фильтр','Отказ прямого доступа другому клиенту']),('Администратор и история','Проверить исполнителя, запрет завершения без результата, два перехода и три события истории.',['Заявка в работе и отказ пустого результата','Завершение и согласованная история']),('Отзыв и прямые запросы','Проверить ранний, чужой, короткий и повторный отзыв; сравнить количество строк после отказов.',['Отзыв владельца после завершения','Прямые запросы и состояние данных']),('Чистый повтор и передача','Повторить запуск в новой БД; сверить контракт, собственный репозиторий и официальные формы.',['Чистый повтор на новой базе','История проекта и комплект сдачи'])]
    cases=['Неверный логин','Короткий пароль','ФИО, телефон, email','Повторный логин','Неверный вход','Отсутствующий CSRF','Ошибочный случай варианта','Корректный случай варианта','Собственный соседний случай','Недействующая услуга','Прямая чужая карточка','Клиентский переход статуса','Недействующий исполнитель','Пропуск или обратный переход','Завершение без результата','Два правильных перехода','Ранний отзыв','Чужой отзыв','Короткий отзыв','Свой отзыв после завершения','Повторный отзыв','Чистая БД и повтор']
    body=doc.element.body;children=list(body);start=next(i for i,e in enumerate(children) if text(e)=='Этап выполнения работы');end=next(i for i,e in enumerate(children) if text(e)=='Итоговая проверка и сдача');anchor=children[end]
    for e in children[start:end]:body.remove(e)
    parts.CONTROL_ID=10000;fig=0
    for idx,(title,prompt,captions) in enumerate(stages,1):
        first=len(list(body))-1;parts.heading(doc,title,level=2,new_page=idx>1);doc.add_paragraph(prompt)
        for label,tag,lines in [('Исходные данные и ожидаемый результат','initial',2),('Выполненные действия','actions',3),('Фактический результат и проверка','actual',2),('Вывод по этапу и объяснение расхождений','conclusion',2)]:parts.response(doc,label,f's{idx}_{tag}',lines)
        if idx==6:
            doc.add_page_break();p=doc.add_paragraph(style='Table caption');p.add_run('Таблица ');parts.field(p,r'SEQ Таблица \* ARABIC','4');p.add_run(' — проверка сервиса заявок')
            table=doc.add_table(rows=len(cases)+1,cols=6);table.autofit=False;borders=parts.el('tblBorders')
            for side in ['top','left','bottom','right','insideH','insideV']:borders.append(parts.el(side,val='single',sz=4,color='000000'))
            table._tbl.tblPr.append(borders)
            for j,label in enumerate(['№','Случай','Вход','Ожидание','Факт / код','Данные / вывод']):table.cell(0,j).text=label
            for i,case in enumerate(cases,1):table.cell(i,0).text=str(i);table.cell(i,1).text=case
            for row in table.rows:
                row.height=Mm(14);row.height_rule=WD_ROW_HEIGHT_RULE.AT_LEAST
                for cell,w in zip(row.cells,[12,35,25,27,27,34]):
                    cell.width=Mm(w)
                    for p in cell.paragraphs:p.style='Table text'
            table.rows[0]._tr.get_or_add_trPr().append(parts.el('tblHeader'))
        doc.add_page_break();p=doc.add_paragraph();p.add_run('Подтверждения этапа приведены на рис. ')
        for j,caption in enumerate(captions):
            if j:p.add_run(', ')
            parts.field(p,f'REF pp05rvmp_fig_{fig+j+1} \\h',str(fig+j+1))
        p.add_run('. Вставить собственные результаты.')
        for caption in captions:
            fig+=1;parts.figure_slot(doc,caption,f'pp05rvmp_figure_{fig}',fig,f'pp05rvmp_fig_{fig}')
        for e in list(body)[first:-1]:body.remove(e);anchor.addprevious(e)
    for cid,c in enumerate(doc.element.xpath('.//w:sdt'),30000):c.find('w:sdtPr/w:id',c.nsmap).set(qn('w:val'),str(cid))
    doc.core_properties.title='Отчет о выполнении';doc.core_properties.subject='ПМ.05';doc.core_properties.author=doc.core_properties.last_modified_by='';doc.core_properties.comments=doc.core_properties.keywords=''
    for level in doc.part.numbering_part.element.findall('.//'+qn('w:lvl')):
        suffix=level.find(qn('w:suff'))
        if suffix is not None:suffix.set(qn('w:val'),'nothing')
        rpr=level.find(qn('w:rPr'))
        if rpr is None:rpr=parts.el('rPr');level.append(rpr)
        fonts=rpr.find(qn('w:rFonts'))
        if fonts is None:fonts=parts.el('rFonts');rpr.append(fonts)
        for attr in ('ascii','hAnsi','eastAsia','cs'):fonts.set(qn('w:'+attr),'Times New Roman')
        for attr in ('asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme'):fonts.attrib.pop(qn('w:'+attr),None)
    for p in doc.paragraphs:
        if p.style.name in ('Heading 1','Heading 2','Heading 3') and p.runs:p.runs[0].text=' '+p.runs[0].text
        if p.text=='Состав передаваемых материалов':p.paragraph_format.page_break_before=True
    doc.save(target)
    with zipfile.ZipFile(target) as z:edited={n:z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(MASTER) as z:original={n:z.read(n) for n in z.namelist()}
    allowed={'word/document.xml','docProps/core.xml','word/numbering.xml'}
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name,value in original.items():z.writestr(name,edited[name] if name in allowed else value)
    shutil.copyfile(target,R/'site/downloads/Отчет о выполнении.docx')
    (R/'output/report-origin.json').write_text(json.dumps({'master_sha256':hashlib.sha256(MASTER.read_bytes()).hexdigest(),'stages':len(stages),'figures':fig,'cases':len(cases),'unrelated_parts_preserved':True},indent=2),encoding='utf-8')
    print('Copied and adapted master:',len(stages),'stages,',fig,'frames,',len(cases),'blank cases')
if __name__=='__main__':build()
