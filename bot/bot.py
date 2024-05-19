import logging
import re
import paramiko
import os
import subprocess
from dotenv import load_dotenv
import psycopg2 
from psycopg2 import Error
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

# Подключаем логирование
logging.basicConfig(
    filename='logfile.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('TOKEN')
HOST = os.getenv('RM_HOST')
PORT = os.getenv('RM_PORT')
USER = os.getenv('RM_USER')
PASSWD = os.getenv('RM_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_USER = os.getenv('DB_USER')
DB_PASSWD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

class DataBase:
    
    def __init__(self):
        #подключение к базе данных
        try:
            self.connection = psycopg2.connect(database = DB_DATABASE,
                                           user = DB_USER,
                                           password = DB_PASSWD,
                                           host = DB_HOST,
                                           port = DB_PORT)
            self.cursor = self.connection.cursor()
            logger.info("Соединение с PostgreSQL открыто")
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)

    def __del__(self):
        if self.connection is not None:
            self.cursor.close()
            self.connection.close()    
            logging.info("Соединение с PostgreSQL закрыто")

#добавление номера телефона в БД     
    def add_phones(self, data):
        with self.connection:
            try:
                lst =[]
                for l in data:
                    lst.append(tuple([l]))
                query = "INSERT INTO phones (number) values (%s)"            
                self.cursor.executemany(query, lst)
                self.connection.commit()
                logger.info("Номера успешно добавлены")
                return True
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
                return False
 
#запрос номеров из БД         
    def check_phones(self):
        with self.connection:
            try:
                self.cursor.execute("SELECT * FROM phones")
                self.connection.commit()
                logger.info("Номера успешно получены")
                return self.cursor.fetchall()
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
      
#добавление email адресов в БД
    def add_emails(self, data):
        with self.connection:
            try:
                lst =[]
                for l in data:
                    lst.append(tuple([l]))
                query = "INSERT INTO emails (address) values (%s)"
                self.cursor.executemany(query, lst)
                self.connection.commit()
                logger.info("Адреса успешно добавлены")
                return True
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
                return False
 
#запрос email адресов  из БД      
    def check_emails(self):
        with self.connection:
            try:
                self.cursor.execute("SELECT * FROM emails")
                self.connection.commit()
                logger.info("Адреса успешно получены")
                return self.cursor.fetchall()
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
            

#Обработка команды /start
def start(update: Update, context):
    user = update.effective_user
    logger.info("Пользователь %s начал разговор.", user.full_name)
    update.message.reply_text(f'Привет {user.full_name}!')

#Обработка команды /help    
def helpCommand(update: Update, context):
    user = update.effective_user
    logger.info("Пользователь %s вызвал команду help.", user.full_name)
    update.message.reply_text('Help!')

#echo ответы на сообщения
def echo(update: Update, context):
    logger.info("Пользователь %s отправил: %s", update.effective_user.full_name, update.message.text)
    update.message.reply_text(update.message.text)

#поиск номеров телефонов в тексте
def findPhoneNumbers (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов

    phoneNumRegex = re.compile(r"\b[8|\+7][\- ]?\(?\d{3}\)?[\- ]?\d{3}[\- ]?\d{2}[\- ]?\d{2}\b")

    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END
    
    phoneNumberList=list(set(phoneNumberList))
    context.user_data["phoneNumbers"] = phoneNumberList
    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n' # Записываем очередной номер
        
    update.message.reply_text(phoneNumbers + 'Добавить найденные номера? [Да/Нет]') # Отправляем сообщение пользователю
    
    return 'savePhoneReply'

def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    logger.info("Пользователь %s запустил команду поиска номеров телефонов.", update.effective_user.full_name)
    return 'findPhoneNumbers'

#поиск email адресов
def findEmail (update: Update, context):
    user_input = update.message.text

    emailRegex = re.compile(r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[.a-zA-Z0-9-]+")

    EmailList = emailRegex.findall(user_input) 

    if not EmailList: 
        update.message.reply_text('Email-адреса не найдены')
        return ConversationHandler.END
    
    EmailList=list(set(EmailList))
    context.user_data["emails"] = EmailList
    emails = '' 
    for i in range(len(EmailList)):
        emails += f'{i+1}. {EmailList[i]}\n' 
        
    update.message.reply_text(emails + 'Добавить найденные email-адреса? [Да/Нет]') 
    return  'saveEmailReply' 

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска email-адреса: ')
    logger.info("Пользователь %s запустил команду поиска email адресов.", update.effective_user.full_name)
    return 'findEmail'

#проверка пароля на сложность
def verifypassword (update: Update, context):
    user_input = update.message.text

    passwdRegex = re.compile(r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*()]).{8,}$")

    if not re.fullmatch(passwdRegex, user_input):
        update.message.reply_text('Пароль простой')
        return ConversationHandler.END
    
    else:
        update.message.reply_text('Пароль сложный') 
        return ConversationHandler.END 

def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль: ')
    logger.info("Пользователь %s запустил команду проверки пароля на сложность.", update.effective_user.full_name)
    return 'verifypassword'

#выполнение команд на удаленном хосте с помощью ssh
def sendSSHCommand(command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #Устанавливается соединение с удаленным сервером
        client.connect(hostname=HOST, username=USER, password=PASSWD, port=PORT)
        #Выполнение команды
        stdin, stdout, stderr = client.exec_command(command)
        data = stdout.read() + stderr.read()
        client.close()
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        return data
    except Exception as e:
        logger.error("Ошибка при подключении по ssh: %s", str(e))

#получение информации о релизе
def get_releaseCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду get_release.", update.effective_user.full_name)
    data=sendSSHCommand('lsb_release -d')
    update.message.reply_text(data)

#получение информации об архитектуры процессора, имени хоста системы и версии ядра
def get_unameCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду uname.", update.effective_user.full_name)
    data=sendSSHCommand('uname -a')
    update.message.reply_text(data)

#получение информации о времени работы
def get_uptimeCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду uptime.", update.effective_user.full_name)
    data=sendSSHCommand('uptime')
    update.message.reply_text(data)

#получение информации о состоянии файловой системы
def get_dfCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду df.", update.effective_user.full_name)
    data=sendSSHCommand('df -h')
    update.message.reply_text(data)

#получение информации о состоянии оперативной памяти
def get_freeCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду free.", update.effective_user.full_name)
    data=sendSSHCommand('free -h')
    update.message.reply_text(data)

#получение информации о производительности системы
def get_mpstatCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду mpstat.", update.effective_user.full_name)
    data=sendSSHCommand('mpstat')
    update.message.reply_text(data)

#получение информации о работающих в данной системе пользователях
def get_wCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду w.", update.effective_user.full_name)
    data=sendSSHCommand('w')
    update.message.reply_text(data)

#получение информации о последних 10 входов в систему
def get_authsCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду get_auths.", update.effective_user.full_name)
    data=sendSSHCommand('last -10')
    update.message.reply_text(data)

#получение информации о последних 5 критических событиях
def get_criticalCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду get_critical.", update.effective_user.full_name)
    data=sendSSHCommand('journalctl -p 2 -n 5')
    update.message.reply_text(data)

#получение информации о запущенных процессах
def get_psCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду get_ps.", update.effective_user.full_name)
    data=sendSSHCommand('ps -A | head -n 10')
    update.message.reply_text(data)

#получение информации об используемых портах
def get_ssCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду  get_ss.", update.effective_user.full_name)
    data=sendSSHCommand('ss -lntu')
    update.message.reply_text(data)

#вывод информации об установленных пакетах
def check_apt_list (update: Update, context):
    user_input = update.message.text

    if user_input=='ALL': #вывод инф-ции о всех пакетах
        logger.info("Пользователь %s запустил команду get_apt_list для всех пакетов.", update.effective_user.full_name)
        data=sendSSHCommand('apt list --installed | head -n 10')
        update.message.reply_text(data)
        return ConversationHandler.END 
    
    else: #вывод информации об определенном пакете
        logger.info("Пользователь %s запустил команду get_apt_list для пакета %s.", update.effective_user.full_name, user_input)
        data=sendSSHCommand(f'apt list --installed | grep "{user_input}" | head -n 10')
        update.message.reply_text(data) 
        return ConversationHandler.END 

#получение информации об установленных пакетах  
def get_apt_listCommand(update: Update, context):
    update.message.reply_text('-- Если хотите получить информацию о всех установленных пакетах, введите ALL;\n' 
                              '-- Если хотите получить информацию о конкретном установленном пакете, введите название пакета;')
    return 'check_apt_list'

#получение информации о запущенных сервисах
def get_servicesCommand(update: Update, context):
    logger.info("Пользователь %s запустил команду  get_services.", update.effective_user.full_name)
    data=sendSSHCommand('systemctl --type=service --state=running | head -n 10')
    update.message.reply_text(data)

#получение email адресов из БД  
def get_emailsCommand(update: Update, context):
    db = DataBase()
    logger.info("Пользователь %s запросил адреса из БД.", update.effective_user.full_name)
    data = db.check_emails()
    msg = ''
    for line in data:
       msg += f'{line[1]}\n'
    update.message.reply_text(msg)

#получение номеров из БД
def get_numbersCommand(update: Update, context):
    db = DataBase()
    logger.info("Пользователь %s запросил номера из БД.", update.effective_user.full_name)
    data = db.check_phones()
    msg = ''
    for line in data:
       msg += f'{line[1]}\n'
    update.message.reply_text(msg)

#получение логов о репликации
def get_logsCommand(update: Update, context):
    logger.info("Пользователь %s запросил логи о репликации.", update.effective_user.full_name)
    command = "cat /var/log/postgresql/postgresql.log | grep 'repl' | tail -n 40"
    res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0 or res.stderr.decode() != "":
        logger.error("Ошибка при выводе логов репликации: %s", res.stderr.decode())
    else:
        update.message.reply_text(res.stdout.decode().strip('\n'))
    

#Обработка ответа пользователя(сохранение номеров телефонов)
def savePhoneReply (update: Update, context):
    db = DataBase()
    user_input = update.message.text
    regYes = re.compile(r'^Да$', re. I)
    regNo = re.compile(r'^Нет$', re. I)
    if re.fullmatch(regNo, user_input):# Если пользователь ответил "Нет"
        return ConversationHandler.END
    elif re.fullmatch(regYes, user_input): # Если пользователь ответил "Да"
        #Добавление номеров в БД
        phoneNumbers = context.user_data["phoneNumbers"]
        if (db.add_phones(phoneNumbers)):
            update.message.reply_text("Номера успешно добавлены!")
            return ConversationHandler.END
        else:
            update.message.reply_text("Произошла ошибка при добавлении")
            return ConversationHandler.END
    else:
        update.message.reply_text("Некорректный ввод")
        return ConversationHandler.END

#Обработка ответа пользователя(сохранение email адресов)
def saveEmailReply (update: Update, context):
    db = DataBase()
    user_input = update.message.text
    regYes = re.compile(r'^Да$', re. I)
    regNo = re.compile(r'^Нет$', re. I)
    if re.fullmatch(regNo, user_input): # Если пользователь ответил "Нет"
        return ConversationHandler.END
    elif re.fullmatch(regYes, user_input):  # Если пользователь ответил "Да"
        #Добавление адресов в БД
        emails = context.user_data["emails"]
        if (db.add_emails(emails)):
            update.message.reply_text("Адреса успешно добавлены!")
            return ConversationHandler.END
        else:
            update.message.reply_text("Произошла ошибка при добавлении")
            return ConversationHandler.END
    else:
        update.message.reply_text("Некорректный ввод")
        return ConversationHandler.END

def main():
	
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher
 
	# Регистрируем обработчики команд 
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'savePhoneReply': [MessageHandler(Filters.text & ~Filters.command, savePhoneReply,)],
        },
        fallbacks=[]
    ))
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'findEmail': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'saveEmailReply': [MessageHandler(Filters.text & ~Filters.command, saveEmailReply,)],
        },
        fallbacks=[]
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verifypassword': [MessageHandler(Filters.text & ~Filters.command, verifypassword)],
        },
        fallbacks=[]
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', get_apt_listCommand)],
        states={
            'check_apt_list': [MessageHandler(Filters.text & ~Filters.command, check_apt_list)],
        },
        fallbacks=[]
    ))

    dp.add_handler(CommandHandler("get_release", get_releaseCommand))
    dp.add_handler(CommandHandler("get_uname", get_unameCommand))
    dp.add_handler(CommandHandler("get_uptime", get_uptimeCommand))
    dp.add_handler(CommandHandler("get_df", get_dfCommand))
    dp.add_handler(CommandHandler("get_free", get_freeCommand))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstatCommand))
    dp.add_handler(CommandHandler("get_w", get_wCommand))
    dp.add_handler(CommandHandler("get_auths", get_authsCommand))
    dp.add_handler(CommandHandler("get_critical", get_criticalCommand))
    dp.add_handler(CommandHandler("get_ps", get_psCommand))
    dp.add_handler(CommandHandler("get_ss", get_ssCommand))
    dp.add_handler(CommandHandler("get_services", get_servicesCommand))
    
    dp.add_handler(CommandHandler("get_repl_logs", get_logsCommand))
    dp.add_handler(CommandHandler("get_emails", get_emailsCommand))
    dp.add_handler(CommandHandler("get_phone_numbers", get_numbersCommand))

		# Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
		
		# Запускаем бота
    updater.start_polling()

		# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
