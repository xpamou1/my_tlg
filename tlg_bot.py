# coding: utf-8
import time
import telepot
import telepot.helper
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telepot.delegate import (
    per_chat_id, create_open, pave_event_space, include_callback_query_chat_id)

from pprint import pprint
from datetime import datetime
import db.my_db as db

our_dict = telepot.helper.SafeDict()  # thread-safe dict
TIME_FORMAT = "%H:%M"

MENU_KEY = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Start')],
    [KeyboardButton(text='Statistic')],
], resize_keyboard=True)

DATE_CALENDARE = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='DATE', callback_data='date')],
        [InlineKeyboardButton(text='DEL', callback_data='del'), ]])

DEL = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text='DEL', callback_data='del'), ]])

TIME_IN_BUTTON = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text='IN TIME', callback_data='in_time'), ]])

TIME_OUT_BUTTON = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text='OUT TIME', callback_data='out_time'), ]])


class TimeManager(telepot.helper.ChatHandler):

    def __init__(self, *args, **kwargs):
        super(TimeManager, self).__init__(*args, **kwargs)
        self.in_time = None
        self.out_time = None
        self.work_time = None
        self.week_day = None
        self.state = {'state': 'index'}

    def start_page(self):
        self.sender.sendMessage(u'Добрый день', reply_markup=MENU_KEY, )

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            if msg['text'] == 'Start':
                pprint(msg)
                self.check_work_day()
                self.state['state'] = 'wait_in_time'
                self.sender.sendMessage(u'Введите время прихода в формате час:мин\nЛибо нажмите кнопку',
                                        reply_markup=TIME_IN_BUTTON)
            elif self.state['state'] == 'wait_in_time':
                self.in_time = self.check_time(msg['text'])
                self.state['state'] = 'wait_out_time'
                self.sender.sendMessage(u'Введите время ухода в формате час:мин\nЛибо нажмите кнопку',
                                        reply_markup=TIME_OUT_BUTTON)
                print('in', self.in_time)
            elif self.state['state'] == 'wait_out_time':
                self.out_time = self.check_time(msg['text'])
                if self.in_time:
                    self.function_time()

            elif msg['text'] == 'Statistic':
                total_seconds = 0
                h_stat = 0
                m_stat = 0
                for day in db.get_all_days_by_chat_id(self.id):
                    total_seconds += day.delta
                    sec_stat = total_seconds
                    h_stat = str(sec_stat // 3600)
                    m_stat = (sec_stat // 60) % 60
                    if m_stat < 10:
                        m_stat = ('0' + str(m_stat))
                    else:
                        m_stat = str(m_stat)
                self.sender.sendMessage(u'В этом месяце вы отработали {}:{}'.format(h_stat, m_stat),
                                        reply_markup=DATE_CALENDARE)

            else:
                self.start_page()

    def function_time(self):
        if self.out_time > self.in_time:
            now_day = datetime.now()
            self.in_time = now_day.replace(hour=self.in_time.hour, minute=self.in_time.minute, second=0)
            self.out_time = now_day.replace(hour=self.out_time.hour, minute=self.out_time.minute, second=0)
            new_day = db.create_day(self.id, self.in_time, self.out_time)
            print('время в секундах:', str(db.get_delta(new_day), ))
            print('out', self.out_time)
            self.sender.sendMessage(u'Хорошего вечера', reply_markup=MENU_KEY, )
            self.check_time_work()
        else:
            self.sender.sendMessage(u'Время ухода привысило время прихода!', reply_markup=MENU_KEY)
            self.close()

    def check_work_day(self):
        self.week_day = datetime.weekday(datetime.now())
        if self.week_day <= 3:
            self.work_time = 9 * 3600
        elif self.week_day == 4:
            self.work_time = 6 * 3600
        else:
            self.sender.sendMessage(u'Сегодня выходной')
            self.close()

    def check_time(self, time):
        try:
            good_time = (datetime.strptime(time, TIME_FORMAT))
            return good_time
        except ValueError:
            self.sender.sendMessage(u'Неправильный формат времени!\nПопробуйте заново')
            self.close()

    def check_time_work(self):
        self.delta_time = self.out_time - self.in_time
        if (self.delta_time.total_seconds()) <= self.work_time:
            time_work_delta = self.work_time - (self.delta_time.total_seconds())
            self.math_time(time_work_delta, 1)
        else:
            time_work_delta = self.delta_time.total_seconds() - self.work_time
            self.math_time(time_work_delta, 0)

    def math_time(self, time_work, work_hard):
        sec_stat = int(time_work)
        h_stat = str(sec_stat // 3600)
        m_stat = (sec_stat // 60) % 60
        if m_stat < 10:
            m_stat = ('0' + str(m_stat))
        else:
            m_stat = str(m_stat)
        if work_hard:
            self.sender.sendMessage(u'У вас за сегодняшний день недоработка {}:{}'.format(h_stat, m_stat))
        else:
            self.sender.sendMessage(u'У вас за сегодняшний день переработка {}:{}'.format(h_stat, m_stat))
        self.close()

    def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')

        if query_data == "in_time":
            (msg['text']) = 'Start'
            in_key = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text=datetime.now().time().strftime("%H:%M"))],
            ], resize_keyboard=True)
            self.sender.sendMessage(u'Для быстрого заполнения нажмите на кнопку,'
                                    u' погрешность +- 1 минута', reply_markup=in_key, )

        elif query_data == 'out_time':
            out_key = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text=(datetime.now().time().strftime("%H:%M")))],
            ], resize_keyboard=True)
            self.sender.sendMessage(u'Для быстрого заполнения нажмите на кнопку,'
                                    u' погрешность +- 1 минута', reply_markup=out_key, )
        elif query_data == 'date':
            self.calendar()

        elif query_data == 'del':
            db.dell_all(self.id)

    def calendar(self):
        for day in db.get_all_days_by_chat_id(self.id):
            self.sender.sendMessage('Дата:{} Пришел: {} Ушел: {}'.format(datetime.date(day.in_time),
                                                                         day.in_time.time().strftime("%H:%M"),
                                                                         day.out_time.time().strftime("%H:%M")))

    def on__idle(self, event):
        pass
        '''
        if self.in_time:
            self.sender.sendMessage(u'Приятного рабочего дня')
            self.close()
        '''

    def on_close(self, ex):
        pass


TOKEN = '472100603:AAH9hnkq-ofauDbkYTdjbg1Fib7oiNX_32w'

bot = telepot.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(
        pave_event_space())(
        per_chat_id(types=['private']), create_open, TimeManager, timeout=10),
])
MessageLoop(bot).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)
