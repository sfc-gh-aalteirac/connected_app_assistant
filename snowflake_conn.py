import streamlit as st
import snowflake.connector as sf
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


# @st.experimental_singleton
def init_connection(cred):
    try:
        return sf.connect(**cred)
    except Exception as ex:
        return f"Some error you don't know how to handle {ex}"


