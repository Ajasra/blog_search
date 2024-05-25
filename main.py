import hashlib

import streamlit as st

from libs.data_handle import get_db, get_books_links
from libs.gemini_api import generate_answer

st.set_page_config(
    page_title="Deep Life Index",
    page_icon=":book:",
    layout="centered",
)


def make_hashes(password):
    """Hash the input password."""
    return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password, hashed_text):
    """Check if the hashed password matches the stored hash."""
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False


def interact():

    if 'database' not in st.session_state:
        st.session_state.database = get_db()
        st.session_state.books = get_books_links()

    # Title of the app
    st.title("Deep Life Index")

    # Dropdown to select the model
    model_selected = st.selectbox(
        'Choose a model',
        ['gemini-1.5-flash-latest', 'gemini-1.5-pro-latest']
    )

    # Text input field for the answer
    question = st.text_area("Write your question here:")

    # Button to submit the answer
    if st.button("Submit"):

        query = question
        model = model_selected
        answer, content, metadata = generate_answer(query, st.session_state.database, model)

        # Display the answer in Markdown format
        st.markdown(f"## REPLY:\n{answer}")

        st.markdown("## Sources:")
        for i in range(len(metadata)):
            meta = metadata[i]
            source_info = ""

            if 'url' in meta:
                source_info += f"[{meta['url']}]({meta['url']})"
            if 'source' in meta:
                source_info += f" [{meta['source']}]({meta['source']})"

            if 'name' in meta:
                title = meta['name']
                url = ""
                for q in range(0, len(st.session_state.books)):
                    book = st.session_state.books[q]
                    if meta['name'] == book['name']:
                        title = book['title']
                        url = book['url']
                        break
                source_info += f" {title}"
                with st.expander(source_info):
                    st.markdown(content[i])
                    if url:
                        st.markdown(f"[Order]({url})")
            else:
                st.markdown(f"- {source_info}")


def main():
    """Main function to run the Streamlit app."""
    # Password hashing and checking
    password = st.secrets["password"]  # Retrieve password from secrets
    password = make_hashes(password)  # Hash the password

    # Display the password input fields
    psw_title = st.title("Password Protected App")
    text_input_container = st.empty()
    password_input = text_input_container.text_input("Password", type="password")

    if check_hashes(password_input, password):
        st.session_state.logged_in = True
        # hide the password input fields
        text_input_container.empty()
        psw_title.empty()
        interact()

    elif password_input != "":
        st.warning("Incorrect Password")


if __name__ == '__main__':
    main()