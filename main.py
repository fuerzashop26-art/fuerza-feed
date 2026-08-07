import xml.etree.ElementTree as ET
from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/feed.xml')
def get_clean_feed():
    # ПОДСТАВЬТЕ СЮДА ВАШУ РЕАЛЬНУЮ ССЫЛКУ НА ОРИГИНАЛЬНЫЙ ФИД ИЗ КАБИНЕТА PROM
    url = "https://baza-bags.prom.ua/products_feed.xml?hash_tag=362a53a1f4f6537540a073604e3d9ce0&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=1&yandex_cpa=&process_presence_sure=&languages=uk%2Cru&extra_fields=keywords&group_ids=" 
    
    try:
        res = requests.get(url, timeout=60)
        res.encoding = 'utf-8'
        
        # Парсим XML напрямую как дерево элементов
        root = ET.fromstring(res.content)

        trash = {'коробка', 'коробки', 'пакет', 'пакети', 'упаковочн', 'упаковк', 'коробочк', 'палантин', 'шарф', 'платок', 'хустка', 'шарфи', 'палантини', 'кошелек', 'кошелки', 'портмоне', 'гаманець', 'гаманці', 'кошелёк', 'кошельки', 'ремень', 'ремні', 'пояс', 'пояси'}
        excs = {'сумка', 'сумочка', 'рюкзак', 'барсетка', 'мессенджер', 'бананка', 'crossbody', 'тоут', 'клатч'}

        # Находим блок с товарами (в Prom/YML это обычно <offers>)
        offers_container = root.find('.//offers')
        if offers_container is None:
            # Если структура нестандартная, ищем корневой тег товаров
            offers_container = root

        # Собираем список всех товаров <offer>
        offers = offers_container.findall('offer')

        for offer in offers:
            remove_item = False

            # 1. Проверка цены (удаляем всё, что меньше 1500)
            price_elem = offer.find('price')
            if price_elem is not None and price_elem.text:
                try:
                    price_val = float(price_elem.text.replace(',', '.'))
                    if price_val < 1500.0:
                        remove_item = True
                except ValueError:
                    pass

            # 2. Проверка стоп-слов в названии
            if not remove_item:
                name_elem = offer.find('name')
                if name_elem is not None and name_elem.text:
                    name = name_elem.text.lower()
                    if any(word in name for word in trash):
                        # Исключение: если это сумка с ремнем — оставляем
                        if any(exc in name for exc in excs) and ('ремен' in name or 'пояс' in name):
                            remove_item = False
                        else:
                            remove_item = True

            # Если товар не подошел по условиям — полностью удаляем его из структуры
            if remove_item:
                offers_container.remove(offer)

        # Превращаем очищенное дерево обратно в XML-строку
        final_xml = ET.tostring(root, encoding='utf-8', method='xml')
        
        return Response(
            final_xml, 
            mimetype='application/xml', 
            headers={"Content-Type": "application/xml; charset=utf-8"}
        )
        
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
