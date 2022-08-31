import streamlit as st
import snowflake_conn as sfc
import snowflakeRunner as dcr
import os
import time
import re
import requests

# Page settings
st.set_page_config(
    page_title="Connected App Assistant",
    page_icon="❄️️",
    layout="wide",
    initial_sidebar_state="expanded",
    # menu_items={
    #     'Get Help': '',
    #     'Report a bug': "",
    #     'About': "This app helps deploy and manage Connected Application!"
    # }
)


# Set up main page
col1, col2 = st.columns((6, 1))
col1.title("⚙️ Connected App Assistant")

sdcol1, sdcol2, sdcol3 = st.sidebar.columns([3,6,1])

with sdcol1:
    st.write("")

with sdcol2:
    st.image("assets/snow.png",width=100)

with sdcol3:
    st.write("")


st.sidebar.markdown("***")
action = st.sidebar.radio("What action would you like to take?", ("First Installation", "Maintenance"))
st.sidebar.markdown("***")

snowRunner = dcr.SnowflakeRunner()


# Build form based on selected action
if action == "First Installation":  
    varDict={}    
    st.subheader("First Installation")
    st.write("Simple application to generate a script based on parameterized templates. The form captures application specifics for customers and generate the installation script ready to run.")
    st.write("Templates are parameterized with that format '<My Variable>', you can also define possible values with list: <My List#1,2,3>")
    st.markdown("***")
    script_path=st.selectbox("Script Template",["https://raw.githubusercontent.com/sfc-gh-aalteirac/connected_app_assistant/main/sql_scripts/script_2.sql",
                                            "https://raw.githubusercontent.com/sfc-gh-aalteirac/connected_app_assistant/main/sql_scripts/script_1.sql"])
    rawsc = requests.get(script_path).text
    expander = st.expander("See Script Template...")
    script_mod=expander.text_area("",rawsc,disabled=False, height=len(rawsc.splitlines()*25))
    x=re.findall(r'<(.*?)>',script_mod)
    st.write("Generated Form:")
    with st.form("initial_deployment_form"):    
        for key in x:
            if '#' in key:
                lst=key.split("#")[1].split(",")
                lbl=key.split("#")[0]
                varDict[key]=st.selectbox(lbl,lst)
            else:    
                varDict[key]=st.text_input(key,placeholder='***'+key+'***')
        is_debug_mode = st.checkbox("Preview mode (generate scripts, but not run them)", True)
        submitted = st.form_submit_button("Deploy")
        if submitted:
            result_badge = st.empty()
            script_area= st.empty()
            with st.spinner("Generating Scripts..."):
                time.sleep(1)
                snowRunner.prepare_deployment(is_debug_mode,varDict,script_mod)
                retScript=snowRunner.execute_locally()
            if is_debug_mode:
                result_badge.success("Scripts Generated!")
            else:
                result_badge=st.success("App Deployed! (not yet...)")
            script_area.text_area("Script Preview:",retScript,disabled=True, height=300)

elif action == "Maintenance":
    st.subheader("Maintenance")

elif action == "Add Add'l Provider ☃️":
    # Form for adding providers
    st.subheader("❄️ Add Providers to Existing DCRs! ❄️")
    with st.form("additional_provider_form"):
        warehouse_size = st.selectbox("Which version does the Consumer have installed?",
                                   ["6.0 Native App", "5.5 Jinja", "5.5 SQL Param"])
        abbreviation = st.text_input("What database abbreviation does the Consumer use? (Leave blank for default)")
        consumer_nickname = st.selectbox("Which is the existing Consumer account?",
                                         st.session_state['account_nicknames'])
        provider_nickname = st.selectbox("Which is the new Provider account?", st.session_state['account_nicknames'])
        app_suffix = st.text_input("What suffix would you like for the Consumer-side app name? (Leave blank for "
                                   "default)")
        # Debug mode prevents actually running the script, but outputs the script contents
        is_debug_mode = st.checkbox("Run in debug mode (generate scripts, but not run them)", True)

        # Get accounts from session_state
        provider_index = st.session_state['account_nicknames'].index(provider_nickname)
        provider_account = st.session_state['accounts'][provider_index]
        consumer_index = st.session_state['account_nicknames'].index(consumer_nickname)
        consumer_account = st.session_state['accounts'][consumer_index]

        submitted = st.form_submit_button("Add Provider")

        if submitted:
            if provider_account == consumer_account:
                st.error("Provider and consumer cannot be the same account!")
            else:
                # Establish connections, if necessary
                if is_debug_mode:
                    provider_conn = None
                    consumer_conn = None
                else:
                    provider_conn = sfc.init_connection("account_" + str(provider_index + 1))
                    consumer_conn = sfc.init_connection("account_" + str(consumer_index + 1))

                if warehouse_size == "6.0 Native App":
                    if st.secrets["local_dcr_v6_path"] == "":
                        path = os.getcwd() + "/data-clean-room-tng/"
                    else:
                        path = st.secrets["local_dcr_v6_path"]
                elif warehouse_size == "5.5 Jinja" or warehouse_size == "5.5 SQL Param":
                    if st.secrets["local_dcr_v55_path"] == "":
                        path = os.getcwd() + "/data-clean-room/"
                    else:
                        path = st.secrets["local_dcr_v55_path"]

                with st.spinner("Adding Provider..."):
                    snowRunner.prepare_provider_addition(is_debug_mode, warehouse_size, provider_account,
                                                              provider_conn, consumer_account, consumer_conn,
                                                              abbreviation, app_suffix, path)
                    snowRunner.execute_locally()

                # Message dependent on debug or not
                if is_debug_mode:
                    st.success("Scripts Generated in Output!")
                else:
                    st.success("Provider Added!")
                st.snow()

