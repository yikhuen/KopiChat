

import streamlit as st
import boto3
import json
import base64
from botocore.exceptions import ClientError
from tavily import TavilyClient

# Page Configuration 
st.set_page_config(page_title="CPF Assistant", layout="centered")
# NEW: Updated Title and Markdown
st.title("🤖 KopiChat")
st.markdown("Your AI-powered guide to Singapore's Central Provident Fund. Ask me about your CPF accounts, schemes, and regulations.")
st.divider()

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Boto3 & Tavily Client Initialization
try:
    bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='ap-southeast-1')
    tavily_client = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
except Exception as e:
    st.error(f"Error initializing clients: {e}")
    st.stop()

# Helper Functions (Unchanged)
def format_messages_for_api(messages):
    api_messages = []
    for msg in messages:
        role = msg["role"]
        content = []
        for block in msg["content"]:
            if block["type"] == "text":
                content.append({"type": "text", "text": block["text"]})
            elif block["type"] == "image":
                content.append({
                    "type": "image",
                    "source": { "type": "base64", "media_type": block["media_type"], "data": block["base64_data"] },
                })
        api_messages.append({"role": role, "content": content})
    return api_messages

def display_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "search_results" in message:
                with st.expander("Show Web Search Results"):
                    st.markdown(message["search_results"])
            for content_block in message.get("content", []):
                if content_block["type"] == "text":
                    st.markdown(content_block["text"])
                elif content_block["type"] == "image":
                    image_bytes = base64.b64decode(content_block["base64_data"])
                    st.image(image_bytes, caption=f"Image ({content_block['media_type']})")


