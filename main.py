# coding=utf-8
# import main function from file function.py
import own_function as mainFunc
import re, urllib.request #sys, os, inspect
import xlwt
from xlwt import Workbook
from requests_html import HTML
from datetime import datetime

# класс констант для окна сообщений функции ShowMessage
class _Const(object):
    ICON_EXLAIM = 0x30  # желтый треугольник
    ICON_INFO = 0x40    # синий восклицательный знак
    ICON_STOP = 0x10    # красный крестик
    MB_OK = 0
    #MB_OKCANCEL = 1, MB_ABORTRETRYIGNORE = 2, MB_YESNOCANCEL = 3, MB_YESNO = 4, MB_RETRYCANCEL = 5, MB_CANCELTRYCONTINUE = 6, MB_HELP = 0x4000

# константы для окна сообщений - функция ShowMessage
CONST = _Const()
today_now = datetime.now().strftime("%d%m%Y-%H%M%S")
cur_date = datetime.now().strftime("%d.%m.%Y")
current_path = mainFunc.get_script_dir()
config_file = current_path + "config.ini"
sqlite_db = current_path + "notices.db"

conn = mainFunc.create_connection(sqlite_db)
# site - с какого сайта взята информация; area - улица, квартал и т.п.; notice - текст объявления; phones - номера телефонов в объявлениях; date_set - дата получения информации;
mainFunc.create_table(conn, """CREATE TABLE IF NOT EXISTS notices(id integer PRIMARY KEY, site text, area text, notice text, price text, phones text, date_set TIMESTAMP DEFAULT CURRENT_DATE)""")

# получаем настройки из ini-файла
cnf_params = mainFunc.get_config(config_file)
# список адресов сайта shansplus.com.ua, по которым будут собираться объявления
list_categories = cnf_params['list_of_categories']
# единый xpath-путь к объявлениям на страницах сайта
site_xpath = cnf_params['ad_xpath']
# кол-во страниц одного раздела для просмотра
cnt_pages = cnf_params['cnt_pages']
# кол-во объявлений на каждой странице
cnt_items = cnf_params['cnt_items']
name_of_out_file = cnf_params['name_of_out_file']
# если save_to_excel = 1 - выводить результат в книгу Excel, иначе в html-файл
save_to_excel = cnf_params['save_to_excel']

if save_to_excel == 1:  # если выводим в Excel, то расширение создаваемого файла - .xls, иначе - .htm
    ext_file = '.xls'
else:
    ext_file = '.htm'

