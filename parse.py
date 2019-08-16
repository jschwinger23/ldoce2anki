import os
import yaml
import glob
import pprint
from contextlib import suppress

from jinja2 import Template
from bs4 import BeautifulStoneSoup


def parse(word: str, soup: BeautifulStoneSoup) -> dict:
    entries = []
    word = {'word': word, 'entries': entries}
    for entry in soup.find_all(class_='ldoceEntry Entry'):
        entries.append({})
        last_entry = entries[-1]
        with suppress(AttributeError):
            american_pron = entry.find(class_='AMEVARPRON')
            american = f'/{american_pron.text.strip()}/' if american_pron else ''
            last_entry['pron'] = '/{english}/ {american}'.format(
                english=entry.find(class_='PRON').text.strip(),
                american=american,
            ).rstrip()
        try:
            last_entry['pos'] = entry.find(class_='POS').text.strip()
        except AttributeError:
            entries.pop()
            continue

        senses = last_entry['senses'] = []
        for sense in entry.find_all(class_='Sense'):
            senses.append({})
            last_sense = senses[-1]
            try:
                last_sense['definition'] = sense.find(class_='DEF').text.strip()
            except AttributeError:
                try:
                    last_sense['definition'] = sense.find(class_='REFHWD').text.strip()
                except AttributeError:
                    senses.pop()
                    continue

            find_rel = sense.find(class_='RELATEDWD')
            if find_rel:
                last_sense['rel'] = find_rel.text.strip()[2:]

            find_syn = sense.find(class_='SYN')
            if find_syn:
                last_sense['syn'] = find_syn.text.strip()[4:]

            find_opp = sense.find(class_='OPP')
            if find_opp:
                last_sense['opp'] = find_opp.text.strip()[4:]

            last_sense['examples'] = [
                e.text.strip() for e in sense.find_all(class_='EXAMPLE')
            ]
    return word

def yaml_converter(word: dict) -> str:
    return yaml.dump(word, allow_unicode=True)


class AnkiHtmlConverter:
    def __init__(self):
        self._tmpl = '''
            <div>
                <div>
                    <div>
                        <div style="" text-align: center; "">{{ word.word }}</div>
                    </div>
                {% for entry in word.entries %}
                    <hr />
                    <div style="" text-align: center; ""><font color="" #108040 "">{{ entry.pos }}</font>&nbsp;{{ entry.pron }}</div>
                {% for sense in entry.senses %}
                    <div style="" text-align: left; "">{{ loop.index }}. {{ sense.definition }}
                    {% if sense.syn %}
                        = <font color="" #0000ff ""><b>{{ sense.syn }}</b></font>
                    {% endif %}
                    {% if sense.rel %}
                        → <font color="" #0000ff ""><b>{{ sense.rel }}</b></font>
                    {% endif %}
                    {% if sense.opp %}
                        ≠ <font color="" #0000ff ""><b>{{ sense.opp }}</b></font>
                    {% endif %}
                    </div>

                  {% if sense.examples|length > 0 %}
                    <div>
                        <ul style="" list-style-type: disc; "">
                    {% for example in sense.examples %}
                            <li style="" text-align: left; ""><font color="" #999999 "">{{ example }}</font></li>
                    {% endfor %}
                        </ul>
                    </div>
                  {% else %}
                    <div style="" text-align: left; "">&nbsp;</div>
                  {% endif %}
                {% endfor %}
                {% endfor %}
                </div>
            </div>
        '''

    def __call__(self, word: dict) -> str:
        html = Template(self._tmpl).render(word=word)
        return html.replace('\n', '')


if __name__ == '__main__':
    converter = AnkiHtmlConverter()
    for filename in glob.glob('htmls/*.html'):
        soup = BeautifulStoneSoup(open(filename))
        if not soup.find(class_='ldoceEntry Entry'):
            continue
        word = os.path.basename(filename).rsplit('.', 1)[0]
        print(word, f'"{converter(parse(word, soup))}"', sep='\t')