elif action == "Upgrade 🧊":
    # Form for upgrading
    st.subheader("❄️ Upgrade Existing v5.5 DCRs to v6.0! ❄️")
    with st.form("upgrade_form"):
        new_abbreviation = st.text_input("What database abbreviation would you like for the **new** v6.0 DCR? (Leave "
                                         "blank for default)")
        old_abbreviation = st.text_input("What is the database abbreviation of the **old** v5.5 DCR? (Leave blank for "
                                         "default)")
        provider_nickname = st.selectbox("Which Provider account are you upgrading?",
                                         st.session_state['account_nicknames'])
        consumer_nickname = st.selectbox("Which Consumer account?",
                                         st.session_state['account_nicknames'])
        # Debug mode prevents actually running the script, but outputs the script contents
        is_debug_mode = st.checkbox("Run in debug mode (generate scripts, but not run them)", True)

        # Get accounts from session_state
        provider_index = st.session_state['account_nicknames'].index(provider_nickname)
        provider_account = st.session_state['accounts'][provider_index]
        consumer_index = st.session_state['account_nicknames'].index(consumer_nickname)
        consumer_account = st.session_state['accounts'][consumer_index]

        submitted = st.form_submit_button("Upgrade")

        if submitted:
            if provider_account == consumer_account:
                st.error("Provider and Consumer cannot be the same account!")
            elif new_abbreviation == old_abbreviation and (new_abbreviation != "" or old_abbreviation != ""):
                st.error("Old and new database abbreviation cannot match!")
            else:
                # Establish connections, if necessary
                if is_debug_mode:
                    provider_conn = None
                    consumer_conn = None
                else:
                    provider_conn = sfc.init_connection("account_" + str(provider_index + 1))
                    consumer_conn = sfc.init_connection("account_" + str(consumer_index + 1))

                if st.secrets["local_dcr_v6_path"] == "":
                    path = os.getcwd() + "/data-clean-room-tng/"
                else:
                    path = st.secrets["local_dcr_v6_path"]

                with st.spinner("Updating Clean Room..."):
                    snowRunner.prepare_upgrade(is_debug_mode, provider_account, provider_conn, consumer_account,
                                                    consumer_conn, new_abbreviation, old_abbreviation, path)
                    snowRunner.execute_locally()

                # Message dependent on debug or not
                if is_debug_mode:
                    st.success("Scripts Generated in Output!")
                else:
                    st.success("Clean Room Upgraded!")
                st.snow()

elif action == "Uninstall 💧":
    # Form for uninstalling
    st.subheader("❄️ Uninstall Existing DCRs! ❄️")
    st.warning("This action **drops** related shares and databases!")
    with st.form("initial_deployment_form"):
        warehouse_size = st.selectbox("Which version do you want to uninstall?",
                                   ["6.0 Native App", "5.5 Jinja", "5.5 SQL Param"])  # , "ID Resolution Native App"])
        abbreviation = st.text_input(
            "What database abbreviation would you like to uninstall? (Leave blank for default)")
        account_nickname = st.selectbox("Which account to uninstall?", st.session_state['account_nicknames'])
        account_type = st.selectbox("What is the account type for the account being uninstalled?", ["Consumer",
                                                                                                    "Provider"])

        consumer_accounts_options = st.session_state['account_nicknames']
        consumer_accounts_options.insert(0, "")
        consumer_nickname = st.selectbox("Which Consumer account (if uninstalling Provider)?",
                                         consumer_accounts_options)
        app_suffix = st.text_input("What suffix would you like for the Consumer-side app name? (Leave blank for "
                                   "default)")
        # Debug mode prevents actually running the script, but outputs the script contents
        is_debug_mode = st.checkbox("Run in debug mode (generate scripts, but not run them)", True)

        # Get accounts from session_state
        account_index = st.session_state['account_nicknames'].index(account_nickname)
        account = st.session_state['accounts'][account_index]
        if consumer_nickname != "":
            consumer_index = st.session_state['account_nicknames'].index(consumer_nickname) - 1
            consumer_account = st.session_state['accounts'][consumer_index]
        else:
            consumer_account = ""

        st.warning("Submitting while not in debug mode will **drop** related shares and databases")
        submitted = st.form_submit_button("Uninstall")

        if submitted:
            if account == consumer_account and account_type == "Provider":
                st.error("Provider and Consumer cannot be the same account!")
            else:
                # Establish connections, if necessary
                if is_debug_mode:
                    account_conn = None
                else:
                    account_conn = sfc.init_connection("account_" + str(account_index + 1))

                if warehouse_size == "6.0 Native App":
                    if st.secrets["local_dcr_v6_path"] == "":
                        path = os.getcwd() + "/data-clean-room-tng/"
                    else:
                        path = st.secrets["local_dcr_v6_path"]
                elif warehouse_size == "5.5 Jinja" or warehouse_size == "5.5 SQL Param":
                    if st.secrets["local_dcr_v55_path"] == "":
                        path = os.getcwd() + "/data-clean-room/"
                    else:
                        path = st.secrets["local_dcr_v55_path"]

                with st.spinner("Uninstalling Clean Room..."):
                    snowRunner.prepare_uninstall(is_debug_mode, warehouse_size, account_type, account, account_conn,
                                                      consumer_account, abbreviation, app_suffix, path)
                    snowRunner.execute_locally()

                # Message dependent on debug or not
                if is_debug_mode:
                    st.success("Scripts Generated in Output!")
                else:
                    st.success("Clean Room Uninstalled!")
                st.snow()
