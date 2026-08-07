import xml.etree.ElementTree as ET
from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/feed.xml')
def get_clean_feed():
    url = "https://baza-bags.prom.ua/products_feed.xml?hash_tag=362a53a1f4f6537540a073604e3d9ce0&sales_notes=&product_ids=&label_ids=&exclude_fields=&html_description=1&yandex_cpa=&process_presence_sure=&languages=uk%2Cru&extra_fields=keywords&group_ids=" 
 
    try:
        res = requests.get(url, timeout=60)
        res.encoding = 'utf-8'
        
        root = ET.fromstring(res.content)

        offers_container = root.find('.//offers')
        if offers_container is None:
            offers_container = root

        offers = offers_container.findall('offer')

        for offer in offers:
            remove_item = False

            price_elem = offer.find('price')
            if price_elem is not None and price_elem.text:
                try:
                    price_val = float(price_elem.text.replace(',', '.'))
                    if price_val < 1500.0:
                        remove_item = True
                except ValueError:
                    pass

            if remove_item:
                offers_container.remove(offer)

        final_xml = ET.tostring(root, encoding='utf-8', method='xml', xml_declaration=True)
        
        return Response(
            final_xml, 
            mimetype='application/xml', 
            headers={"Content-Type": "application/xml; charset=utf-8"}
        )
        
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
