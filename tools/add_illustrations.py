from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
p=R/'content/materials.json';d=json.loads(p.read_text(encoding='utf-8'))
for page in d['guide']:page['blocks']=[b for b in page['blocks'] if b['kind']!='image']
def image(name,title,caption,clip=None):
    b={'kind':'image','title':title,'path':'evidence/windows/'+name,'text':caption}
    if clip:b['clip']=dict(zip(['x','y','w','h'],clip))
    return b
def add(title,b):
    assert (R/b['path']).is_file(),b['path']
    page=next(x for x in d['guide'] if title in x['title'])
    if not any(x.get('title')==b['title'] for x in page['blocks']):page['blocks'].append(b)
for page in d['guide']:
    for b in page['blocks']:
        if b['kind']=='text':b['text']=b['text'].replace('«Просмотреть диаграмму»','«Создать новую диаграмму». Ввести название, оставить выделенными шесть своих таблиц и нажать «Готово»').replace('кнопкой сохранения изображения','кнопкой «Сохранить диаграмму во внешнем формате» в нижней панели. Выбрать PNG и путь, нажать «Сохранить»; в вопросе об открытии допустимо выбрать «Нет». Сохранить')
add('База данных',image('er-export.png','Связи собственной модели','В DBeaver создана и экспортирована диаграмма шести таблиц. Проверяются внешние ключи и единственный отзыв на заявку.'))
add('Реализация правила',image('rule-editor.png','Редактирование условия','В Блокноте заполнен rules: условие по услуге требует ответа adapter. Сохранение выполнено в UTF-8.',(14,467,650,205)))
add('Проверка клиента',image('flask-registration-error.png','Серверный отказ регистрации','Flask: короткий логин отклонён; форма остаётся открытой, пароль очищен.',(154,244,940,370)))
add('Проверка клиента',image('flask-rule-error.png','Отказ предметной проверки','Flask: правило выполняется на сервере до INSERT; остальные данные формы сохранены.',(154,270,950,185)))
add('Проверка клиента',image('flask-created.png','Допустимый ответ «Нет»','Flask: после выбора «Нет» создаётся собственная заявка. Отсутствие блока питания и отсутствие ответа — разные случаи.',(154,265,940,400)))
add('Проверка клиента',image('php-foreign-404.png','Прямой запрос другого клиента','PHP: другой клиент открывает известный адрес заявки и получает 404, данные владельца не возвращаются.',(0,0,620,70)))
add('Администратор',image('flask-completion-error.png','Завершение без результата отклонено','Flask: после отказа заявка остаётся «В работе». Для продолжения нужно заполнить результат.',(154,270,950,185)))
add('Администратор',image('flask-completion-error.png','Поле описания результата','В поле под исполнителем ввести содержательный результат и повторить «Завершить заявку». На снимке показано исходное пустое поле.',(154,820,950,300)))
add('Администратор',image('flask-review.png','Три успешных события','Flask: создание, принятие в работу и завершение. Отказы не добавляют событий.',(154,0,940,410)))
add('Отзыв владельца',image('flask-review.png','Сохранённый отзыв','Flask: владелец завершённой заявки сохранил отзыв; повторная форма больше не предлагается.',(154,459,940,205)))
add('Отзыв владельца',image('php-review.png','Тот же серверный результат PHP','PHP: история и сохранённый отзыв повторно отображаются после чтения карточки.',(154,459,940,205)))
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('Added real illustrations with readable page regions; source screenshots unchanged')
