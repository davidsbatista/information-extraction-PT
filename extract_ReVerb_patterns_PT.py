#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import codecs
import nltk
import os

from BeautifulSoup import BeautifulSoup
from polyglot.text import Text

__author__ = "David S. Batista"
__email__ = "dsbatista@gmail.com"


ignore_entities = [".", ". .", ". . .",  "! . . .", "»", "?", "E", "-",
                   ". . »", ". . . »", ". . . )", "sr"]

categories = ['Nacional', 'Mundo', 'Economia', 'Sociedade', 'Cultura']

DEBUG = 0
SDT_OUTPUT = 0


class Triple(object):

    def __init__(self, e1, e1_type, rel, e2, e2_type):
        self.e1 = e1
        self.e1_type = e1_type
        self.rel = rel
        self.e2 = e2
        self.e2_type = e2_type

    def __str__(self):
        out = self.e1+'\t'+self.e1_type+'\t'+self.rel+'\t'+self.e2+'\t'+self.e2_type
        return out.encode("utf8")


def extract_triples(reverb_pattern, text):

    triples = []

    for s in text.sentences:
        try:
            if len(s.entities) < 2:
                continue
        except ValueError:
            continue

        if DEBUG == 1:
            print s
            print
            print s.entities
            print

        for i in range(len(s.entities)):
            if i + 1 == len(s.entities):
                break

            e1 = s.entities[i]
            e2 = s.entities[i + 1]
            entity1 = " ".join(e1)
            entity2 = " ".join(e2)

            if entity1.encode("utf8") in ignore_entities \
                    or entity2.encode("utf8") in ignore_entities:
                continue

            if entity1.islower() or entity1.islower():
                continue

            context = s.words[e1.end:e2.start]
            if len(context) > 8 or len(context) == 0:
                continue

            if DEBUG == 1:
                print entity1, '\t', entity2
                print s.pos_tags[e1.end:e2.start]
                print
            rel = reverb_pattern.parse(s.pos_tags[e1.end:e2.start])
            for x in rel:
                if isinstance(x, nltk.Tree) and x.label() == 'REL_PHRASE':
                    rel_phrase = " ".join([t[0] for t in x.leaves()])
                    triple = Triple(entity1, e1.tag, rel_phrase, entity2, e2.tag)
                    triples.append(triple)

    if SDT_OUTPUT == 1:
        for t in triples:
            print t

    return triples


def process_chave(reverb_pattern):

    input_base_path = "/Users/dbatista/Downloads/CHAVEPublico/"
    triples = []

    for root, dirs, files in os.walk(input_base_path):
        for news_file in files:
            file_path = os.path.join(root, news_file)
            print news_file
            with codecs.open(file_path, "r", encoding='latin_1') as input_file:

                # open SGML file and get text sections
                sgml_file = input_file.read().encode("utf8")
                soup = BeautifulSoup(sgml_file)

                # get article category
                for doc in soup.findAll("doc"):
                    children = doc.findChildren()
                    if len(children) == 4:
                        continue
                    category = children[3]

                    # filter by category and extract triples
                    if category.getText() in categories:
                        article_text = children[-1].getText()
                        text = Text(article_text, hint_language_code='pt')
                        extracted_triples = extract_triples(reverb_pattern, text)
                        triples.extend(extracted_triples)

    with open('triples.csv', 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter='\t', quotechar='"')
        for t in triples:
            writer.writerow([t.e1.encode("utf8"), t.e1_type,
                             t.rel.encode("utf8"),
                             t.e2.encode("utf8"), t.e2_type])

    print len(triples), "extracted"


def test_patterns(reverb_pattern):

    sentences = [

        "-- Vai amanhã à missa no Sagrado Coração, em memória do ministro Guy Malary, "
        "assassinado há um ano pela Junta?",

        "«O tribunal (5º Juízo Cível da Comarca de Lisboa) confirmou a suspensão de Paco "
        "Bandeira e Fernando Luso Soares da Sociedade Portuguesa de Autores, recusando "
        "a providência cautelar que aqueles haviam requerido para que fosse suspensa "
        "a sua expulsão», divulgou ontem em comunicado a Sociedade Portuguesa de "
        "Autores (SPA).",

        'O director-geral do FMI, Michel Camdessus, alertou na semana passada Moscovo '
        'para as dificuldades que se colocarão para a concessão de novos empréstimos.',

        "Ontem, o assessor de Imprensa da Casa Branca, George Stephanopoulos, "
        "em declarações à cadeia de televisão ABC, classificou de «oportunismo político» "
        "o pedido dos republicanos, afirmando que Clinton entregou todos os documentos "
        "ao Departamento de Justiça.",

        'Além da nova fábrica, a NC² está instalando um escritório em São Paulo.',

        'O Conselho de Reitores das Universidades Portuguesas(CRUP) vai entretanto enviar a '
        'Marçal Grilo, no princípio da próxima semana, um pedido de audiência e um convite'
        'à sua participação numa reunião plenária da estrutura, para que possam revelar ao'
        'novo ministro a sua perspectiva sobre os grandes problemas do ensino superior.',

        'António Pires de Lima, que mantém divergências políticas públicas com '
        'Nobre Guedes, considerou que a ausência do ex-ministro do Ambiente vai limitar '
        'o âmbito do próprio Congresso.',
    ]
    for s in sentences:
        text = Text(s, hint_language_code='pt')
        for x in extract_triples(reverb_pattern, text):
            print x
        print
        print "==================="


def main():

    verb = "<ADV>*<AUX>*<VERB><PART>*<ADV>*"
    word = "<NOUN|ADJ|ADV|DET|ADP>"
    preposition = "<ADP|ADJ>"

    rel_pattern = "( %s (%s* (%s)+ )? )+ " % (verb, word, preposition)
    grammar_long = '''REL_PHRASE: {%s}''' % rel_pattern

    print grammar_long
    reverb_pattern = nltk.RegexpParser(grammar_long)

    # test_patterns(reverb_pattern)

    process_chave(reverb_pattern)


if __name__ == "__main__":
    main()
