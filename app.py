

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

