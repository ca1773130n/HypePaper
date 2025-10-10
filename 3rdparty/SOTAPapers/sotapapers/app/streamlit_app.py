import streamlit as st
import loguru # Import loguru for logging
import pandas as pd # Added pandas for DataFrame handling

from sotapapers.utils.config import get_config_path
from sotapapers.core.settings import Settings
from sotapapers.core.database import DataBase
from sotapapers.modules.database_query_agent import DatabaseQueryAgent

settings = Settings(get_config_path())
config = settings.config

APP_TITLE = config.streamlit_app.title
APP_PORT = config.streamlit_app.port

# Initialize session state for login
if "is_user_logged_in" not in st.session_state:
    st.session_state.is_user_logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# Initialize database
# Assuming db path is in config.database.path
db = DataBase(db_url=config.database.url, logger=loguru.logger)

def login_screen():
    st.header(f"Please log in to {APP_TITLE}.")
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password") # Add password input

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            user = db.get_user_by_username(username_input)
            if user and db.verify_password(password_input, user.password_hash):
                st.session_state.is_user_logged_in = True
                st.session_state.current_user = user
                st.success(f"Welcome, {user.username}!")
                st.rerun()
            else:
                st.error("Invalid username or password.") # More general error message for security
    with col2:
        if st.button("Register"):
            if username_input and password_input:
                user = db.get_user_by_username(username_input)
                if user is None:
                    # Pass password to create_user
                    new_user = db.create_user(username=username_input, password=password_input, google_id=f"dummy_google_id_{username_input}")
                    st.session_state.is_user_logged_in = True
                    st.session_state.current_user = new_user
                    st.success(f"Account created and logged in as {new_user.username}!")
                    st.rerun()
                else:
                    st.warning("Username already exists. Please choose a different one.")
            else:
                st.error("Please enter both username and password to register.")

def load_papers_with_code():
    # load papers from database
    papers = db.get_papers_with_code()
    st.dataframe(papers)

def show_main_app():
    st.set_page_config(layout="wide")

    st.sidebar.title("SOTA Papers")
    st.sidebar.markdown("---")
    
    # User Profile Section in Sidebar
    if st.session_state.current_user:
        st.sidebar.write(f"@**{st.session_state.current_user.username}**")
        if st.sidebar.button("Logout"):
            st.session_state.is_user_logged_in = False
            st.session_state.current_user = None
            st.rerun()
        st.sidebar.markdown("---")

    menu_options = {
        "Daily arXiv Monitor": "daily_arxiv", 
        "Trending Papers with Code": "trending_papers", 
        "Find SOTA": "find_sota", 
        "Paper Galaxy": "paper_galaxy",
        "Natural Language Query": "natural_language_query", # Add new menu option
        "User Profile": "user_profile" # Add user profile to menu
    }

    if "current_page" not in st.session_state:
        st.session_state.current_page = menu_options["Daily arXiv Monitor"]

    for display_name, key in menu_options.items():
        if st.sidebar.button(display_name):
            st.session_state.current_page = key
            st.rerun()

    # Display content based on current_selection_key
    if st.session_state.current_page == menu_options["Daily arXiv Monitor"]:
        show_daily_arxiv_monitor_page()
    elif st.session_state.current_page == menu_options["Trending Papers with Code"]:
        show_trending_papers_page()
    elif st.session_state.current_page == menu_options["Find SOTA"]:
        show_find_sota_paper_page()
    elif st.session_state.current_page == menu_options["Paper Galaxy"]:
        show_paper_galaxy_page()
    elif st.session_state.current_page == menu_options["Natural Language Query"]:
        show_natural_language_query_page()
    elif st.session_state.current_page == menu_options["User Profile"]:
        show_user_profile_page()

def show_daily_arxiv_monitor_page():
    st.header("Daily arXiv Monitor Page - Dummy Content")
    st.write("This page could display daily arXiv paper summaries.")
    st.button("Load Latest Papers")
    st.dataframe({'Title': ['Paper A', 'Paper B'], 'Authors': ['Author 1', 'Author 2']})

def show_trending_papers_page():
    load_papers_with_code()
    st.header("Trending Papers with Code Page - Dummy Content")
    st.write("Here you might see a list of trending papers with links to their code.")
    st.slider("Select number of papers to display", 5, 20, 10)
    st.image("https://via.placeholder.com/300", caption="Placeholder for a trend chart")

def show_find_sota_paper_page():
    st.header("Find a SOTA Paper Page - Dummy Content")
    st.write("Use this section to search for State-of-the-Art papers.")
    st.text_input("Search Keywords", "Enter your query here")
    st.checkbox("Include citations")
    st.table({'Paper': ['SOTA Paper 1', 'SOTA Paper 2'], 'Metric': ['95%', '92%']})

def show_paper_galaxy_page():
    st.header("Paper Galaxy Page - Dummy Content")
    st.write("Explore the interconnectedness of papers in a graph visualization.")
    st.selectbox("Select a field of study", ["Computer Vision", "Natural Language Processing", "Reinforcement Learning"])
    st.warning("Graph visualization will be embedded here.")

def show_natural_language_query_page():
    st.header("Natural Language Database Query")
    st.write("Enter your natural language query to retrieve information from the database.")

    # Initialize the DatabaseQueryAgent
    db_query_agent = DatabaseQueryAgent(settings, loguru.logger, db)

    query_input = st.text_area("Your Query:", height=100)

    if st.button("Execute Query"):
        if query_input:
            with st.spinner("Generating SQL and querying database..."):
                result = db_query_agent.query_database_natural_language(query_input)
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                elif "columns" in result and "rows" in result:
                    df = pd.DataFrame(result["rows"], columns=list(result["columns"]))
                    st.success("Query executed successfully!")
                    st.dataframe(df)
                else:
                    st.info(result["message"])
        else:
            st.warning("Please enter a query.")

def show_user_profile_page():
    st.header("User Profile Page")
    if st.session_state.current_user:
        st.write(f"**Username:** {st.session_state.current_user.username}")
        st.write(f"**Google ID (Dummy):** {st.session_state.current_user.google_id}")
        st.write(f"**Settings (Dummy):** {st.session_state.current_user.settings}")
        st.subheader("Update Settings")
        new_setting_key = st.text_input("Setting Key", key="setting_key")
        new_setting_value = st.text_input("Setting Value", key="setting_value")
        if st.button("Save Setting", key="save_setting_button"):
            # Dummy save setting logic
            if new_setting_key and new_setting_value:
                if st.session_state.current_user.settings is None:
                    st.session_state.current_user.settings = {}
                st.session_state.current_user.settings[new_setting_key] = new_setting_value
                # In a real app, you would persist this change to the database
                st.success("Setting saved (dummy update).")
            else:
                st.warning("Please enter both key and value.")

        st.markdown("---")
        st.subheader("Danger Zone")
        if st.button("Delete Account", key="delete_account_button"):
            st.warning("Are you sure you want to delete your account? This action cannot be undone.")
            if st.button("Confirm Deletion", key="confirm_delete_button"):
                if st.session_state.current_user:
                    user_id_to_delete = st.session_state.current_user.id
                    if db.delete_user(user_id_to_delete):
                        st.success("Account successfully deleted.")
                        st.session_state.is_user_logged_in = False
                        st.session_state.current_user = None
                        st.rerun()
                    else:
                        st.error("Failed to delete account.")
    else:
        st.info("Please log in to view your profile.")

if __name__ == "__main__":
    if st.session_state.is_user_logged_in:
        show_main_app()
    else:
        login_screen()
