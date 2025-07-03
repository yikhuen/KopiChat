

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
# try:
#     bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='ap-southeast-1')
#     tavily_client = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
# except Exception as e:
#     st.error(f"Error initializing clients: {e}")
#     st.stop()

try:
    # Initialize Boto3 client with credentials from Streamlit's secrets
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name='ap-southeast-1',
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
    )
    # Initialize Tavily client
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

# Main App Flow
display_chat_history()

# Input Area
uploaded_file = st.file_uploader(
    "Upload an image (optional, for documents/screenshots):",
    type=["png", "jpg", "jpeg", "webp"],
)
perform_search = st.toggle("Search the web for the latest CPF info")

if prompt := st.chat_input("Ask a question about CPF..."):
    
    user_message_content = []
    if uploaded_file:
        image_base64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        user_message_content.append({
            "type": "image", "media_type": uploaded_file.type, "base64_data": image_base64,
        })
    user_message_content.append({"type": "text", "text": prompt})
    st.session_state.messages.append({"role": "user", "content": user_message_content})
    
    # NEW: Detailed System Prompt for CPF Specialization
    system_prompt = """
    You are a specialized AI assistant, an expert on Singapore's Central Provident Fund (CPF).
    Your primary role is to provide clear, helpful, and accurate information about CPF schemes, rules, and regulations.

    **Your Instructions:**

    1.  **Strictly On-Topic:** You MUST answer ONLY questions related to CPF. If a user asks about anything else (e.g., movies, recipes, history), you must politely decline. Your refusal message should be: "I apologize, but my purpose is to assist with inquiries about Singapore's CPF. I am unable to answer questions unrelated to this topic."

    2.  **Core Knowledge Areas:** Your expertise includes all aspects of CPF, such as accounts (OA, SA, MA, RA), contributions, interest rates, CPF LIFE, housing, investments (CPFIS), healthcare (MediShield Life, CareShield Life), and education schemes.

    3.  **Utilize Web Search:** When web search results are provided, prioritize them to answer questions about the very latest CPF policy changes, interest rates, or news, as your internal knowledge may be outdated.

    4.  **CRITICAL - No Financial Advice:** You are an informational tool, not a financial advisor. Never give personalized financial advice or tell a user what they "should" do with their money. If a user asks for advice, explain the relevant schemes objectively and include this disclaimer: "This information is for educational purposes only and does not constitute financial advice. Please consult with a licensed financial advisor for personalized guidance."

    5.  **Refer to Official Sources:** Always encourage users to verify critical information on the official CPF Board website. When providing detailed information, conclude your response with: "For the most current details and to use official calculators, please refer to the CPF Board website at cpf.gov.sg."

    6.  **Privacy First:** Never ask for personal information like NRIC numbers, CPF account numbers, or account balances.
    """
    
    search_context_for_display = None

    if perform_search:
        with st.spinner("Searching the web for the latest CPF information..."):
            try:
                search_results = tavily_client.search(query=f"Singapore CPF {prompt}", search_depth="advanced")
                context_str = "Web search results:\n\n"
                for result in search_results['results']:
                    context_str += f"- **URL:** {result['url']}\n  - **Content:** {result['content']}\n"
                
                search_context_for_display = context_str
                system_prompt += f"\n\n---\n\nUse the following real-time web search results to formulate your answer:\n{context_str}\n---"

            except Exception as e:
                st.error(f"Error during Tavily search: {e}")
                st.stop()

    # Call Bedrock API and Display Streaming Response
    with st.chat_message("assistant"):
        stream_placeholder = st.empty()
        full_response = ""
        
        try:
            api_messages = format_messages_for_api(st.session_state.messages)
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": api_messages
            }
            
            response_stream = bedrock_runtime.invoke_model_with_response_stream(
                body=json.dumps(request_body),
                modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
                accept='application/json',
                contentType='application/json'
            )
            
            for event in response_stream.get("body"):
                chunk = json.loads(event["chunk"]["bytes"])
                
                if chunk['type'] == 'content_block_delta':
                    if chunk['delta']['type'] == 'text_delta':
                        full_response += chunk['delta']['text']
                        stream_placeholder.markdown(full_response + "▌")

            stream_placeholder.markdown(full_response)

            assistant_message = {"role": "assistant", "content": [{"type": "text", "text": full_response}]}
            if search_context_for_display:
                assistant_message["search_results"] = search_context_for_display
            
            st.session_state.messages.append(assistant_message)
            
            st.rerun()
            
        except ClientError as e:
            st.warning(f"🚨 An AWS client error occurred: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")


