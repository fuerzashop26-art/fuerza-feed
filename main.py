import xml.etree.ElementTree as ET
from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/feed.xml')
def get_clean_feed():
    # Оригинальная ссылка на ваш фид поставщика Baza-Bags
    url = "https://baza-bags.prom.ua/products_feed.xml?hash_tag=362a53a1f4f6537540a073604e3d9ce0&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=1&yandex_cpa=&process_presence_sure=&languages=uk%2Cru&extra_fields=keywords&group_ids=" 
    
    try:
        # Скачиваем фид напрямую из сети
        res = requests.get(url, timeout=60)
        res.encoding = 'utf-8'
        
        # Парсим XML напрямую как дерево элементов
        root = ET.fromstring(res.content)

        # Находим блок с товарами (<offers>)
        offers_container = root.find('.//offers')
        if offers_container is None:
            offers_container = root

        # Собираем список всех товаров <offer>
        offers = offers_container.findall('offer')

        for offer in offers:
            remove_item = False

            # ГЛАВНОЕ УСЛОВИЕ: Проверка цены (удаляем всё, что строго меньше 1500 грн)
            price_elem = offer.find('price')
            if price_elem is not None and price_elem.text:
                try:
                    price_val = float(price_elem.text.replace(',', '.'))
                    if price_val < 1500.0:
                        remove_item = True
                except ValueError:
                    pass  # Если цена повреждена, не трогаем, чтобы не сломать импорт
            else:
                # Если у товара вообще нет цены — убираем его от греха подальше
                remove_item = True

            # Если товар дешевле 1500 грн — полностью вырезаем всю карточку товара
            if remove_item:
                offers_container.remove(offer)

        # Превращаем очищенное дерево обратно в XML-строку с XML-декларацией
        final_xml = ET.tostring(root, encoding='utf-8', method='xml', xml_declaration=True)
        
        return Response(
            final_xml, 
            mimetype='application/xml', 
            headers={"Content-Type": "application/xml; charset=utf-8"}
        )
        
    except Exception as e:
        # Безопасный возврат ошибки, если сервер поставщика недоступен
        return Response(
            f"<error>Не удалось обработать фид: {str(e)}</error>",
            status=500,
            mimetype='application/xml'
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
