import streamlit as st
from newspaper import Article
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, VideoUnavailable
from transformers import pipeline
import nltk
import requests
import json

# Download NLTK data
nltk.download('punkt')

# Load the summarization pipeline
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

st.title('Article and Video Summarizer')

url = st.text_input('URL Input', placeholder='Paste the URL of the article or YouTube video and press Enter', label_visibility='collapsed')

def summarize_text(text, max_chunk=1000):
    summarized_text = []
    num_iters = int(len(text) / max_chunk) + 1
    for i in range(num_iters):
        start = i * max_chunk
        end = min((i + 1) * max_chunk, len(text))
        chunk = text[start:end]
        if chunk:
            out = summarizer(chunk, max_length=150, min_length=30, do_sample=False)
            summarized_text.append(out[0]['summary_text'])
    return " ".join(summarized_text)

def get_transcript(video_id, language='en'):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript([language])
        return " ".join([item['text'] for item in transcript.fetch()])
    except NoTranscriptFound:
        return None
    except TranscriptsDisabled:
        st.error("Transcripts are disabled for this video.")
    except VideoUnavailable:
        st.error("The video is unavailable.")
    except Exception as e:
        st.error(f"An error occurred while fetching the transcript: {str(e)}")
    return None

def get_youtube_video_details(video_id, api_key):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            snippet = data["items"][0]["snippet"]
            title = snippet["title"]
            thumbnail_url = snippet["thumbnails"]["high"]["url"]
            return title, thumbnail_url
    return None, None

if url:
    if 'youtube.com/watch' in url or 'youtu.be/' in url:
        try:
            if 'youtube.com/watch' in url:
                video_id = url.split('v=')[-1]
            elif 'youtu.be/' in url:
                video_id = url.split('/')[-1]

            st.write(f"Extracted Video ID: {video_id}")

            # Provide your YouTube Data API key here
            api_key = "AIzaSyBpeSG0qej8ZFJ0uZ267nfHBW0fv_RQLEo"
            video_title, thumbnail_url = get_youtube_video_details(video_id, api_key)

            if video_title and thumbnail_url:
                st.image(thumbnail_url)
                st.subheader(video_title)

            transcript = get_transcript(video_id)
            if not transcript:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                available_languages = transcript_list._manually_created_transcripts or transcript_list._generated_transcripts
                available_languages = [t.language_code for t in available_languages]
                st.write(f"Available languages: {', '.join(available_languages)}")
                language = st.selectbox("Select a language", available_languages)
                transcript = get_transcript(video_id, language)

            if transcript:
                tab1, tab2 = st.tabs(["Full Text", "Summary"])
                with tab1:
                    st.subheader('Full Text:')
                    st.write(transcript)

                with tab2:
                    summarized_text = summarize_text(transcript)
                    st.subheader('Summary:')
                    st.write(summarized_text)
            else:
                st.error("Could not retrieve a transcript for the video.")
        except Exception as e:
            st.error(f"Sorry, something went wrong: {str(e)}")