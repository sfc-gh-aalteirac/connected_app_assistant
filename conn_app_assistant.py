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

@st.cache(allow_output_mutation=True)
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()
def getCookies(key):
    ret=None
    try:
        ret=cookie_manager.get(cookie=key)
    except Exception as ex:
       ret= None
    return ret   

def logout():
    del st.session_state.connected
    del st.session_state.snow_session

def setCookies():
    expire=datetime.datetime(year=2024, month=2, day=2)   
    with st.empty():
        cookie_manager.set('acc', st.session_state.account,key="acc",expires_at=expire) 
        cookie_manager.set('usr', st.session_state.user,key="usr",expires_at=expire) 
        cookie_manager.set('passw', st.session_state.password,key="passw",expires_at=expire)  
        cookie_manager.set('ware', st.session_state.warehouse,key="ware",expires_at=expire) 

def connect():
    lst=[]
    if 'connected' not in st.session_state or st.session_state.connected==0:
        snowconn = sf_con.init_connection({"user":st.session_state.user,"password":st.session_state.password,"account":st.session_state.account})
        st.session_state.snow_session=snowconn  
    if type(st.session_state.snow_session) is not str:
        st.session_state.connected=1
    else:
        st.session_state.error="Something goes wrong... " + st.session_state.snow_session
        st.session_state.connected=0
        return    
    cur = st.session_state.snow_session.cursor()
    cur.execute('SHOW WAREHOUSES')
    for (name) in cur:
        lst.append(name[0])
    cur.close() 
    st.session_state.list_ware=lst
    # setCookies()
    # st.stop()

def initLayout():
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
    global action
    action = st.sidebar.radio("What action would you like to take?", ("Setup Snowflake Account","First Installation", "Maintenance"))
    st.sidebar.markdown("***")

initLayout()
snowRunner = sfc.SnowflakeRunner()

def populateForm(disabled):
    global ware, result_badge
    if getCookies("acc") is None: st.session_state.account=st.text_input("Account",placeholder='***Account ID***',disabled=disabled) 
    else: st.session_state.account=st.text_input("Account",value=getCookies("acc"),disabled=disabled)
    if getCookies("usr") is None: st.session_state.user=st.text_input("User",placeholder='***User Name***',disabled=disabled) 
    else: st.session_state.user=st.text_input("User",value=getCookies("usr"),disabled=disabled)
    if getCookies("passw") is None: st.session_state.password=st.text_input("Password",placeholder='***Password***',type='password',disabled=disabled)
    else: st.session_state.password=st.text_input("Password",value=getCookies("passw"),type="password",disabled=disabled)
    if getCookies("ware") is None: 
        ware=""
    else: 
        ware=getCookies("ware")
    st.session_state.warehouse=ware
    

if action == "Setup Snowflake Account": 
    st.subheader("Snowflake Account Informations")
    cookie_manager.get_all()
    print("A") 
    if "connected" in st.session_state and st.session_state.connected==1:
        print("B") 
        populateForm(True)
        wh=st.empty()
        if(ware==""):
            st.session_state.warehouse=wh.selectbox("warehouse",st.session_state.list_ware) 
        else:
            st.session_state.warehouse=wh.selectbox("warehouse",st.session_state.list_ware,index=st.session_state.list_ware.index(ware))   
        result_badge = st.empty()
        result_badge.success("Connected!" )
        logout=st.button("Logout",on_click=logout)
        setCookies()
    else:
        populateForm(False)
        wh=st.empty()
        lst=[ware]
        st.session_state.warehouse=wh.selectbox("warehouse",lst,disabled=True) 
        if(st.session_state.get("error") is not None):
            result_badge = st.empty()
            result_badge.error(st.session_state.get("error"))
            del st.session_state.error
        valid=st.button("Connect",on_click=connect)
               
                   
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


 