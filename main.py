import re
from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/feed.xml')
def get_clean_feed():
    url = "https://prom.ua"
    try:
        res = requests.get(url, timeout=30)
        res.encoding = 'utf-8'
        text = res.text

        trash = ['коробка', 'коробки', 'пакет', 'пакети', 'упаковочн', 'упаковк', 'коробочк', 'палантин', 'шарф', 'платок', 'хустка', 'шарфи', 'палантини', 'кошелек', 'кошелки', 'портмоне', 'гаманець', 'гаманці', 'кошелёк', 'кошельки', 'ремень', 'ремні', 'пояс', 'пояси']
        excs = ['сумка', 'сумочка', 'рюкзак', 'барсетка', 'мессенджер', 'бананка', 'crossbody', 'тоут', 'клатч']

        parts = text.split('<offer ')
        clean_parts = [parts[0]]

        for part in parts[1:]:
            end_idx = part.find('</offer>')
            if end_idx == -1:
                clean_parts.append('<offer ' + part)
                continue

            offer_body = part[:end_idx]
            rest = part[end_idx:]

            price_match = re.search(r'<price>([^<]+)</price>', offer_body)
            if price_match:
                try:
                    if float(price_match.group(1)) < 1500.0:
                        if len(rest) > 8: clean_parts.append(rest[8:])
                        continue
                except:
                    pass

            name_match = re.search(r'<name>([^<]+)</name>', offer_body)
            if name_match:
                name = name_match.group(1).lower()
                if any(word in name for word in trash):
                    if any(exc in name for exc in excs) and ('ремен' in name or 'пояс' in name):
                        pass
                    else:
                        if len(rest) > 8: clean_parts.append(rest[8:])
                        continue

            clean_parts.append('<offer ' + part)

        final_xml = ''.join(clean_parts)
        return Response(final_xml, mimetype='application/xml', headers={"Content-Type": "application/xml; charset=utf-8"})
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
