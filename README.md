# sar_file_analyzer
The app is using streamlit, altair, pandas and other great python modules   
for graphical presentation of various metrics from ascii sar files.

## live demo
you might have a look here:
https://share.streamlit.io/jschaef/sar_file_analyzer/main/code/first_st.py.
Create your own account and upload a sar file or use admin/password

## requirements
* pyhton3 
* python3x-pip* 
* python3x-tk*
* sar files with '.' as decimal separator (LC_NUMERIC en,us)
* 8GB RAM for better user experience

## build
* <code>python3x -m venv venv</code> 
* <code>source venv/bin/activate</code> 
* <code>pip install -U pip</code>
* <code>pip install -r requirements.txt</code>
* <code>install nodejs-common via your package manager (you need the npm binary)</code>
* <code>npm install vega-lite vega-cli canvas</code>

## configure
* edit config.py
* edit code/.streamlit/config.toml
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

## configuring streamlit
below a sample config.toml. Put it into code/.streamlit/config.toml
```
[global]
dataFrameSerialization = "legacy"

[server]
maxUploadSize = 300

[theme]
primaryColor="#6eb52f"
backgroundColor="#f0f0f5"
secondaryBackgroundColor="#e0e0ef"
textColor="#262730"
font="sans serif"
```

## bugs
In case the app is throwing an error about helpers.py line 381 <code>format(precision=4)</code>
correct it to <code>set_precision(4)</code>.
Depending on the pandas version the second one is deprecated but the first one still not known.
