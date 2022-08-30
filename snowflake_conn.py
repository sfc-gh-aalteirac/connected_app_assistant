import streamlit as st
import snowflake.connector as sf
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# Loads private key
pkb = ""

if st.secrets["local_key_path"] != "":
    with open(st.secrets["local_key_path"], "rb") as key:
        p_key = serialization.load_pem_private_key(
            key.read(),
            password=os.environ['PRIVATE_KEY_PASSPHRASE'].encode(),
            backend=default_backend()
        )

    # Stores public key
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())


# Initialize connection
# Uses st.experimental_singleton to only run once
@st.experimental_singleton
def init_connection(account):
    if pkb != "":
        return sf.connect(**st.secrets[account], private_key=pkb)
    else:
        return sf.connect(**st.secrets[account])
