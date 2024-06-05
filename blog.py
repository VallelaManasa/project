import sqlite3
import pandas as pd
import streamlit as st
import aiohttp
import asyncio
from googlesearch import search
import newspaper
import pyttsx3
from bs4 import BeautifulSoup
import requests
import runpy
from datetime import datetime
import hashlib


# Create a connection object
conn = sqlite3.connect('blog.db')
# Create a cursor object
c = conn.cursor()
# Create the table if it doesn't exist
c.execute('''
CREATE TABLE IF NOT EXISTS posts (
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    date DATE NOT NULL
)
''')

# Create users table
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
)
''')

conn.commit()
conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    try:
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=?', (username,))
        if c.fetchone():
            conn.close()
            return False  # Username already exists
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(e)
        return None

def get_user(username, password):
    try:
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hash_password(password)))
        data = c.fetchone()
        conn.close()
        return data
    except sqlite3.Error as e:
        print(e)
        return None

def add_post(author, title, content, date):
    try:
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute('INSERT INTO posts (author, title, content, date) VALUES (?, ?, ?, ?)', (author, title, content, date))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(e)

def get_all_posts():
    try:
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute('SELECT * FROM posts')
        data = c.fetchall()
        conn.close()
        return data
    except sqlite3.Error as e:
        print(e)
        return []

def get_post_by_title(title):
    try:
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute('SELECT * FROM posts WHERE title=?', (title,))
        data = c.fetchone()
        conn.close()
        return data
    except sqlite3.Error as e:
        print(e)
        return None

def delete_post(title):
    try:
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute('DELETE FROM posts WHERE title=?', (title,))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(e)

def update_likes(title, likes):
    try:
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute('UPDATE posts SET likes=? WHERE title=?', (likes, title))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(e)

def update_rating(title, rating):
    try:
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute('UPDATE posts SET rating=? WHERE title=?', (rating, title))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(e)

title_temp = """
<div style="background-color:#ddf3ed;padding:10px;border-radius:10px;margin:10px;">
<h4 style="color:#53C8B6;text-align:center;">{}</h4>
<img src="https://www.w3schools.com/howto/img_avatar.png" alt="Avatar" style="vertical-align: middle;float:left;width: 50px;height: 50px;border-radius: 50%;">
<h6>Author: {}</h6>
<br/>
<br/>
<p style="text-align:justify"> {}</p>
</div>
"""

post_temp = """
<div style="background-color:#ddf3ed;padding:10px;border-radius:5px;margin:10px;">
<h4 style="color:#53C8B6;text-align:center;">{}</h4>
<h6>Author: {}</h6>
<h6>Date: {}</h6>
<img src="https://www.w3schools.com/howto/img_avatar.png" alt="Avatar" style="vertical-align: middle;width: 50px;height: 50px;border-radius: 50%;">
<br/>
<br/>
<p style="text-align:justify"> {}</p>
</div>
"""

# Session management
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'page' not in st.session_state:
    st.session_state['page'] = 'Home'
if 'navigate_login' not in st.session_state:
    st.session_state['navigate_login'] = False

def navigate_to(page):
    st.session_state['page'] = page
    st.experimental_rerun()


# Sidebar menu
if st.session_state['page'] == "Home":
    if st.session_state['logged_in']:
        menu = ["Home",  "Logout"]
    else:
        menu = ["Signup", "Login"]

    choice = st.sidebar.selectbox("User Info", menu)
else:
    choice = st.session_state['page']


if choice == "Signup":
    st.title("Signup")
    with st.form(key="signup_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Signup")
    if submit:
        if add_user(username, password):
            st.success("User registered successfully. Please log in.")
            st.session_state['navigate_login'] = True
        else:
            st.error("Username already exists. Please choose a different username.")

    if st.button("Login"):
        navigate_to("Login")        
elif choice == "Login":
    st.title("Login")
    with st.form(key="login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
    if submit:
        user = get_user(username, password)
        if user:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success("Logged in successfully.")
            navigate_to("Home")  # Redirect to home page after successful login
        else:
            st.error("Invalid username or password.")

elif choice == "Logout":
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.success("Logged out successfully.")
    navigate_to("Signup")  # Redirect to signup page after logout
else:
    engine = pyttsx3.init()
    st.markdown(
        """
        <style>
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            padding: 10px 20px;
            background-color: #0E1117;
            box-sizing: border-box;
        }
        .logo {
            display: flex;
            align-items: center;
        }
        .logo img {
            height: 60px;
            margin-right: 10px;
        }
        .menu {
            display: flex;
            gap: 20px;
        }
        .menu a {
            text-decoration: none;
            color: white;
            font-weight: bold;
            position: relative;
        }
        .menu a::after {
            content: '';
            position: absolute;
            width: 100%;
            transform: scaleX(0);
            height: 2px;
            bottom: -3px;
            left: 0;
            background-color: white;
            transform-origin: bottom right;
            transition: transform 0.25s ease-out;
        }
        .menu a:hover::after,
        .menu a:focus::after {
            transform: scaleX(1);
            transform-origin: bottom left;
        }
        </style>
        <div class="header">
            <div class="logo">
                <img src="https://static.vecteezy.com/system/resources/previews/022/329/505/non_2x/quill-pen-writing-in-the-papers-on-an-open-book-logo-education-logo-icon-design-suitable-for-company-logo-print-digital-icon-apps-and-other-marketing-material-purpose-education-logo-set-vector.jpg" alt="Logo">
            </div>
            <div class="menu">
                <a href="#">Help</a>
                <a href="#">Contact Us</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def is_url(input_text):
    return input_text.startswith('http://') or input_text.startswith('https://')

async def fetch_article_metadata(session, url):
    try:
        async with session.get(url) as response:
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')

            title = soup.find('title').get_text() if soup.find('title') else 'No title'
            og_image = soup.find('meta', property='og:image')
            image_url = og_image['content'] if og_image else None

            return {
                'title': title,
                'top_image': image_url,
                'url': url
            }
    except Exception as e:
        return None

async def fetch_recommended_articles(query):
    try:
        urls = search(query, num_results=6)
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_article_metadata(session, url) for url in urls]
            articles = await asyncio.gather(*tasks)
            return [article for article in articles if article]
    except Exception as e:
        st.error(f'Sorry, something went wrong: {e}')
        return []

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'username' not in st.session_state:
    st.session_state['username'] = ''

menu = ["Home", "Add Post", "View Posts", "Search Blogs", "Video Summarizer", "Article Summarizer", "Manage"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Home":
    if st.session_state['logged_in']:
        st.write(f"Welcome {st.session_state['username']}")
        url_or_text = st.text_input('', placeholder='Paste the URL of the article and press Enter')

        if url_or_text:
            if is_url(url_or_text):
                try:
                    article = newspaper.Article(url_or_text)
                    article.download()
                    article.parse()

                    img = article.top_image
                    st.image(img)

                    title = article.title
                    st.subheader(title)

                    authors = article.authors
                    st.text(','.join(authors))

                    article.nlp()

                    keywords = article.keywords
                    st.subheader('Keywords:')
                    st.write(', '.join(keywords))

                    tab1, tab2 = st.tabs(["Full Text", "Summary"])
                    with tab1:
                        st.subheader('Full Text')
                        txt = article.text.replace('Advertisement', '')
                        st.write(txt)
                    with tab2:
                        st.subheader('Summary')
                        summary = article.summary.replace('Advertisement', '')
                        st.write(summary)

                    if st.button("Read Summary"):
                        engine.say(summary)
                        engine.runAndWait()

                except Exception as e:
                    st.error(f'Sorry, something went wrong: {e}')

            else:
                try:
                    articles = asyncio.run(fetch_recommended_articles(url_or_text))
                    for article in articles:
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.markdown(f"[{article['title']}]({article['url']})")
                        with col2:
                            if article['top_image']:
                                st.image(article['top_image'], width=150, use_column_width=True)
                except Exception as e:
                    st.error(f'Sorry, something went wrong: {e}')

        st.subheader('Recent News Articles')

        url = "https://newsapi.org/v2/top-headlines?country=in&apiKey=50aec2557c344e3bb301a144b1e673dd"
        r = requests.get(url)
        r = r.json()
        articles = r.get('articles', [])

        if not articles:
            st.write("No articles found for India.")
        else:
            for article in articles:
                st.header(article['title'])
                st.markdown(f"<span style='color: red; font-size: 14px; font-weight: bold;'>Published at: {article['publishedAt']}</span>", unsafe_allow_html=True)
                if article.get('author'):
                    st.write(article['author'])
                st.write(article['source']['name'])
                st.write(article['description'])
                st.write(f"URL: {article['url']}")
                if article['urlToImage'] and article['urlToImage'].endswith(('jpg', 'png', 'jpeg')):
                    st.image(article['urlToImage'])
                else:
                    st.write("Image format not supported or URL not provided")

elif choice == "Video Summarizer":
    runpy.run_path("vedio.py")

elif choice == "Article Summarizer":
    runpy.run_path("article.py")

elif choice == "View Posts":
    st.title("View Posts")
    st.write("Here you can see all the posts in the blog.")
    posts = get_all_posts()
    if posts:
        for idx, post in enumerate(posts):
            st.markdown(title_temp.format(post[1], post[0], post[2][:50] + "..."), unsafe_allow_html=True)

            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                if st.button("Read More", key=f"read_more_{idx}"):
                    st.markdown(post_temp.format(post[1], post[0], post[3], post[2]), unsafe_allow_html=True)

            with col2:
                like_key = f"like_{idx}"
                like_button_id = f"like_button_{idx}"
                like_button_style = """
                <style>
                .like-button {
                    cursor: pointer;
                    border: none;
                    background-color: transparent;
                    color: #000;
                }
                .liked {
                    color: #e74c3c; /* Red color */
                }
                </style>
                """
                st.markdown(like_button_style, unsafe_allow_html=True)
                liked = st.session_state.get(f'liked_{idx}', False)
                like_count = st.session_state.get(f'like_count_{idx}', 0)
                if st.button("❤", key=like_key, help="Like" if not liked else "Unlike", on_click=lambda: toggle_like(idx)):
                    liked = not liked
                    st.session_state[f'liked_{idx}'] = liked
                    like_count = like_count + 1 if liked else max(0, like_count - 1)
                    st.session_state[f'like_count_{idx}'] = like_count
                if like_count > 0:
                    st.markdown(f'<button class="like-button {"liked" if liked else ""}" id="{like_button_id}">{like_count}</button>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<button class="like-button {"liked" if liked else ""}" id="{like_button_id}"></button>', unsafe_allow_html=True)

            with col3:
                rating_key = f"rating_{idx}"
                rating = st.slider(f"Rate {post[1]}", 1, 5, key=rating_key)
                update_rating(post[1], rating)
    else:
        st.write("No posts available.")

elif choice == "Add Post":
    st.title("Add Post")
    st.write("Here you can add a new post to the blog.")
    with st.form(key="add_form"):
        author = st.text_input("Author")
        title = st.text_input("Title")
        content = st.text_area("Write your article here:", height=500)
        date = st.date_input("Date")
        submit = st.form_submit_button("Submit")
    if submit:
        add_post(author, title, content, date)
        st.success("Post added successfully")

elif choice == "Search Blogs":
    st.title("Search")
    st.write("Here you can search for a post by title or author.")
    query = st.text_input("Enter your query")
    if query:
        posts = get_all_posts()
        results = [post for post in posts if query.lower() in post[0].lower() or query.lower() in post[1].lower()]
        if results:
            st.write(f"Found {len(results)} matching posts:")
            for idx, result in enumerate(results):
                st.markdown(title_temp.format(result[1], result[0], result[2][:50] + "..."), unsafe_allow_html=True)
                if st.button("Read More", key=f"search_read_more_{idx}"):
                    st.markdown(post_temp.format(result[1], result[0], result[3], result[2]), unsafe_allow_html=True)
        else:
            st.write("No matching posts found")

elif choice == "Manage":
    st.title("Manage")
    st.write("Here you can delete posts or view some statistics.")
    titles = [post[1] for post in get_all_posts()]
    title = st.selectbox("Select a post to delete", titles)
    if st.button("Delete"):
        delete_post(title)
        st.success("Post deleted successfully")
    if st.checkbox("Show statistics"):
        posts = get_all_posts()
        df = pd.DataFrame(posts, columns=["author", "title", "content", "date"])
        st.write("Number of posts:", len(posts))
        st.write("Number of authors:", len(df["author"].unique()))
        st.write("Most recent post:", df["date"].max())
        st.write("Oldest post:", df["date"].min())
        st.write("Posts by author:")
        author_count = df["author"].value_counts()
        st.bar_chart(author_count)

# Function to toggle like
def toggle_like(idx):
    liked = st.session_state.get(f'liked_{idx}', False)
    st.session_state[f'liked_{idx}'] = not liked

    # Update likes count in database
    title = get_all_posts()[idx][1]
    likes_count = st.session_state.get(f'like_count_{idx}', 0)
    update_likes(title, likes_count)
