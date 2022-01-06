#!/usr/bin/python3
import time
import altair as alt
from altair.vegalite.v4.schema.channels import Opacity, StrokeWidth
import dataframe_funcs as ddf
import pandas as pd
import streamlit as st
from config import Config

my_tz = time.tzname[0]
#https://altair-viz.github.io/user_guide/faq.html#maxrowserror-how-can-i-plot-large-datasets
alt.data_transformers.disable_max_rows()

def draw_single_chart(df, property, width, hight,
                ylabelpadd=10, xlabelpadd=10):
    
    df['date'] = df['date'].dt.tz_localize('UTC', ambiguous=True)

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
        alt.X('utchoursminutes(date)', type='temporal',
              scale=alt.Scale(zero=False),
              axis=alt.Axis(domain=True, labelBaseline='line-top',
                    title='date')),
        alt.Y(property, scale=alt.Scale(zero=False),
              axis=alt.Axis(labelPadding=ylabelpadd,
                            titlePadding=5,
                            ),
              ),
        #tooltip=tooltip,
        color=color_x,
        opacity=opacity_x,
    ).properties(
        width=width,
        height=hight,
    ).add_selection(selection).interactive()

    return(c)

def draw_single_chart_v9(df, property, restart_headers, os_details, width, hight,
                ylabelpadd=10, xlabelpadd=10):

    df['date'] = df['date'].dt.tz_localize('UTC', ambiguous=True)
    rule_field, z_field, y_pos = create_reboot_rule(df, property, restart_headers, os_details)

    tooltip=[
        alt.Tooltip(field="date",
        type="temporal",
        title="Time",
        format="%I:%M:%S %p",
        timeUnit="hoursminutes"
        ),
        alt.Tooltip(field=property,
        type="ordinal",),
        alt.Tooltip(field='file',
        type="ordinal",)
    ]

    tooltip1=[
        alt.Tooltip(field="date",
        type="temporal",
        title="Time",
        format="%I:%M:%S %p",
        timeUnit="utchoursminutes"
        ),
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
        alt.X('utchoursminutes(date)', type='temporal',
              scale=alt.Scale(zero=False),
              axis=alt.Axis(domain=True, labelBaseline='line-top',
                title='date')),
        alt.Y(property, scale=alt.Scale(zero=False),
              axis=alt.Axis(labelPadding=ylabelpadd,
                            titlePadding=5,
                            ),
              ),
        #tooltip=tooltip,
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

def draw_single_chart_v1(df, property, restart_headers, os_details, width, hight,
                         ylabelpadd=10, xlabelpadd=10):

    #df['date'] = df['date'].dt.tz_localize('UTC', ambiguous=True)
    rule_field, z_field, y_pos = create_reboot_rule(
        df, property, restart_headers, os_details)

    if 'metric' in df.columns:
        color_item = 'metric'
    else:
        color_item = 'file'

    #selection = alt.selection_multi(fields=[color_item], bind='legend')
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date'], empty='none')

    selectors = alt.Chart(df).mark_point().encode(
        alt.X('utchoursminutes(date)', type='temporal'),
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )

    c = alt.Chart(df).mark_line(point=False, interpolate='natural').encode(
        alt.X('utchoursminutes(date)', type='temporal',
              scale=alt.Scale(zero=False),
              axis=alt.Axis(domain=True, labelBaseline='line-top',
                            title='date')),
        alt.Y(property, scale=alt.Scale(zero=False),
              axis=alt.Axis(labelPadding=ylabelpadd,
                            titlePadding=5,
                            ),
              ),
        color=f'{color_item}:N'
    ).properties(
    width = width,
    height = hight,
    )

    rules = alt.Chart(df).mark_rule(color='gray').encode(
        alt.X('utchoursminutes(date)', type='temporal'),
    ).transform_filter(
        nearest
    )

    points = c.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    text = c.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, f'{property}:Q', alt.value(' '))
    )
    
    reboot_text = return_reboot_text(z_field, y_pos)

    for rule in rule_field:
        c += rule

    if reboot_text:
        c += reboot_text
    mlayer = alt.layer(c, selectors,points, rules, text, ).interactive()
    return(mlayer)



def create_reboot_rule(df, property, restart_headers, os_details):
    y_pos = df[property].max()/2
    rule_field = []
    z_field = []
    for header in restart_headers:
        xval = header.split()[-1]
        date_str, format = ddf.format_date(os_details)
        z = pd.to_datetime(
            f'{date_str} {xval}', format=format)
        z = z.tz_localize('UTC')
        z_field.append(z)
        mdf = pd.DataFrame({'x': [z]})
        rule = alt.Chart(mdf).mark_rule(color='red').encode(
             x=alt.X('utchoursminutes(x)', type='temporal', axis=alt.Axis(title='date')), 
             size=alt.value(2), strokeDash=(alt.value([5, 5])))

        rule_field.append(rule)
    return rule_field, z_field, y_pos

