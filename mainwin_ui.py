# *-* encoding=utf-8

import os
from sys import exit
import tkinter as tk
from tkinter.constants import CENTER
from tkinter.font import BOLD
import tkinter.ttk as ttk
from tkinter import messagebox
import tkinter.scrolledtext as scrolledtext

import own_function as mainFunc
import re, urllib.request
from xlwt import Workbook
from requests_html import HTML
from datetime import datetime
from bs4 import BeautifulSoup as bs
import configparser as INI


class MainwindowApp:
    def __init__(self, master=None):
        # get setting from ini-file
        self.today_now = datetime.now().strftime("%d%m%Y-%H%M%S")
        self.cur_date = datetime.now().strftime("%d.%m.%Y")
        self.current_path = mainFunc.get_script_dir()
        self.config_file = self.current_path + "config.ini"
        self.sqlite_db = self.current_path + "notices.db"
        self.conn = mainFunc.create_connection(self.sqlite_db)
        # site - с какого сайта взята информация; area - улица, квартал и т.п.; notice - текст объявления; phones - номера телефонов в объявлениях; date_set - дата получения информации;
        mainFunc.create_table(self.conn, """CREATE TABLE IF NOT EXISTS notices(id integer PRIMARY KEY, site text, area text, notice text, price text, phones text, date_set TIMESTAMP DEFAULT CURRENT_DATE)""")
        # получаем настройки из ini-файла
        cnf_params = mainFunc.get_config(self.config_file)
        self.name_of_out_file = cnf_params['name_of_out_file']
        # если save_to_excel = 1 - выводить результат в книгу Excel, иначе в html-файл
        save_to_excel = int(cnf_params['save_to_excel'])
        # кол-во страниц одного раздела для просмотра
        cnt_pages = cnf_params['cnt_pages']
        # список адресов сайта shansplus.com.ua, по которым будут собираться объявления
        list_categories = cnf_params['list_of_categories']
        self.toplevel1 = tk.Tk() if master is None else tk.Toplevel(master)
        # перехват закрытия окна с назначением своей функции onExit
        self.toplevel1.wm_protocol( "WM_DELETE_WINDOW", self.onExit )
        self.mainwindow = tk.Frame(self.toplevel1)
        self.start_name_file = tk.Label(self.mainwindow)
        self.start_name_file.configure(font='{DejaVu Sans} 12 {}', text='Початок імені файлу')
        self.start_name_file.grid(sticky='nw')
        # создаем и настраиваем поле (Entry) с кол-вом просматриваемых страниц
        self.ent_begin_file = tk.Entry(self.mainwindow)
        self.ent_begin_file.configure(font='{DejaVu Sans} 12 {}', width='50')
        self.ent_begin_file.grid(padx='5', row='1', sticky='nw')
        # вставляем значения из ini-файла
        self.ent_begin_file.delete(0, tk.END)
        self.ent_begin_file.insert(0, self.name_of_out_file)
        # создаем и настраиваем контрол CheckButton
        self.chkBtn_excel_file = ttk.Checkbutton(self.mainwindow)
        self.chk_excel_state = tk.IntVar()
        self.chkBtn_excel_file.configure(offvalue='0', onvalue='1', text='Зберегти в Excel-файл', variable=self.chk_excel_state)
        self.chkBtn_excel_file.grid(column='0', pady='6', row='2', sticky='nw')
        self.chk_excel_state.set(save_to_excel)
        # set style for spinbox
        styleSpinBox = ttk.Style()
        styleSpinBox.theme_use('default')
        styleSpinBox.configure('My.TSpinbox', arrowsize=15)
        self.spinbox_cnt_pages = ttk.Spinbox(self.mainwindow, style='My.TSpinbox')
        self.spinbox_cnt_pages.configure(font='{DejaVu Sans} 12 {}', from_='0', to='1000', increment='1', justify='right', width='10')
        self.spinbox_cnt_pages.delete( 0, tk.END )
        # вставляем число страниц из ini-файла
        self.spinbox_cnt_pages.insert( 0, cnt_pages )
        self.spinbox_cnt_pages.grid(column='0', pady='6', row='4', sticky='nw')
        self.lbl_cnt_pages = ttk.Label(self.mainwindow)
        self.lbl_cnt_pages.configure(font='{DejaVu Sans} 12 {}', text='Кіл-ть сторінок, на яких будуть шукатись оголошення:')
        self.lbl_cnt_pages.grid(column='0', row='3', sticky='nw')
        self.lbl_list_url = ttk.Label(self.mainwindow)
        self.lbl_list_url.configure(font='{DejaVu Sans} 12 {}', text='Список url-адрес для пошуку оголошень')
        self.lbl_list_url.grid(column='0', pady='6', row='5', sticky='nw')
        # создаем и настраиваем ScrolledText (list of urls)
        self.txt_list_url = scrolledtext.ScrolledText(self.mainwindow, undo=True)
        self.txt_list_url.configure(font='{DejaVu Sans} 10 {}', height='10', relief='sunken', width='63', wrap='word',)
        self.txt_list_url.insert( tk.INSERT, list_categories )
        self.txt_list_url.grid(column='0', row='6', sticky='nsew')
        # определяем общий стиль для кнопок
        btns_style = ttk.Style()
        btns_style.configure('my.TButton', font=('Helvetica', 10, BOLD))
        # кнопка сохранения настроек
        self.btn_save_setting = ttk.Button(self.mainwindow)
        self.btn_save_setting.configure(text='Зберегти параметри', style='my.TButton')
        self.btn_save_setting.grid(column='0', pady='6', row='7', sticky='nw')
        self.btn_save_setting.configure(command=lambda: self.save_setting())
        # кнопка поиска объявлений
        self.btn_start = ttk.Button(self.mainwindow)
        self.btn_start.configure(text='Отримати нові оголошення', style='my.TButton')
        self.btn_start.grid(column='0', pady='6', padx='165', row='7', sticky='nw')
        self.btn_start.configure(command=lambda: self.get_new_ads())
        # настройка окна
        self.mainwindow.configure(height='200', padx='5', pady='5', width='200')
        self.mainwindow.grid(column='0', row='0', sticky='nw')
        self.toplevel1.configure(height='200', width='200')
        self.toplevel1.resizable(False, False)
        self.toplevel1.title('Пошук оголошень')
        self.mainwindow = self.toplevel1


    def save_setting(self):
        config = INI.ConfigParser()
        config.read(self.config_file)
        # сохраняем данные в раздел 'MAIN'
        config['MAIN'] = { 'name_of_out_file': self.ent_begin_file.get(), 'save_to_excel': self.chk_excel_state.get() }
        # сохраняем данные в раздел 'PAGES_LOAD'
        config['PAGES_LOAD'] = { 'cnt_pages': self.spinbox_cnt_pages.get() }
        config['URLS'] = {'list_of_categories': ','.join(self.txt_list_url.get("1.0", "end-1c").split())}
        # сохраняем изменения в ini-файл
        with open(self.config_file, 'w') as c_file:
            config.write(c_file)
        messagebox.showinfo('Збереження налаштувань', 'Налаштування успішно збережені')


    def get_new_ads(self):
        # если выводим в Excel, то расширение создаваемого файла - ".xls", иначе - ".htm"
        ext_file = '.xls' if self.chk_excel_state.get() == 1 else '.htm'
        # получаем объявления по адресам с подготовленного списка категорий
        k = 0
        # цикл по всем urls из списка адресов (берем из контрола txt_list_url)
        for url_category in self.txt_list_url.get("1.0", "end-1c").split():
            i = 1
            sheet_line = -1  # номер строки на листе Excel
            while i <= int(self.spinbox_cnt_pages.get()):
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
                    break
                except urllib.error.URLError as e:
                    break
                except Exception:
                    break

                html = bs(html.html, 'html.parser')
                for elem in html.body.findAll('div', attrs={'class':'post-right full'}):
                    clr = elem.find('p', attrs={'class': 'post-desc'}).text[:-1]
                    if clr is None: break
                    search_pattern = [r'[\d\,\.]{1,}[ \t]{0,}(?:млн|тис|тыс){0,}[\.]{0,}[ \t]{0,}грн[\.]{0,}', r'\$[ \t]{0,}[\d\,\.]{1,}', r'[\d\,\.]{1,}[ \t]{0,}(?:у\.е\.|уе\.|у\.е|уе)']
                    for pattern in search_pattern:
                        price = re.search(pattern, clr)
                        if bool(price):  # если мы нашли цену, т.е. True
                            price = price.group(0)
                            break
                        if price is None:
                            price = ''
                    try:
                        tlfs = clr.split(sep=' т. ', maxsplit=1)[1].replace(' ','')  # получаем подстроку с номерами телефонов  
                        tlfs = re.sub(r'[^\d\-\,].+$', '', tlfs)  # очищаем номера телефонов от лишних символов вконце
                    except:
                        tlfs = ''
                    try:
                        notice = re.search(r'(.+)т\.\ ', clr).group(1)
                        split_notice = notice.split(', ', maxsplit=1)
                        notice_area = split_notice[0] # Area (street, district & etc...)
                        try:
                            notice_info = split_notice[1] # Other info from notice
                        except:
                            notice_info = ''
                    except:
                        notice = None
                    if mainFunc.is_in_reality_db(self.current_path, tlfs) == False:
                        # Создаем запрос, который отбирает такие же записи в базе (если они есть)
                        sql_notice = "SELECT site, area, notice FROM notices WHERE (site = '" + name_site + "' AND area = '" + notice_area + "' AND notice = '" + notice_info + "');"
                        db_notice = mainFunc.query_table(self.conn, sql_notice)
                        # если запрос не вернул данные - сохранить информацию как новую
                        if (len(set(db_notice)) == 0):
                            with self.conn:
                                notice = (name_site, notice_area, notice_info, price, tlfs)
                                mainFunc.create_notices(self.conn, notice)
                            k += 1  # обновляем колличество найденных объявлений
                            sheet_line += 1  # обновляем номер строки для листа Excel
                            if k == 1:  # если мы нашли первое объявление
                                if self.chk_excel_state.get() == 1:
                                    wb = Workbook()  # create Excel sheet
                                else:
                                    # save begin data to out html-file
                                    f_html = mainFunc.save_to_html_begin(self.current_path + self.ent_begin_file.get() + self.today_now + ext_file)
                            if self.chk_excel_state.get() == 1:
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
                                sheets.write( sheet_line, 4, self.cur_date )
                            else:
                                f_html.write("<tr class='DataFild'><td>" + name_site + "</td><td>" + notice_area + "</td><td>" + notice_info + "</td><td>" + price + "</td><td>" + tlfs.replace(',',', ') + "</td><td>" + self.cur_date + "</td></tr>\n")
                i += 1

        # --- завершаем запись в отчет по найденным объявлениям
        if k == 0:  # если не нашли ни одного нового объявления
            # Если объявления не найдены
            messagebox.showinfo('Завершення роботи', 'Нові оголошення НЕ ЗНАЙДЕНІ')
        else:
            if self.chk_excel_state.get() == 1:  # если в конфиге указали что выводить данные в Excel
                wb.save(self.current_path + self.ent_begin_file.get() + self.today_now + ext_file)
            else:
                mainFunc.save_to_html_end(f_html)
            # Выводим сообщение о завершении работы программы
            messagebox.showinfo('Завершення роботи','Знайдено ' + str(k) + ' оголошень(ня).\nСтворений файл ' + self.ent_begin_file.get() + self.today_now + ext_file)


    # Процедура, которая сработает при закрытии окна
    def onExit(self):
        exit()


    def run(self):
        self.mainwindow.mainloop()
