#!/usr/bin/python3
import time
import altair as alt
import dataframe_funcs as ddf
import pandas as pd
import streamlit as st
from config import Config

my_tz = time.tzname[0]
#https://altair-viz.github.io/user_guide/faq.html#maxrowserror-how-can-i-plot-large-datasets
alt.data_transformers.disable_max_rows()

def draw_single_chart(df, property, width, hight,
                ylabelpadd=10, xlabelpadd=10):
    
    df['date'] = df['date'].dt.tz_localize(Config.timezone)

    tooltip=[
        alt.Tooltip(field="date",
        type="temporal",
        title="Time",
        format="%I:%M:%S %p",),
        alt.Tooltip(field=property,
        type="ordinal",),
        alt.Tooltip(field='file',
        type="ordinal",)
    ]

    tooltip1=[
        alt.Tooltip(field="date",
        type="temporal",
        title="Time",
        format="%I:%M:%S %p",),
        alt.Tooltip(field=property,
        type="ordinal",),
    ]

    if 'metric' in df.columns:
        tooltip = tooltip1
        color_item = 'metric'
        lsel = 'metric'
    else:
        color_item = 'file'
        lsel = 'file'


    selection = alt.selection_multi(fields=[lsel], bind='legend')
    color_x = alt.condition(selection,
                            alt.Color(f'{color_item}:N'),
                            alt.value('white',))

    opacity_x = alt.condition(selection, alt.value(1.0), alt.value(0))

    c = alt.Chart(df).mark_line(point=False, interpolate='natural').encode(
        alt.X(f'date:T',
              scale=alt.Scale(zero=False),
              axis=alt.Axis(domain=True, labelBaseline='line-top',
                            )),
                            #title=f'date {df.at[0,"file"]}')),
        alt.Y(property, scale=alt.Scale(zero=False),
              axis=alt.Axis(labelPadding=ylabelpadd,
                            titlePadding=5,
                            ),
              ),
        #tooltip=['date', property, 'file'],
        tooltip=tooltip,
        color=color_x,
        opacity=opacity_x,
    ).properties(
        width=width,
        height=hight,
    ).add_selection(selection).interactive()

    return(c)

def draw_single_chart_v1(df, property, restart_headers, os_details, width, hight,
                ylabelpadd=10, xlabelpadd=10):

    df['date'] = df['date'].dt.tz_localize(Config.timezone)
    rule_field, z_field, y_pos = create_reboot_rule(df, property, restart_headers, os_details)

    tooltip=[
        alt.Tooltip(field="date",
        type="temporal",
        title="Time",
        format="%I:%M:%S %p",),
        alt.Tooltip(field=property,
        type="ordinal",),
        alt.Tooltip(field='file',
        type="ordinal",)
    ]

    tooltip1=[
        alt.Tooltip(field="date",
        type="temporal",
        title="Time",
        format="%I:%M:%S %p",),
        alt.Tooltip(field=property,
        type="ordinal",),
    ]

    if 'metric' in df.columns:
        tooltip = tooltip1
        color_item = 'metric'
        lsel = 'metric'
    else:
        color_item = 'file'
        lsel = 'file'


    selection = alt.selection_multi(fields=[lsel], bind='legend')
    color_x = alt.condition(selection,
                            alt.Color(f'{color_item}:N'),
                            alt.value('white',))

    opacity_x = alt.condition(selection, alt.value(1.0), alt.value(0))

    c = alt.Chart(df).mark_line(point=False, interpolate='natural').encode(
        alt.X(f'date:T',
              scale=alt.Scale(zero=False),
              axis=alt.Axis(domain=True, labelBaseline='line-top',
                            )),
                            #title=f'date {df.at[0,"file"]}')),
        alt.Y(property, scale=alt.Scale(zero=False),
              axis=alt.Axis(labelPadding=ylabelpadd,
                            titlePadding=5,
                            ),
              ),
        #tooltip=['date', property, 'file'],
        tooltip=tooltip,
        color=color_x,
        opacity=opacity_x,
    ).properties(
        width=width,
        height=hight,
    ).add_selection(selection).interactive()

    reboot_text = return_reboot_text(z_field, y_pos)

    for rule in rule_field:
        c += rule

    if reboot_text: 
        c += reboot_text

    return(c)

