from flask import Flask, Response
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)

@app.route('/feed.xml')
def get_clean_feed():
    # Прямая ссылка на ваш оригинальный фид поставщика
    url = "https://prom.ua"
    
    try:
        # Скачиваем свежие данные от поставщика
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        
        # Парсим XML структуру
        root = ET.fromstring(response.text)

        # Жесткий список мусорных слов для удаления
        trash_words = [
            'коробка', 'коробки', 'пакет', 'пакети', 'упаковочн', 'упаковк', 'коробочк',
            'палантин', 'шарф', 'платок', 'хустка', 'шарфи', 'палантини',
            'кошелек', 'кошелки', 'портмоне', 'гаманець', 'гаманці', 'кошелёк', 'кошельки',
            'ремень', 'ремні', 'пояс', 'пояси'
        ]
        
        # Исключения: если в названии есть эти слова, то по ключевым словам товар НЕ удаляем
        exceptions = ['сумка', 'сумочка', 'рюкзак', 'барсетка', 'мессенджер', 'бананка', 'crossbody', 'тоут', 'клатч']

        offers_parent = root.find('.//offers')
        categories_parent = root.find('.//categories')
        removed_categories = set()

        if offers_parent is not None:
            for offer in list(offers_parent):
                name_node = offer.find('name')
                price_node = offer.find('price')
                category_id = offer.find('categoryId')
                
                is_removed = False
                
                # 1. Фильтр цены: удаляем всё, что дешевле 1500 грн
                if price_node is not None and price_node.text:
                    try:
                        if float(price_node.text) < 1500.0:
                            offers_parent.remove(offer)
                            is_removed = True
                            if category_id is not None:
                                removed_categories.add(category_id.text)
                    except ValueError:
                        pass
                
                # 2. Фильтр мусора: удаляем кошельки, ремни, коробки
                if not is_removed and name_node is not None and name_node.text:
                    name_text = name_node.text.lower()
                    if any(word in name_text for word in trash_words):
                        # Если это сумка с ремнем в комплекте — пропускаем ее (оставляем)
                        if any(exc in name_text for exc in exceptions) and ('ремень' in name_text or 'ремені' in name_text or 'пояс' in name_text):
                            continue
                        # Во всех остальных случаях (отдельный ремень, чистый кошелек) — удаляем
                        offers_parent.remove(offer)
                        if category_id is not None:
                            removed_categories.add(category_id.text)

        # Чистим дерево категорий от пустых разделов
        if categories_parent is not None:
            for category in list(categories_parent):
                cat_text = category.text.lower() if category.text else ""
                cat_id = category.get('id')
                if any(word in cat_text for word in trash_words) or cat_id in removed_categories:
                    categories_parent.remove(category)

        # Собираем чистый XML обратно в строку
        clean_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        
        # Отдаем его Прому с четким указанием, что это XML-файл
        return Response(clean_xml, mimetype='application/xml', headers={"Content-Type": "application/xml; charset=utf-8"})
        
    except Exception as e:
        return Response(f"Ошибка сервера фильтрации: {str(e)}", status=500, mimetype='text/plain')

if __name__ == '__main__':
    # Порт для запуска на сервере Render
    app.run(host='0.0.0.0', port=10000)
