from gnews import GNews
from newspaper import Article
import datetime
from deep_translator import GoogleTranslator
from dataclasses import dataclass, field
from typing import List
from bs4 import BeautifulSoup
import argparse
import os


@dataclass
class mention_article:
    url: str = ""
    title: str = ""
    month_num: int = 0
    day_num: int = 0
    lead_text: str = ""
    publisher: str = ""
    mention_text: List = field(default_factory=lambda: [])


@dataclass
class topic_article:
    url: str = ""
    title: str = ""
    publisher: str = ""
    month_num: int = 0
    day_num: int = 0


def find_lead(paragraph_list):
    for idx, paragraph in enumerate(paragraph_list):
        if len(paragraph.split(" ")) > 15 and paragraph[-1] == ".":
            del paragraph_list[idx]
            return paragraph


def query_mentions(query: str, time_frame: str, language: str) -> list:
    all_mentions_articles = []

    google_news = GNews(period=time_frame, max_results=10)
    google_news.language = language
    query_results = [] + google_news.get_news(query)

    # add press clips from query_results to document
    for idx, article in enumerate(query_results):
        all_mentions_articles.append(mention_article(url=article["url"]))

        article_obj = Article(article["url"])

        # download articles
        try:
            article_obj.download()
            article_obj.parse()
        except:
            print(f"error: {article['url']}")
            continue

        # get date of article
        date_list = article["published date"].split(" ")
        calendar_map = {
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Nov": 11,
            "Dec": 12,
        }
        month_num = calendar_map[date_list[2]]
        day_num = date_list[1]

        # ensure clips are in english, if not translate
        article_title = article_obj.title
        if language != "english":
            article_title = GoogleTranslator(source="auto", target="en").translate(
                article_obj.title
            )
            article_text = article_obj.text
            if len(article_obj.text) > 5000:
                article_text = article_obj.text[0:4900]
            english_article_text = GoogleTranslator(
                source="auto", target="en"
            ).translate(article_text)
        if language == "english":
            english_article_text = article_obj.text
        article_text_list = english_article_text.split("\n")

        # populate dataclass
        all_mentions_articles[idx].title = article_title
        all_mentions_articles[idx].month_num = month_num
        all_mentions_articles[idx].day_num = day_num
        all_mentions_articles[idx].publisher = article["publisher"]["title"]
        all_mentions_articles[idx].lead_text = find_lead(article_text_list)

        # add paragraphs with mention
        for paragraph in article_text_list:
            if query.title().split(" ")[1] in paragraph:
                all_mentions_articles[idx].mention_text.append(paragraph)
    return all_mentions_articles


def query_topics(topics: list, geographical_area: str, period) -> list:
    all_topic_articles = {}

    for topic in topics:
        all_topic_articles[topic] = []

        google_news = GNews(period=period, max_results=4)
        google_news.language = "english"
        topic_query_result = []
        topic_query_result += google_news.get_news(f"{geographical_area} " + topic)

        for idx, article in enumerate(topic_query_result):
            all_topic_articles[topic].append(topic_article(url=article["url"]))
            article_obj = Article(article["url"])

            try:
                article_obj.download()
                article_obj.parse()
            except:
                print(f"error: {article['url']}")
                continue

            # get date of article
            date_list = article["published date"].split(" ")
            calendar_map = {
                "Jan": 1,
                "Feb": 2,
                "Mar": 3,
                "Apr": 4,
                "May": 5,
                "Jun": 6,
                "Jul": 7,
                "Aug": 8,
                "Sep": 9,
                "Nov": 11,
                "Dec": 12,
            }
            month_num = calendar_map[date_list[2]]
            day_num = date_list[1]

            all_topic_articles[topic][idx].title = article_obj.title
            all_topic_articles[topic][idx].month_num = month_num
            all_topic_articles[topic][idx].day_num = day_num
            all_topic_articles[topic][idx].publisher = article["publisher"]["title"]

    return all_topic_articles


