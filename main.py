import asyncio
import streamlit as st
import streamlit.components.v1 as components
from agents import AgentManager
import re
import time


# Initialize event loop
if "event_loop" not in st.session_state:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    st.session_state["event_loop"] = loop
else:
    loop = st.session_state["event_loop"]

# Initialize session state variables
if "scan_results" not in st.session_state:
    st.session_state["scan_results"] = []
if "agent_manager" not in st.session_state:
    st.session_state["agent_manager"] = AgentManager()
if "initial_prompt" not in st.session_state:
    st.session_state["initial_prompt"] = ""  # Stores the original user input
if "feedback_history" not in st.session_state:
    st.session_state["feedback_history"] = []  # Stores all feedback inputs
if "show_feedback_ui" not in st.session_state:
    st.session_state["show_feedback_ui"] = False  # Determines when to show feedback UI


# Extract HTML, CSS, and JS from response
def extract_code(response):
    html_match = re.search(r'<html.*?>[\s\S]*?<\/html>', response, re.IGNORECASE)
    css_match = re.search(r'<style.*?>[\s\S]*?<\/style>', response, re.IGNORECASE)
    js_match = re.search(r'<script.*?>[\s\S]*?<\/script>', response, re.IGNORECASE)

    html_content = html_match.group(0) if html_match else ""
    css_content = css_match.group(0) if css_match else ""
    js_content = js_match.group(0) if js_match else ""

    return f"{html_content}\n{css_content}\n{js_content}"


# Process user input and get agent responses
async def process_user_input(query, agent_manager):
    agents_response, conversation_log = await agent_manager.updated_multi_agentic_chat(query)
    return agents_response, conversation_log

async def process_user_input_for_feedback(query, agent_manager):
    agents_response, conversation_log = await agent_manager.feedback_multi_agentic_chat(query)
    return agents_response, conversation_log


# Main app layout
def main():
    st.set_page_config(
        page_title="Multi-Agentic UI Component Builder",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    st.title("🤖 UI Component Builder")

    if not st.session_state["show_feedback_ui"]:
        # Initial UI - User enters requirements
        st.session_state["initial_prompt"] = st.text_area(
            label="Enter your UI requirements:", 
            value="""Create a modern, clean UI section for a webpage promoting 'Copilot+ PC' with a focus on AI-powered devices. The design should include:
- A centered title with 'Copilot+ PC' in a smaller font at the top.
- A large, bold headline that says 'Join the era of AI' with 'Join' in blue, 'the era of' in black, and 'AI' in brown.
- A short description below in a smaller font explaining the product, mentioning Microsoft Surface and Snapdragon X Elite Plus processors.
- Two call-to-action buttons: 'Explore Surface Pro' and 'Explore Surface Laptop', styled as blue buttons with white text.
- The layout should be responsive, with good spacing, a clean background, and readable typography."""
        )

        if st.button("Generate UI Code") and st.session_state["initial_prompt"]:
            start_time = time.time()
            
            with st.spinner("Processing your request, please wait..."):
                file_data, conversation_log = st.session_state["event_loop"].run_until_complete(
                    process_user_input(st.session_state["initial_prompt"], st.session_state["agent_manager"])
                )

            extracted_code = extract_code(file_data)

            # Display generated UI
            st.markdown("### Rendered UI Preview")
            components.html(extracted_code, height=600, scrolling=True)
            end_time = time.time()
            # st.markdown(f"### Time taken: {end_time - start_time:.2f} seconds")

            # Store the generated code for further iterations
            st.session_state["latest_generated_code"] = extracted_code

            # Log the conversation
            st.session_state["conversation_log"] = conversation_log

            # Enable Feedback UI for subsequent runs
            st.session_state["show_feedback_ui"] = True
            st.rerun()  # Refresh UI to hide the initial input section

    else:
        # Show UI only for feedback submission
        st.markdown("### Rendered UI Preview (Updated)")
        components.html(st.session_state["latest_generated_code"], height=600, scrolling=True)

        # Show Agent Conversation Flow
        with st.expander("Show latest Agent Conversation"):
            st.markdown("### 🔄 Agent Conversation Flow")
            if st.session_state["feedback_history"]:
                st.markdown(f"**User feedback:** {st.session_state['feedback_history'][-1]}")
            for entry in st.session_state["conversation_log"]:
                st.markdown(f"**{entry['agent']}:** {entry['message']}")

        # Feedback Section
        user_feedback = st.text_area("Provide your feedback to improve the UI:", "")

        if st.button("Submit Feedback and Regenerate UI") and user_feedback:
            start_time = time.time()

            # Store feedback
            st.session_state["feedback_history"].append(user_feedback)

            # Create new prompt by combining original input + all feedbacks
            updated_prompt = st.session_state["initial_prompt"] + "\n\n" + "\n".join(st.session_state["feedback_history"])

            with st.spinner("Processing feedback and regenerating UI..."):
                file_data, conversation_log = st.session_state["event_loop"].run_until_complete(
                    process_user_input_for_feedback(updated_prompt, st.session_state["agent_manager"])
                )

            extracted_code = extract_code(file_data)

            # Store the new generated code
            st.session_state["latest_generated_code"] = extracted_code
            # Store the new conversation log
            st.session_state["conversation_log"] = conversation_log

            end_time = time.time()
            # st.markdown(f"### Time taken: {end_time - start_time:.2f} seconds")

            # Refresh UI to update with the new version
            st.rerun()

if __name__ == "__main__":
    main()