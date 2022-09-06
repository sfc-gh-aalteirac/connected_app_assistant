import streamlit as st
import snowflake_conn as sfc
import snowflakeRunner as sfc
import snowflake_conn as sf_con
import os
import time
import re
import requests
import extra_streamlit_components as stx
import datetime

st.set_page_config(
    page_title="Connected App Assistant",
    page_icon="❄️️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.cache(allow_output_mutation=True)
def get_manager():
    return stx.CookieManager()

def getCookies(key):
    ret=None
    try:
        ret=cookie_manager.get(cookie=key)
    except Exception as ex:
       ret= None
    return ret   



cookie_manager = get_manager()

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
action = st.sidebar.radio("What action would you like to take?", ("Setup Snowflake Account","First Installation", "Maintenance"))
st.sidebar.markdown("***")

snowRunner = sfc.SnowflakeRunner()


if action == "Setup Snowflake Account": 
    st.subheader("Snowflake Account Informations")

    with st.form("acc"): 
        if getCookies("acc") is None: acc=st.text_input("Account",placeholder='***Account ID***') 
        else: acc=st.text_input("Account",value=getCookies("acc"))
        if getCookies("usr") is None: usr=st.text_input("User",placeholder='***User Name***') 
        else: usr=st.text_input("User",value=getCookies("usr"))
        if getCookies("passw") is None: passw=st.text_input("Password",placeholder='***Password***',)
        else: passw=st.text_input("Password",value=getCookies("passw"),type="password")
        if getCookies("ware") is None: ware=st.text_input("Warehouse",placeholder='***Warehouse***')
        else: ware=st.text_input("Warehouse",value=getCookies("ware"))
        
        valid=st.form_submit_button("Validate")
        result_badge = st.empty()
        if valid:
            snowconn = sf_con.init_connection({"user":usr,"password":passw,"account":acc,"warehouse":ware})

            if type(snowconn) is not str:
                result_badge.success("Connected!" )
                st.session_state.snow_session=snowconn
            else:
                result_badge.error("Something goes wrong... " + snowconn)
    expire=datetime.datetime(year=2028, month=2, day=2)    
    cookie_manager.set('acc', acc,key="acc",expires_at=expire) 
    cookie_manager.set('usr', usr,key="usr",expires_at=expire) 
    cookie_manager.set('passw', passw,key="passw",expires_at=expire)  
    cookie_manager.set('ware', ware,key="ware",expires_at=expire)      
                   
if action == "First Installation":  
    print(st.session_state.snow_session)
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
            st.snow()
elif action == "Maintenance":
    st.subheader("Maintenance")


 