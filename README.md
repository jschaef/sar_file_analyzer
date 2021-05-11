# sar_file_analyzer
The app is using streamlit, altair, pandas and other great python modules   
for graphical presentation of various metrics from ascii sar files.

## requirements
* pyhton3 
* python3x-pip* 
* sar files with '.' as decimal separator (LC_NUMERIC en,us)
* 8GB RAM for better user experience

## build
* <code>python -m venv venv</code> 
* <code>source venv/bin/activate</code> 
* <code>pip install -U pip</code>
* <code>pip install six appdirs packaging ordered-set</code>
* <code>pip install -r requirements.txt</code>
* <code>install nodejs-common via your package manager (you need the npm binary)</code>
* <code>npm install vega-lite vega-cli canvas</code>

## configure
* edit config.py
## run
* <code>streamlit run first_st.py</code>

## access
* open a webbrowser and navigate to the page displayed before
* username admin/password
* change password of admin
* upload your first sar file "Manage Sar Files"

## note
Newer versions of sar_file_analyzer may rely on the latest streamlit version.   
Such when pulling the newest git changes it might be that it is not working
within your old virtual environment.   
In this case do a <code>pip install -U streamlit</code>