# получаем объявления по адресам с подготовленного списка категорий
k = 0
for url_category in list_categories:
    i=1
    sheet_line = -1  # номер строки на листе Excel
    while i <= cnt_pages:
        try:
            doc = urllib.request.urlopen(url_category+str(i))
            doc_loaded = doc.read().decode('utf8')
            doc.close()
            html = HTML(html=doc_loaded)
            # name_site - для поля базы данных 'site' (сайт, с которого была получена инфо)
            try:
                name_site = html.xpath('/*/head/title', first=True).text  # пытаемся получить заголовок страницы
                name_site = name_site.split(' – ')
                name_site = name_site[0]
            except:
                name_site = "Шанс+"
            if (name_site == '') or (name_site is None):
                name_site = "Шанс+"
        except urllib.error.HTTPError as e:
            #mainFunc.ShowMessage('HTTPError', str(e.code), CONST.MB_OK | CONST.ICON_EXLAIM)
            #return e.code
            break
        except urllib.error.URLError as e:
            #mainFunc.ShowMessage('URLError', str(e.reason), CONST.MB_OK | CONST.ICON_EXLAIM)
            #return str(e.reason)
            break
        except Exception:
            import traceback
            #mainFunc.ShowMessage('generic exception', traceback.format_exc(), CONST.MB_OK | CONST.ICON_EXLAIM)
            break
            #return traceback.format_exc()
        j=1
        while j<=cnt_items:
            # Find all notice on the page
            clr = html.xpath(site_xpath.format( str(j) ), first=True)
            if clr is None: # если не удалось получить текст объявления - выдать ошибку и выйти из цикла
                break
            # паттерны для поиска цены в объявлении
            # search_pattern = [r'\d{1,}\ у\.е\.\ \–\ \d{1,}\ грн\.', r'\d{1,}\ у\.е\.\ \–\ \d{1,}млн\.\ грн\.', r'\d{1,}\ у\.е\.\ \–\ \d{1,}\ млн\.\ грн\.', r'\$\d{1,}\ тыс\.\ \–\ \d{1,}\ грн\.', r'\$\d{1,}\ \–\ \d{1,}\ грн\.', r'\d{1,}\ грн\.']
            search_pattern = [r'[\d\,\.]{1,}[ \t]{0,}(?:млн|тис|тыс){0,}[\.]{0,}[ \t]{0,}грн[\.]{0,}', r'\$[ \t]{0,}[\d\,\.]{1,}', r'[\d\,\.]{1,}[ \t]{0,}(?:у\.е\.|уе\.|у\.е|уе)']
            for pattern in search_pattern:  # пытаемся найти цену в объявлении
                price = re.search(pattern, clr.text)
                if bool(price):  # если мы нашли цену, т.е. True
                    price = price.group(0) #сохраняем 1-ое найденное значение (других по идее не должно и быть)
                    break
            if price is None:  # если не нашли цены ни по одному паттерну - записать пустую строку
                price = ''
            # Находим все телефоны в объявлении (считаем, что после " т. " в объявлении идут номера телефонов)
            try:
                tlfs = clr.text.split(sep=' т. ', maxsplit=1)[1].replace(' ','')  # получаем подстроку с номерами телефонов
                tlfs = re.sub(r'[^\d\-\,].+$', '', tlfs)  # очищаем номера телефонов от лишних символов вконце
            except:
                tlfs = ''
            try:
                # получаем объявление, убирая номера телефонов
                notice = re.search(r'(.+)т\.\ ', clr.text).group(1)
                split_notice = notice.split(', ', maxsplit=1)
                notice_area = split_notice[0] # Area (street, district & etc...)
                try:
                    notice_info = split_notice[1] # Other info from notice
                except:
                    notice_info = ''
            except:
                notice = None
            # если в базе номеров риэлторов данного номера телефона нету (т.е. это номер тлф частного лица)
            if mainFunc.is_in_reality_db(current_path, tlfs) == False:
                # Создаем запрос, который отбирает такие же записи в базе (если они есть)
                sql_notice = "SELECT site, area, notice FROM notices WHERE (site = '" + name_site + "' AND area = '" + notice_area + "' AND notice = '" + notice_info + "');"
                db_notice = mainFunc.query_table(conn, sql_notice)
                # если запрос не вернул данные - сохранить информацию как новую
                if (len(set(db_notice)) == 0):
                    with conn:
                        notice = (name_site, notice_area, notice_info, price, tlfs)
                        mainFunc.create_notices(conn, notice)
                    k += 1  # обновляем колличество найденных объявлений
                    sheet_line += 1  # обновляем номер строки для листа Excel
                    if k == 1:  # если мы нашли первое объявление
                        if save_to_excel == 1:
                            wb = Workbook()  # create Excel sheet
                        else:
                            # save begin data to out html-file
                            f_html = mainFunc.save_to_html_begin(current_path + name_of_out_file + today_now + ext_file)
                    if save_to_excel == 1:
                        try:  # пробуем создать лист. Если он уже существует - игнорировать
                            sheets = wb.add_sheet(name_site, cell_overwrite_ok=True)
                            # настраиваем ширину колонок на листе Excel (0x10F - это примерно 1 для ширины в Excel)
                            sheets.col(0).width = 0x10F * 23   # стоблец "улица"
                            sheets.col(1).width = 0x10F * 115  # стоблец "объявление"
                            sheets.col(2).width = 0x10F * 13   # стоблец "цена"
                            sheets.col(3).width = 0x10F * 21   # стоблец "номер тлф"
                            sheets.col(4).width = 0x10F * 10   # стоблец "дата выгрузки"
                        except:
                            pass
                        # выводим данные на лист Excel (sheet_line - номер строки, [0,1,2] - номера колонок)
                        sheets.write( sheet_line, 0, notice_area )
                        sheets.write( sheet_line, 1, notice_info )
                        sheets.write( sheet_line, 2, price )
                        sheets.write( sheet_line, 3, tlfs.replace(',',', ') )
                        sheets.write( sheet_line, 4, cur_date )
                    else:
                        f_html.write("<tr class='DataFild'><td>" + name_site + "</td><td>" + notice_area + "</td><td>" + notice_info + "</td><td>" + price + "</td><td>" + tlfs.replace(',',', ') + "</td><td>" + cur_date + "</td></tr>\n")
            j += 1
        i += 1

# --- завершаем запись в отчет по найденным объявлениям
if k == 0:  # если не нашли ни одного нового объявления
    # Если объявления не найдены
    mainFunc.ShowMessage('Завершение работы', 'Новые объявления НЕ НАЙДЕНЫ', CONST.MB_OK | CONST.ICON_INFO)
else:
    if save_to_excel == 1:  # если в конфиге указали что выводить данные в Excel
        wb.save(current_path + name_of_out_file + today_now + ext_file)
    else:
        mainFunc.save_to_html_end(f_html)
    # Выводим сообщение о завершении работы программы
    mainFunc.ShowMessage('Завершение работы','Найдено ' + str(k) + ' объявлений(я).\nСоздан файл ' + name_of_out_file + today_now + ext_file, CONST.MB_OK | CONST.ICON_INFO)
