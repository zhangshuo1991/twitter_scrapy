import json

from playwright.sync_api import Playwright, sync_playwright, expect
from datetime import datetime
from tqdm import tqdm


def run(playwright: Playwright, username, conn) -> None:
    try:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        # page.on("request", lambda request: print(">>", request.method, request.url))
        page.on("response", lambda response: handle_response(response, conn, username))
        page.goto(f"https://twitter.com/{username}")
        page.wait_for_load_state()
        text = page.content()
        # print(text)
        # ---------------------
        context.close()
        browser.close()
    except Exception as e:
        print('error: ', username)
        return


def handle_response(response, conn, screen_name):
    #  https://api.twitter.com/graphql/
    now = datetime.now()
    now = now.replace(hour=0, minute=0, second=0, microsecond=0, )
    if response.url.startswith('https://api.twitter.com/graphql/'):
        # print(response.url)
        if response.text() is None or len(response.text()) <= 0:
            return
        with conn.cursor() as cursor:
            cursor.execute(
                """insert into localhost(screen_name, data, update_time)  values (%s,%s,%s)
                ON CONFLICT (screen_name,update_time) DO update set data=excluded.data""",
                (screen_name, response.text(), now))
            conn.commit()
            # print('finished: ', screen_name)

    # print(response.json())


def crawl_twitter_list(conn):
    now = datetime.now()
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            select screen_name from table
                """)
        rows = cursor.fetchall()
        for item in tqdm(rows):
            screen_name = item[0]
            with sync_playwright() as playwright:
                run(playwright, screen_name, conn)


import psycopg2

if __name__ == '__main__':
    w_conn = psycopg2.connect(
        host="localhost",
        database="localhost",
        user="localhost",
        password="localhost")
    crawl_twitter_list(w_conn)