def return_reboot_text(z_field, y_pos):
    if z_field:
        mdf = pd.DataFrame({'date': z_field, '': y_pos})
        reboot_text = alt.Chart(mdf).mark_text(
            text='RESTART', angle=90, color='black', fontSize=12).\
            encode(alt.X('utchoursminutes(date)', type='temporal'), y=':Q')
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
    df['date_utc'] = df['date'].dt.tz_localize('UTC')
    rule_field, z_field, y_pos = create_reboot_rule(
        df, 'y', restart_headers, os_details)

    selection_new = alt.selection_multi(fields=['metrics'], bind='legend',)

    color_x = alt.condition(selection_new,
                           alt.Color('metrics:N'),
                            alt.value('white',))

    tooltip = [
        alt.Tooltip(field="date_utc",
                    type="temporal",
                    title="Time",
                    format="%I:%M:%S %p",
                    timeUnit="utchoursminutes",),
        alt.Tooltip(field='metrics',
                    title='metric',
                    type="ordinal",),
        alt.Tooltip(field='y',
                    title='value',
                    type="ordinal",),
    ]  
    #opacity_x = alt.condition(selection_new, alt.value(1.0), alt.value(0))
    line = alt.Chart(df).mark_line(interpolate='linear').encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
        alt.Y('y:Q'),
    #    opacity=opacity_x,
        #color=color_x,
        color='metrics:N'
        #tooltip=tooltip
#    ).add_selection(
#        selection_new
    ).properties(
        width=1200, height=400
    )
 
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date'], empty='none')

    selectors = alt.Chart(df).mark_point().encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )

    rules = alt.Chart(df).mark_rule(color='gray').encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
    ).transform_filter(
        nearest
    )

    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    text = line.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, 'y:Q', alt.value(' '))
    )

    #line.configure_legend(orient='left')

    for rule in rule_field:
        line += rule
    reboot_text = return_reboot_text(z_field, y_pos)
    if reboot_text:
        line += reboot_text

    mlayer = alt.layer(line, selectors, rules, points, text)
    return mlayer.interactive()


def overview_v1(df, restart_headers, os_details):
    df['date_utc'] = df['date'].dt.tz_localize('UTC')
    rule_field, z_field, y_pos = create_reboot_rule(
        df, 'y', restart_headers, os_details)

    selection_new = alt.selection_multi(fields=['metrics'])

    color_x = alt.condition(selection_new,
                            alt.Color('metrics:N', legend=None),
                            alt.value(''))

    opacity_x = alt.condition(selection_new, alt.value(1.0), alt.value(0))
    line = alt.Chart(df).encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
        alt.Y('y:Q'),
        opacity = opacity_x
    ).properties(
        width=1200, height=400
    )

    final_line = line.mark_line(strokeWidth=2).add_selection(selection_new).encode(
        color=color_x
    )
    
    legend = alt.Chart(df).mark_point().encode(
        y=alt.Y('metrics:N', axis=alt.Axis(orient='right')),
        color=color_x
    ).add_selection(
        selection_new
    )

    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date'], empty='none')

    selectors = alt.Chart(df).mark_point().encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )

    rules = alt.Chart(df).mark_rule(color='gray').encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
    ).transform_filter(
        nearest
    )

    xpoints = alt.Chart(df).mark_point().encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
        alt.Y('y:Q',),
        opacity=alt.condition(selection_new, alt.value(1), alt.value(0)),
        color=color_x
    ).transform_filter(
        nearest
    )

    tooltip_text = line.mark_text(
        align = "left",
        dx = -30,
        dy = -15,
        fontSize = 11,
        lineBreak = "\n",
    ).encode(
        text = alt.condition(nearest, 
        alt.Text('y:Q',),
        alt.value(' '),
    ),
        opacity=alt.condition(selection_new, alt.value(1), alt.value(0)),
        color = color_x
    )


    for rule in rule_field:
        line += rule
    reboot_text = return_reboot_text(z_field, y_pos)
    if reboot_text:
        line += reboot_text
    #line = line + selectors + rules + xpoints
    mlayer = alt.layer(final_line, selectors, rules, xpoints, tooltip_text).interactive()
    mlayer = mlayer|legend
    return mlayer
    #return mlayer.interactive()