# creates paragraph that bolds name of query
def bold_name(name: str, text: str):
    temp_html = "<h1>"

    delimiter = name.split()[-1].title()
    split_paragraph = text.split(delimiter)

    for index, text in enumerate(split_paragraph):
        temp_html += text
        if index != len(split_paragraph) - 1:
            temp_html += f"""<b>{delimiter}</b>"""

    return temp_html + "</h1>"


def main():
    html = """<head><link rel="stylesheet" href="style.css"></head>"""

    # Initialize the parser
    parser = argparse.ArgumentParser(
        description="Query information about a specific area and topics."
    )

    # Adding arguments
    parser.add_argument(
        "--query",
        type=str,
        default="joe biden",
        help="Query string, e.g., a person's name.",
    )
    parser.add_argument(
        "--area",
        type=str,
        default="new york city",
        help="The area of interest, e.g., a city name.",
    )
    parser.add_argument(
        "--time_frame",
        type=str,
        choices=["24h", "48h", "7d", "30d"],
        default="24h",
        help="Time frame for the query. Options: 24h, 7d, 30d.",
    )
    parser.add_argument(
        "--topics_to_query",
        type=str,
        default="housing,education,labor,budget,immigration,guns",
        help='Comma-separated list of topics to query, e.g., "Housing,Education,Labor".',
    )
    parser.add_argument(
        "--language", type=str, help="Clips in different language to search for."
    )

    # Parse the arguments
    args = parser.parse_args()

    # Post-process topics_to_query to convert from comma-separated string to list
    if args.topics_to_query:
        topics_list = [topic.strip() for topic in args.topics_to_query.split(",")]
    else:
        topics_list = []

    # Adjust query to title case
    query = " ".join(args.query.split("_")).title()
    time_frame = args.time_frame
    topics_to_query = topics_list
    area = " ".join(args.area.split("_"))
    language = args.language

    # title
    html += f"<h1><b><u>{query.upper()} MENTIONS:</b></u></h1><br>"

    # english clips
    for article in query_mentions(
        query=query, time_frame=time_frame, language="english"
    ):

        html += f"""<h1><b><u><a href="{article.url}" target="_blank">{article.title} -- {article.publisher} {article.month_num}/{article.day_num}/22</a></u></b></h1>"""
        html += f"""<h1>{article.lead_text}</h1><br>"""
        for paragraph in article.mention_text:
            html += bold_name(name=query, text=paragraph) + "<br>"

    # non-english clips
    if language:
        for article in query_mentions(
            query=query, time_frame=time_frame, language=language
        ):
            html += f"""<h1><b><u><a href="{article.url}" target="_blank">{article.title} -- {article.publisher} {article.month_num}/{article.day_num}/22</a></u></b></h1>"""
            html += f"""<h1>{article.lead_text}</h1><br>"""
            for paragraph in article.mention_text:
                html += bold_name(name=query, text=paragraph) + "<br>"

    # topic clips
    topic_query_results = query_topics(
        topics=topics_to_query, geographical_area=area, period=time_frame
    )
    html += "<h1><b><u>PRESS CLIPS:</b></u></h1>"
    for topic in topics_to_query:
        html += f"""<h1>-</h1>"""
        html += f"<h1><b><u{topic.title()}</b></u></h1>"
        for article in topic_query_results[topic]:
            html += f"""<h1><b><u><a href="{article.url}" target="_blank">{article.title} -- {article.publisher} {article.month_num}/{article.day_num}/22</a></u></b></h1>"""

    path = "./out/"
    os.makedirs(path, exist_ok=True)
    html = html.replace("’", """'""")
    html = html.replace("–", "-")
    html = html.replace("“", '"')
    html = html.replace("‘", """'""")
    html = html.replace("”", '"')
    html = html.replace("—", "-")

    soup = BeautifulSoup(html, "html.parser")
    with open(path + f"{query} Press Clips {datetime.date.today()}.html", "w") as file:
        file.write(soup.prettify())


if __name__ == "__main__":
    main()
