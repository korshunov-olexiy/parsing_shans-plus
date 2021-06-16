# coding=utf-8

import sys, os, inspect
import configparser as INI
import re
import sqlite3
from sqlite3 import Error
from tkinter import messagebox


def get_script_dir(follow_symlinks=True):  # Получить путь к этому скрипту (c разделителем каталогов для целевой системы в конце)
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path) + os.path.sep


# получаем адреса разделов с объявлениями которые нужно обработать
def get_config(cnf_file):
    config = INI.ConfigParser()
    config.sections()
    if len(list(config.read(cnf_file, encoding='utf8'))) == 0:
        config['MAIN'] = {}   # сначала создаем раздел 'MAIN', а потом в этом разделе создаем секцию 'MAIN'
        config['MAIN']['name_of_out_file'] = "shansplus_"
        config['MAIN']['save_to_excel'] = '1'
        config['PAGES_LOAD'] = {}  # сначала создаем раздел 'PAGES_LOAD', а потом в этом разделе создаем секции 'cnt_pages' и 'cnt_items'
        config['PAGES_LOAD']['cnt_pages'] = '5'
        config['PAGES_LOAD']['cnt_items'] = '30'
        config['URLS'] = {}  # сначала создаем раздел 'URLS', а потом в этом разделе создаем секцию 'list_of_categories'
        config['URLS']['list_of_categories'] = "http://shansplus.com.ua/ad-category/nedvizhimost/kvartiryi-prodazha/101/page/,http://shansplus.com.ua/ad-category/nedvizhimost/kvartiryi-prodazha/102/page/,http://shansplus.com.ua/ad-category/nedvizhimost/kvartiryi-prodazha/103/page/,http://shansplus.com.ua/ad-category/nedvizhimost/kvartiryi-prodazha/104/page/,http://shansplus.com.ua/ad-category/nedvizhimost/kvartiryi-prodazha/105/page/,http://shansplus.com.ua/ad-category/nedvizhimost/kvartiryi-prodazha/106/page/,http://shansplus.com.ua/ad-category/nedvizhimost/doma-dachi-uchastki-prodazha/160/page/,http://shansplus.com.ua/ad-category/nedvizhimost/doma-dachi-uchastki-prodazha/165/page/"
        #config['xpath'] = {} # сначала создаем раздел 'xpath', а потом в этом разделе создаем секцию 'xpath'
        #config['xpath']['ad_xpath'] = "/html/body/div[1]/div[4]/div/div/div[2]/div[{}]/div/div[2]/p[3]"
        try:
            with open(cnf_file, 'w', encoding='utf8') as configfile:
                config.write(configfile)
        except Exception as err:
            messagebox.showerror('Помилка створення файлу', 'Відсутній конфігураційний файл.\nПід час створення файлу ' + cnf_file + ' виникла помилка:\n\n' + str(err))
            sys.exit(-1)
    params = {}
    params['list_of_categories'] = config['URLS']['list_of_categories'].split(',')
    #params['ad_xpath'] = config['xpath']['ad_xpath']
    params['cnt_pages'] = int(config['PAGES_LOAD']['cnt_pages'])
    #params['cnt_items'] = int(config['PAGES_LOAD']['cnt_items'])
    params['name_of_out_file'] = config['MAIN']['name_of_out_file']
    params['save_to_excel'] = int(config['MAIN']['save_to_excel'])
    return params

# Work with SQLite database
def create_connection(db_file):
    try:
        return sqlite3.connect(db_file, uri=True)
    except Error as e:
        messagebox.showerror('Помилка підключення до БД', e)
        sys.exit(-1)


def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        messagebox.showerror('Помилка створення таблиці БД', e)
        sys.exit(-1)


def query_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        return c.fetchall()
    except Error as e:
        messagebox.showerror('Помилка отримання даних з БД', e)
        sys.exit(-1)


def create_notices(conn, notice): # INSERT DATA TO 'NOTICES' TABLE
    sql = """INSERT INTO notices(site, area, notice, price, phones) VALUES(?,?,?,?,?);"""
    cur = conn.cursor()
    cur.execute(sql, notice)
    return cur.lastrowid


# очищаем от "НЕ ЦИФР" номер телефона и если это не городской номер (6 симв.) сначала номера удаляем "38" и "+38"
def clear_phone_number(tlf):
    tlf = ''.join( list(filter(lambda x: x.isdigit(), tlf)) )
    if len(tlf) == 6:
        return tlf
    else:
        return re.sub('^38', '',  tlf)


