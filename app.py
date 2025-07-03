

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



