from flask import Flask, request, redirect,jsonify

from datetime import datetime,timedelta
import json
import random
import string
import socket
from collections import defaultdict

class HashTable:  #реализация простой хэш-таблицы для хранения коротких ссылок и их оригинальный URL
    def __init__(self, size):
        self.size = size
        self.table = [None] * size

    def hash_function(self, key):
        return hash(key) % self.size

    def insert(self, key, value):
        index = self.hash_function(key)
        if self.table[index] is None:
            self.table[index] = [(key, value)]
        else:
            for i, (existing_key, _) in enumerate(self.table[index]):
                if existing_key == key:
                    # Если ключ уже существует, обновляем значение
                    self.table[index][i] = (key, value)
                    break
            else:
                # Если ключ не найден, добавляем новую пару ключ-значение
                self.table[index].append((key, value))

    def search(self, key):
        index = self.hash_function(key)
        if self.table[index] is not None:
            for existing_key, value in self.table[index]:
                if existing_key == key:
                    return value
        # Если ключ не найден
        return None

    def delete(self, key):
        index = self.hash_function(key)
        if self.table[index] is not None:
            for i, (existing_key, _) in enumerate(self.table[index]):
                if existing_key == key:
                    del self.table[index][i]
                    break


class JSONCreator: #Работа с json-файлами, в котором хранится статистика
    def __init__(self, filename):
        self.filename = filename
        self.data = self.load_data()

    #Метод load_data загружает данные из файла, обрабатывая возможные ошибки
    def load_data(self):
        try:
            with open(self.filename, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading data from {self.filename}: {e}")
            return []

    #Метод add_data добавляет новую запись в данные 
    def add_data(self, url, ip, time):
        if isinstance(time, datetime):
            time = time.strftime('%Y-%m-%d %H:%M:%S')
        data_entry = {"URL": url, "IP": ip, "Time": time}
        self.data.append(data_entry)

    #Метод create_json записывает обновлённые данные обратно в файл
    def create_json(self):
        with open(self.filename, 'w') as file:
            json.dump(self.data, file)


#Получение IP-адреса хоста
def getHostIP():
    return socket.gethostbyname(socket.gethostname())


app = Flask(__name__)
server_address = ('{getHostIP()}', 3333)
short_link_table = HashTable(size=512)  # Adjust the size based on your requirements

@app.route('/', methods=['GET', 'POST'])
def home():
    generated_link = None
    if request.method == 'POST':
        original_link = request.form['user_input']

        short_link = generate_short_link()

        # Save the short link in the hash table
        short_link_table.insert(short_link, original_link)

        generated_link = f"http://{getHostIP()}:3333/{short_link}"

    return (generated_link)


@app.route('/statistic')
def statistic():
    try:
        with open('statistic.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data from statistic.json: {e}")
        data = []

    return jsonify(data)





def find_pid_for_url(url, reports):
    for record in reversed(list(reports.values())):
        if record["URL"] == url:
            return record["Id"]
    return "null"

def generate_json_report(filename, json_file):
    with open(filename, 'r') as file:
        data = json.load(file)

    time_format = "%Y-%m-%d %H:%M:%S"
    interval = timedelta(seconds=60)

    reports = {}
    id = 1

    for entry in data:
        url = entry["URL"]
        time = datetime.strptime(entry["Time"], time_format)
        output_data = entry.get("IP", "null")
        if url in reports:
            reports_time = datetime.strptime(reports[url]["Time"], time_format)  # Convert to datetime
            if (time - reports_time) < interval:
                reports[url]["Count"] += 1
            else:
                record = {
                    "Id": id,
                    "Pid": find_pid_for_url(url, reports),
                    "URL": url,
                    "SourceIP": output_data,
                    "Time": time.strftime(time_format),
                    "Count": 1
                }
                id += 1
                reports[url] = record
        else:
            record = {
                "Id": id,
                "Pid": find_pid_for_url(url, reports),
                "URL": url,
                "SourceIP": output_data,
                "Time": time.strftime(time_format),
                "Count": 1
            }
            id += 1
            reports[url] = record

        with open(json_file, 'w') as f:
            for report in reports.values():
                for key, value in report.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")

@app.route('/report') #Извлечение данных из файла, генерирует отчёт и возвращает его в виде json-строки
def report():
    filename = "statistic.json"
    json_file = "report.json"
    generate_json_report(filename, json_file)  # Uncomment this line to generate the report

    with open(json_file, 'r') as file:
        data = file.read()
        #print(data)  # Print the content of the file to the console

    # Return the contents of the "report.json" file as a file response
    return jsonify(data)




@app.route('/detail') #Извлекает данные из файла статистики, создаёт детализированный отчёт и сохраняет его в файл
def detail():
    def getHostIP(): #Получение IP-адреса хоста
        return socket.gethostbyname(socket.gethostname())


    url = f"http://{getHostIP()}:3333/getreport"
            

    with open('statistic.json', 'r') as f:
            data = json.load(f)

        # Create report
    report = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for entry in data:
        url = entry['URL']
        source_ip = entry['IP']
        time = datetime.strptime(entry["Time"], "%Y-%m-%d %H:%M:%S")
        minute_interval = time.minute
        time_interval = f"{time.hour:02d}:{minute_interval:02d}-{time.hour:02d}:{(minute_interval+1):02d}"
        report[source_ip][time_interval][url] += 1

    # Format report
    formatted_report = {}
    for source_ip, time_data in report.items():
        source_ip_data = {}
        for time_interval, url_data in time_data.items():
            interval_data = {}
            interval_data["Total"] = sum(url_data.values())
            interval_data["URLS"] = {url: f"({count})" for url, count in url_data.items()}
            source_ip_data[time_interval] = interval_data
        formatted_report[source_ip] = source_ip_data
        
    # Write report to a JSON file
    with open('Detail.json', 'w') as f:
        json.dump(formatted_report, f, indent=4)
    
    json_file="Detail.json"

    with open(json_file, 'r') as file:
        data = file.read()
        #print(data)  # Print the content of the file to the console

    # Return the contents of the "report.json" file as a file response
    return jsonify(data)










@app.route('/<short_link>') #Обрабатывает запросы для перенаправления сокращённых URL на оригинальные.   Добавляет запись о посещении в файл статистики 
def redirect_to_original(short_link):
    # Retrieve the original link from the hash table
    original_link = short_link_table.search(short_link)
    
    if original_link:
        json_creator = JSONCreator('statistic.json')
        json_creator.add_data(original_link + "(" + short_link + ")", request.environ['REMOTE_ADDR'], datetime.now().replace(microsecond=0))
        # Move the create_json outside the if-else block
    else:
        # You might want to log an error or handle it appropriately
        return ('error')

    # Move the create_json outside the if-else block
    json_creator.create_json()
    
    return redirect(original_link)



def generate_short_link(): #Генерирует случайную короткую ссылку заданной длины
    charset = string.ascii_letters + string.digits
    key_length = random.randint(1, 6)

    short_link = ''.join(random.choice(charset) for _ in range(key_length))
    return short_link



if __name__ == '__main__':
    app.run(host=f'{getHostIP()}', port=3333, debug=False)