# очищаем от НЕ ЦИФР и разделяем "," городские номера телефонов (6 симв.)
def format_city_phone_number(tlfs):
    tlf = ''.join( list(filter(lambda x: x.isdigit(), tlfs)) )
    result = ''
    for i in range(0, len(tlf), 6):
        result = result + ',' + tlf[i:i+2] + '-' + tlf[i+2:i+4] + '-' + tlf[i+4:i+6]
    return result[1:]


# Проверяет есть ли в базе 'realities_numbers.txt' переданный список номеров nr, разделенных ","
def is_in_reality_db(path_to_script, nr):
    reality_db = path_to_script + 'realities_numbers.txt'
    nr = nr.split(",")
    if os.path.isfile(reality_db):
        with open(reality_db, 'r') as f_db:
            for line in f_db:
                for i_nr in nr:
                    i_nr = clear_phone_number(i_nr)
                    line = clear_phone_number(line)
                    if line == i_nr:
                        f_db.close()
                        return True
            f_db.close()
            return False
    else:
        return False


# Выводим в файл "name_of_file" начало нашей странички
def save_to_html_begin(name_of_file):
    html_file = open(name_of_file, 'w+', encoding='utf-8')
    html_file.write("""<html>
    <head>
    <meta charset='UTF-8'>
    <style type='text/css'>
        @import url('https://fonts.googleapis.com/css?family=Open+Sans+Condensed:300');
        @import url('https://fonts.googleapis.com/css?family=PT+Sans+Narrow');
        /* configure style for 'text input' element (class as FilterInput) */
        #FilterInput {
            -webkit-transition: width 0.4s ease-in-out;
            transition: width 0.4s ease-in-out;
            width: 25%; padding: 12px 35px; margin: 8px 0; box-sizing: border-box; border: 2px solid rgb(0, 255, 221); border-radius: 4px; background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABUAAAAVCAMAAACeyVWkAAAAbFBMVEUAAACJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYnP5CKoAAAAI3RSTlMABOpSMvaCEPnVuZ10OR3mqW5dQfPd2s7CoZOJZyoLrnlNLe8Vj2gAAACvSURBVBjTlZBJDoMwEARtA2aHELKwhSz1/z8GMRgQOaVP5dK0PBr1b8IquZo49fReVhcksb/JFOB2N0DgOZkBXTFB3kz6IbKI4CyoT5AIWkhdbSxBhhvY/uhhmOEK20JnsDPEEK52gNcMJ5B13MOV4nGRPgRS1DdIQpEl9G4gAGNr30sjoPwsujbsYvJFF20kIkuAS72e0stslWuln0DwVofoFogKdUwH5Oon2d2qL01WERJUYahMAAAAAElFTkSuQmCC"); background-position: 10px 10px; background-repeat: no-repeat;
        }
        #FilterInput:focus { width: 100%; }
        tbody tr:nth-child(odd) { background: rgb(243, 243, 163) }
        tbody tr:nth-child(even) { background: rgb(157, 230, 230) }
        tbody { font-family: 'PT Sans Narrow', sans-serif }
        thead { background: rgb(104, 153, 194) linear-gradient(rgba(0, 0, 0, 0) 50%, rgba(0, 0, 0, .2) 50%) center center / 100% 1em; text-transform: uppercase; height: 25px; font-family: 'Open Sans Condensed', sans-serif; }
        table { border: solid }
        </style>
    </head>
    <body>
    <input id='FilterInput' onkeyup='searchTable()' type='text' placeholder='Введите текст для фильтрации таблицы'>
    <table id='TableData'>
        <thead>
            <tr>
                <th>Сайт</th><th>Вулиця/район</th><th>Інформація</th><th>Ціна</th><th>Телефони</th><th>Дата вивантаження</th>
            </tr>
        </thead>
        <tbody>""")
    return html_file


# Дописываем в открытый файл (obj_file) окончание
def save_to_html_end(obj_file):
    obj_file.write("</tbody>\n</table>\n")
    obj_file.write("""<script>
    function searchTable() {
        var input, filter, found, table, tr, td, i, j;
        input = document.getElementById("FilterInput");
        filter = input.value.toUpperCase();
        table = document.getElementById("TableData");
        //find all class as 'DataFild'
        tr = table.getElementsByClassName("DataFild");
        for (i = 0; i < tr.length; i++) {
            td = tr[i].getElementsByTagName("td");
            for (j = 0; j < td.length; j++) { if (td[j].innerHTML.toUpperCase().indexOf(filter) > -1) { found = true; } }
            if (found) { tr[i].style.display = ""; found = false; } else { tr[i].style.display = "none"; }
        }
    }
    </script>\n""")
    obj_file.write("</body>\n</html>")
    obj_file.close()
