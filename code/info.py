#!/usr/bin/python3

import streamlit as st

def info():
    st.header("Info Page")
    st.markdown('The SAR Analyzer page has been written due to limitations of\
        already existing graphical tools for exploring SAR data. And also \
        due to lack of programming skills in _C/Java/QT_ of the author to contribute to the existing once.')
        
    st.markdown('Such at least we are independent from other projects :blush: .')

    st.subheader('Used languages/frameworks:')
    st.markdown( """* Python version 3 - https://www.python.org/  
        Python is the programing language used for the sar parser and  
        in general used for all aspects of this page""")
    
    st.markdown("""* Streamlit - https://www.streamlit.io/  
        A fast prototyping framework for creating web apps without the need
        to know much about html and javascript""")

    st.markdown("""* Altair - https://altair-viz.github.io/  
        Altair is a declarative statistical visualization library for Python.    
        It is used for drawing the diagrams""")

    st.markdown("""* Pandas - https://pandas.pydata.org/.  
        pandas is a fast, powerful, flexible and easy to use open source data analysis and manipulation tool,
built on top of the Python programming language. Used as easy to compute format of the sar data in this context""" )

    st.markdown("""* Miscelaneous - sqlalchemy, reddis """)

def usage():
    st.header("FAQ")
    st.markdown("""___How can I reset my password?___  
        Not implemented at the moment. But planned.""")
    st.markdown("""__What can I do with diagrams?__   
        There are some features with this diagrams which are not visible in the first place.
        E.g if you scroll inside a diagram you will change the dimension. You could also click
        and move which will vertically/horizontally move the diagram. At the right side you can save
        the diagram. There is also a button to maximize it.
        """)
    st.markdown("""__Can I save a diagram as PDF?__  
        Not at the moment. I'm relying on the features supported by streamlit/altair. Which 
        do not easily support it at the moment.""")
    st.markdown("""__Can this app be containerized?__  
        Yes please - do it.""")

    st.markdown("""___Why does it need time during the first analyses?___  
        When computing a sar file the first time it will be parsed and serialized into 
        a compressed format (python pickled). The parser needs to create a re-usable data
        structure which serves afterwards any time a new view is requested.
        The drawback of streamlit is that each action on a page initiates a whole reload of the page.
        This means that the sar data would be recalculated each time after a user action. With a sar file of about 
        200 MB this process takes about 30 seconds. This would make the app unusable. Pickled data is much
        smaller. The relation is about 1:8. To speed up the web experience I save the preformated data structure
        into picle format on disk or within reddis. Next time the data needs to be presented it loads 
        the ready to use pickled data structure only. Only a few calculations are needed to finally present the data.""")
    
    st.markdown("""___Whom to contact in case of an error?___  
        jochen.schaefer@suse.com via email or ping me on teams.""")