def create_reboot_rule(df, property, restart_headers, os_details):
    y_pos = df[property].max()/2
    rule_field = []
    z_field = []
    for header in restart_headers:
        xval = header.split()[-1]
        date_str, format = ddf.format_date(os_details)
        z = pd.to_datetime(
            f'{date_str} {xval}', format=format)
        z_field.append(z)
        mdf = pd.DataFrame({'x': [z]})
        # apache arrows is displaying localtime hence we need to consider the 
        # actual timezone of the user displaying the data
        mdf['x_utc'] = mdf['x'].dt.tz_localize(my_tz)
        #rule = alt.Chart(pd.DataFrame({'x': [z]})).mark_rule(color='red').encode(
        rule = alt.Chart(mdf).mark_rule(color='red').encode(
            x=alt.X('x_utc', axis=alt.Axis(title='date')), size=alt.value(1), strokeDash=(alt.value([5, 5])))

        rule_field.append(rule)
    return rule_field, z_field, y_pos

def return_reboot_text(z_field, y_pos):
    if z_field:
        mdf = pd.DataFrame({'date': z_field, '': y_pos})
        mdf['date_utc'] = mdf['date'].dt.tz_localize(my_tz)
        reboot_text = alt.Chart(mdf).mark_text(
            text='RESTART', angle=90, color='black', fontSize=11).\
            encode(x='date_utc:T', y=':Q')
    else:
        reboot_text = None
    return reboot_text

def draw_multi_chart(charts, y_shared='independent', x_shared='independent', title=None):
    if charts:
        fin_obj = alt.layer(
            title=title,
        ).resolve_scale(
            size="shared",
            stroke="independent",
            y=y_shared,
            x=x_shared).resolve_scale(
                size="independent",
                x="shared",
                fill="independent",
                color="shared",
                strokeDash='shared',
                strokeWidth='shared',

            ).configure_legend(
                labelLimit=250,
            )
            
        for dia in charts:
            fin_obj = fin_obj + dia
        return(fin_obj).interactive()


def overview(df, restart_headers, os_details):
    rule_field, z_field, y_pos = create_reboot_rule(
        df, 'y', restart_headers, os_details)

    # set timezone for your app
    if not df['date'][0].tzinfo:
        df['date'] = df['date'].dt.tz_localize(Config.timezone, ambiguous=True)

    selection_new = alt.selection_multi(fields=['metrics'], bind='legend',)

    # Create a selection that chooses the nearest point & selects based on x-value
    # not working here
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date'], empty='none')

    color_x = alt.condition(selection_new,
                            alt.Color('metrics:N'),
                            alt.value('white',))

    tooltip = [
        alt.Tooltip(field="date",
                    type="temporal",
                    title="Time",
                    format="%I:%M:%S %p",),
        alt.Tooltip(field='metrics',
                    title='metric',
                    type="ordinal",),
        alt.Tooltip(field='y',
                    title='value',
                    type="ordinal",),
    ]
    opacity_x = alt.condition(selection_new, alt.value(1.0), alt.value(0))
    line = alt.Chart(df).mark_line(interpolate='linear').encode(
        alt.X('date:T'),
        alt.Y('y:Q'),
        opacity=opacity_x,
        color=color_x,
        tooltip=tooltip
    ).add_selection(
        selection_new
    ).properties(
        width=1200, height=400
    )

    #line.configure_legend(orient='left')

    for rule in rule_field:
        line += rule
    reboot_text = return_reboot_text(z_field, y_pos)
    if reboot_text:
        line += reboot_text

    return line.interactive()
