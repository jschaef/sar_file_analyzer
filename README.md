# sar_file_analyzer
The app is using streamlit, altair, pandas and other great python modules   
for graphical presentation of various metrics from ascii sar files.

## requirements
* pyhton3 
* python3x-pip* 
* sar files with '.' as decimal separator (LC_NUMERIC en,us)
* 8GB RAM for better user experience

## build
* python -m venv venv 
* source venv/bin/activate 
* pip install -U pip 
* pip install six appdirs packaging ordered-set
* pip install -r requirements.txt 
* install nodejs-common via your package manager (you need the npm binary) 
* npm install vega-lite vega-cli canvas

## configure
* edit config.py
## run
* streamlit run first_st.py

## access
* open a webbrowser and navigate to the page displayed before
* username admin/password
* change password of admin
* upload your first sar file "Manage Sar Files"
