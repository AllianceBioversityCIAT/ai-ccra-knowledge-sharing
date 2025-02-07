import streamlit as st
from openai import OpenAI
import time

client = OpenAI(
    organization='',
    api_key=''
)

def allAssistant():
    return client.beta.assistants.list(
            order="desc",
            limit="20",
        )

def getAssistantById(id):
    return client.beta.assistants.retrieve(
        assistant_id=id
    )

def createThread():
    empty_thread = client.beta.threads.create()
    return empty_thread

def createMessage(threadId, user_message):
    thread_message = client.beta.threads.messages.create(
        threadId,
        role="user",
        content=user_message,
    )
    return thread_message

def main():
    st.title("AI Annual Report Generator")
    
    if 'thread' not in st.session_state:
        st.session_state.thread = createThread()

    user_input = st.text_area(
        "Enter your prompt:",
        "Generate the narrative of Indicators for the Annual Report 2024.",
        height=100
    )

    if st.button("Generate Report"):
        try:
            with st.spinner("Processing..."):
                assistant = getAssistantById("asst_nh6m5rlAZswQKVX2wYuYgnbu")
                message = createMessage(st.session_state.thread.id, user_input)
                
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread.id,
                    assistant_id=assistant.id,
                )

                while True:
                    run_status = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread.id,
                        run_id=run.id
                    )
                    if run_status.status == 'completed':
                        break
                    elif run_status.status == 'failed':
                        st.error("Run failed. Please try again.")
                        return
                    time.sleep(1)

                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread.id
                )

                for message in messages.data:
                    if message.role == "assistant":
                        st.markdown(message.content[0].text.value)
                        st.success("Report generated successfully!")
                        break

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    main()