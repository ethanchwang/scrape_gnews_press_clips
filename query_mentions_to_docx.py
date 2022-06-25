from gnews import GNews
from newspaper import Article
from docx import Document
import docx
import datetime
from deep_translator import GoogleTranslator
from dataclasses import dataclass,field
from typing import List

@dataclass
class mention_article:
    url: str=''
    title: str=''
    month_num: int=0
    day_num: int=0
    lead_text: str=''
    publisher: str=''
    mention_text: List = field(default_factory=lambda:[])

@dataclass
class topic_article:
    url: str=''
    title: str=''
    publisher: str=''
    month_num: int=0
    day_num: int=0

def find_lead(paragraph_list):
    for idx,paragraph in enumerate(paragraph_list):
        if len(paragraph.split(" "))>15 and paragraph[-1]=='.':
            del paragraph_list[idx]
            return paragraph

def add_hyperlink(paragraph, url, text, color, underline):
    # This gets access to the document.xml.rels file and gets a new relation id value
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    # Create the w:hyperlink tag and add needed values
    hyperlink = docx.oxml.shared.OxmlElement('w:hyperlink')
    hyperlink.set(docx.oxml.shared.qn('r:id'), r_id, )

    # Create a w:r element
    new_run = docx.oxml.shared.OxmlElement('w:r')

    # Create a new w:rPr element
    rPr = docx.oxml.shared.OxmlElement('w:rPr')

    # Add color if it is given
    if not color is None:
        c = docx.oxml.shared.OxmlElement('w:color')
        c.set(docx.oxml.shared.qn('w:val'), color)
        rPr.append(c)

    # Remove underlining if it is requested
    if not underline:
        u = docx.oxml.shared.OxmlElement('w:u')
        u.set(docx.oxml.shared.qn('w:val'), 'none')
        rPr.append(u)

    # Join all the xml elements together add add the required text to the w:r element
    new_run.append(rPr)
    new_run.text = text
    hyperlink.append(new_run)

    paragraph._p.append(hyperlink)

    return hyperlink

def query_mentions(query:str, time_frame:str, language:str) -> list:
    all_mentions_articles = []

    #instantiate GNews object
    google_news = GNews(period=time_frame,max_results=50)
    google_news.language = language
    query_results = [] + google_news.get_news(query)

    #add press clips from query_results to document
    for idx,article in enumerate(query_results):
        all_mentions_articles.append(mention_article(url=article['url']))

        article_obj = Article(article['url'])

        #download articles
        try:
            article_obj.download()
            article_obj.parse()
        except:
            print(f"error: {article['url']}")
            continue

        #get date of article
        date_list = article['published date'].split(" ")
        calendar_map = {'Jun':6,'Jul':7}
        month_num = calendar_map[date_list[2]]
        day_num = date_list[1]

        #ensure clips are in english, if not translate
        article_title = article_obj.title
        if language != 'english':
            article_title = GoogleTranslator(source='auto', target='en').translate(article_obj.title)
            article_text = article_obj.text
            if len(article_obj.text)>5000:
                article_text = article_obj.text[0:4900]
            english_article_text = GoogleTranslator(source='auto', target='en').translate(article_text)
        if language == 'english':
            english_article_text=article_obj.text
        article_text_list = english_article_text.split("\n")

        #populate dataclass
        all_mentions_articles[idx].title = article_title
        all_mentions_articles[idx].month_num = month_num
        all_mentions_articles[idx].day_num = day_num
        all_mentions_articles[idx].publisher = article['publisher']['title']
        all_mentions_articles[idx].lead_text = find_lead(article_text_list)

        #add paragraphs with mention
        for paragraph in article_text_list:
            if query.title().split(" ")[1] in paragraph:
                all_mentions_articles[idx].mention_text.append(paragraph)
                # p = document.add_paragraph(paragraph)
    return all_mentions_articles

def query_topics(topics:list,geographical_area:str) -> list:
    all_topic_articles = {}

    for topic in topics:
        all_topic_articles[topic] = []

        google_news = GNews(period='24h',max_results=4)
        google_news.language = 'english'
        topic_query_result = []
        topic_query_result += google_news.get_news(f'{geographical_area} ' + topic)

        for idx,article in enumerate(topic_query_result):
            all_topic_articles[topic].append(topic_article(url=article['url']))
            article_obj = Article(article['url'])

            try:
                article_obj.download()
                article_obj.parse()
            except:
                print(f"error: {article['url']}")
                continue

            #get date of article
            date_list = article['published date'].split(" ")
            calendar_map = {'Jun':6,'Jul':7}
            month_num = calendar_map[date_list[2]]
            day_num = date_list[1]

            all_topic_articles[topic][idx].title = article_obj.title
            all_topic_articles[topic][idx].month_num = month_num
            all_topic_articles[topic][idx].day_num = day_num
            all_topic_articles[topic][idx].publisher = article['publisher']['title']

            # hyperlink = add_hyperlink(p, article['url'], article_obj.title+f" -- {article['publisher']['title']} {month_num}/{day_num}/22", '0000FF', True)
    return all_topic_articles

def main():
    document = Document()

    query = "adriano espaillat"
    area = "New York City"
    query = query.title()
    time_frame = "24h"
    topics_to_query = ['Housing','Education','Labor','Budget','Immigration','Guns']

    p = document.add_paragraph(f"""CONGRESSMAN {query.split(" ")[1].upper()} MENTIONS:""")
    p = document.add_paragraph()


    for article in query_mentions(query=query,time_frame=time_frame,language='english'):
        p = document.add_paragraph()
        add_hyperlink(p, article.url, article.title+f" -- {article.publisher} {article.month_num}/{article.day_num}/22", '0000FF', True)
        p = document.add_paragraph(article.lead_text)
        for paragraph in article.mention_text:
            p = document.add_paragraph(paragraph)
    for article in query_mentions(query=query,time_frame=time_frame,language='spanish'):
        p = document.add_paragraph()
        add_hyperlink(p, article.url, article.title+f" -- {article.publisher} {article.month_num}/{article.day_num}/22", '0000FF', True)
        p = document.add_paragraph(article.lead_text)
        for paragraph in article.mention_text:
            p = document.add_paragraph(paragraph)
            p = document.add_paragraph()
    topic_query_results = query_topics(topics=topics_to_query,geographical_area=area)
    for topic in topics_to_query:
        p = document.add_paragraph(f"{topic.title()}:")
        for article in topic_query_results[topic]:
            p = document.add_paragraph()
            add_hyperlink(p, article.url, article.title+f" -- {article.publisher} {article.month_num}/{article.day_num}/22", '0000FF', True)

    document.save(f'Press Clips {datetime.date.today()}.docx')

if __name__ == '__main__':
    main()