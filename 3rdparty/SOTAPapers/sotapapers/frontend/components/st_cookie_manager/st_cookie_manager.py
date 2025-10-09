import os
import streamlit.components.v1 as components

_RELEASE = True  # Change to False for development

if not _RELEASE:
    _component_func = components.declare_component(
        "st_cookie_manager",
        url="http://localhost:3001",  # Frontend development server
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("st_cookie_manager", path=build_dir)

def get_cookie(cookie_name: str):
    """
    Get a cookie value from the browser.
    """
    return _component_func(key=cookie_name, name=cookie_name, default=None)

def set_cookie(cookie_name: str, value: str, expires_days: int = 30):
    """
    Set a cookie value in the browser.
    """
    return _component_func(key=cookie_name, name=cookie_name, value=value, expires=expires_days, default=None)

def delete_cookie(cookie_name: str):
    """
    Delete a cookie from the browser.
    """
    return _component_func(key=cookie_name, name=cookie_name, value="", expires=0, default=None) 