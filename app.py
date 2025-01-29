import streamlit as st
import pandas as pd
import requests
import openai
import datetime

# **SETUP API KEYS**
NEWS_API_KEY = "YOUR_NEWS_API_KEY"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# **STREAMLIT PAGE CONFIGURATION**
st.set_page_config(page_title="News Topic Analyzer", page_icon="📰", layout="wide")

# **STYLING**
st.markdown("""
    <style>
    .example-commands { font-size: 14px !important; }
    .chat-bubble { padding: 10px; border-radius: 10px; margin-bottom: 10px; }
    .user-message { background-color: #f0f0f5; }
    .ai-message { background-color: #dfe7fd; }
    </style>
""", unsafe_allow_html=True)

# **HEADER & DESCRIPTION**
st.markdown("""
# 📰 News Topic Analyzer
Welcome to the **News Topic Analyzer**! This AI-powered app allows you to **fetch, summarize, analyze sentiment, and extract topics** interactively via chat.

## **Features**
- 📰 **Fetch latest news on any topic**
- 📝 **Summarize news articles**
- 🔍 **Analyze sentiment (Positive, Neutral, Negative)**
- 📌 **Extract main topics from news articles**
- 📥 **Download CSV files for offline analysis**
""")

# **EXAMPLE COMMANDS**
st.markdown("""
### 📝 **Example Commands**
✅ **Fetch news about Bitcoin**  
✅ **Summarize the latest news**  
✅ **Analyze sentiment of the news**  
✅ **Get the topics on the news**  
""", unsafe_allow_html=True)

# **SESSION STATE SETUP**
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "dataframes" not in st.session_state:
    st.session_state.dataframes = {}

# **SLIDER TO SET NUMBER OF ARTICLES**
num_articles = st.slider("Select number of articles", min_value=1, max_value=1000, value=10)


# **FUNCTION TO FETCH NEWS**
def fetch_news(query, max_results=num_articles):
    """Fetch latest news articles based on user query."""
    api_url = f"https://newsapi.org/v2/everything?q={query}&from={datetime.datetime.now() - datetime.timedelta(days=14)}&sortBy=publishedAt&pageSize={max_results}&apiKey={NEWS_API_KEY}"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        articles = data.get("articles", [])

        if not articles:
            return None, "No articles found."

        df = pd.DataFrame(articles)[["source", "title", "publishedAt"]]
        df["source"] = df["source"].apply(lambda x: x.get("name", "Unknown"))
        return df, None
    return None, "Error fetching news data."


# **FUNCTION TO SUMMARIZE NEWS**
def summarize_news(df):
    """Summarize news articles using GPT-4o-mini."""
    openai.api_key = OPENAI_API_KEY
    news_text = "\n".join(df["title"].tolist())
    prompt = f"Summarize the following news articles:\n{news_text}"

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt}]
    )

    return response["choices"][0]["message"]["content"]


# **FUNCTION TO ANALYZE SENTIMENT**
def analyze_sentiment(df):
    """Analyze sentiment of news articles using GPT-4o-mini."""
    openai.api_key = OPENAI_API_KEY
    sentiments = []

    for title in df["title"]:
        prompt = f"Determine the sentiment (Positive, Neutral, Negative) of this news title: {title}"

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}]
        )

        sentiment = response["choices"][0]["message"]["content"]
        sentiments.append(sentiment)

    df["Sentiment"] = sentiments
    return df


# **FUNCTION TO EXTRACT TOPICS**
def extract_topics(df):
    """Extract main topics from news articles using GPT-4o-mini."""
    openai.api_key = OPENAI_API_KEY
    news_text = "\n".join(df["title"].tolist())
    prompt = f"Extract the main topics from these news articles:\n{news_text}"

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt}]
    )

    topics = response["choices"][0]["message"]["content"].split("\n")
    return topics


# **CHAT RESPONSE FUNCTION**
def chat_response(user_input):
    """Handle user input and provide AI-based responses."""
    response_text = ""

    if user_input.startswith("Fetch news about"):
        query = user_input.replace("Fetch news about", "").strip()
        df, error = fetch_news(query)

        if error:
            response_text = f"❌ {error}"
        else:
            response_text = f"✅ Fetched {len(df)} articles related to '{query}'."
            st.session_state.dataframes[query] = df

            # **Display News Table**
            st.write(f"📰 **News Data for '{query}':**")
            st.dataframe(df)

            # **Download Button**
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(label=f"📥 Download {query} News", data=csv_data, file_name=f"{query}_news.csv", mime="text/csv")

    elif user_input == "Summarize the latest news":
        if st.session_state.dataframes:
            latest_query = list(st.session_state.dataframes.keys())[-1]
            df = st.session_state.dataframes[latest_query]
            summary = summarize_news(df)
            response_text = f"📝 **News Summary:**\n{summary}"
        else:
            response_text = "❌ No data available to summarize. Fetch news first."

    elif user_input == "Analyze sentiment of the news":
        if st.session_state.dataframes:
            latest_query = list(st.session_state.dataframes.keys())[-1]
            df = st.session_state.dataframes[latest_query]
            df = analyze_sentiment(df)
            st.session_state.dataframes[latest_query] = df

            # **Display Sentiment Table**
            st.write("🔍 **Sentiment Analysis:**")
            st.dataframe(df[["title", "publishedAt", "Sentiment"]])

            # **Save to Chat History**
            response_text = "🔍 **Sentiment Analysis for Recent News:**\n"
            for _, row in df.iterrows():
                response_text += f"📰 **{row['title']}** - Sentiment: **{row['Sentiment']}**\n"
        else:
            response_text = "❌ No data available to analyze sentiment. Fetch news first."

    elif user_input == "Get the topics on the news":
        if st.session_state.dataframes:
            latest_query = list(st.session_state.dataframes.keys())[-1]
            df = st.session_state.dataframes[latest_query]
            topics = extract_topics(df)

            response_text = "📌 **Extracted Topics:**\n"
            for idx, topic in enumerate(topics, 1):
                response_text += f"{idx}. {topic}\n"
        else:
            response_text = "❌ No data available to extract topics. Fetch news first."

    else:
        response_text = "❌ Unknown command."

    # **Display Chat Message**
    st.chat_message("ai").write(response_text)
    st.session_state.chat_history.append({"role": "ai", "content": response_text})


# **DISPLAY CHAT HISTORY**
for message in st.session_state.chat_history:
    st.chat_message(message["role"]).write(message["content"])

user_query = st.chat_input("Enter your query here:")
if user_query:
    st.chat_message("human").write(user_query)
    st.session_state.chat_history.append({"role": "human", "content": user_query})
    chat_response(user_query)
