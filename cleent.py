#Способ использования HTTP-запроса для взаимодействия с сервером, который предоставляет сервис сокращения URL
import requests #для взаимодействия с веб-сервером, который обрабатывает сокращённые URL  (способ отправки HTTP-запросов)

def get_short_link(url):
    response = requests.post('http://192.168.1.143:3333/', data={'user_input': url})
    if response.status_code == 200:
        return response.text #возврат текст ответа (короткая ссылка)
    else:
        return 'Error: ' + response.text #возврат сообщения об ошибке с текстом ответа

# Пример использования
original_url = str(input("Enter url or command: ")) #ввод пользователя в виде URL или команды
short_url = get_short_link(original_url) #вызов функции для отправки запроса на сервер сокращения URL
print(short_url)