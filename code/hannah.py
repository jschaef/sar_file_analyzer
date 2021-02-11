import time
from threading import Thread
import streamlit as st
import altair as alt
import pandas as pd

col_names = ['Volume', 'Stromstärke']
volvals = [ 2.294, 3.13, 4.01, 5.012, 6.002, 7.016, 7.546, 7.602, 7.816, 7.912, 8.00 ]
strvals = [-0.052 ,-0.052 ,-0.052 ,-0.052 ,-0.053 ,-0.053 ,-0.053 ,-0.06 ,-0.071 ,-0.101 ,-0.111 ]
x = zip(volvals, strvals)



def draw_single_chart(df, property, x_labels, width, hight, color='red',
                      ylabelpadd=10, xlabelpadd=10):
    selection = alt.selection_multi(fields=['Stromstärke'], bind='legend')

    #domain_x = alt.condition(selection, alt.AxisConfig(disable=True), alt.AxisConfig(disable=False))

    c = alt.Chart(df).mark_line(point=True, interpolate='natural', ).encode(
        x='Volume:Q',
        y='Stromstärke:Q'
       
    ).properties(
        width=width,
        height=hight,
    ).interactive()
    return c

data = [[y[0], y[1]] for y in x]

df = pd.DataFrame(data, index=strvals, columns=col_names,)
df['Stromstärke'].reset_index()
st.write(draw_single_chart(df, 'Volume', volvals, 800, 400))


class Sleepy(Thread):

    def run(self):
        time.sleep(5)
        print("Hello from Thread")


t = Sleepy()
t1 = Sleepy()
t2 = Sleepy()
t.start()      # start method automatic call Thread class run method.
t1.start()
t2.start()
# print 'The main program continues to run in foreground.'
t.join()
t1.join()
t2.join()
st.write("The main program continues to run in the foreground.")
