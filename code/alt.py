#!/usr/bin/python3
import altair as alt
import dataframe_funcs as ddf
import pandas as pd
import streamlit as st

#https://altair-viz.github.io/user_guide/faq.html#maxrowserror-how-can-i-plot-large-datasets
alt.data_transformers.disable_max_rows()

def draw_single_chart(df, property, width, hight,
                ylabelpadd=10, xlabelpadd=10):
    

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

            )
            
        for dia in charts:
            fin_obj = fin_obj + dia
        return(fin_obj).interactive()

def overview(df):
    # js

    selection = alt.selection_multi(fields=['metrics'], bind='legend',)
    color_x = alt.condition(selection,
                            alt.Color('metrics:N'),
                            alt.value('white',))

    opacity_x = alt.condition(selection, alt.value(1.0), alt.value(0))

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date'], empty='none')


    selectors = alt.Chart(df).mark_point().encode(
        x='date:T',
        opacity=alt.value(0),
    ).add_selection(
        nearest, selection
    )

    line = alt.Chart(df).mark_line(interpolate='natural').encode(
        alt.X('date:T',),
        y='y:Q',
        color=color_x,
        opacity = opacity_x,
    )

    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, 'y:Q', alt.value(' '))
    )

    # Draw a rule at the location of the selection
    rules = alt.Chart(df).mark_rule(color='gray').encode(
        x='date:T',
    ).transform_filter(
        nearest
    )

    return alt.layer(
        line.interactive(), selectors, points, rules, text
    ).properties(
        width=800, height=400
    )

def overview_v1(df):
    selection_new = alt.selection_multi(fields=['metrics'], bind='legend',)

    # Create a selection that chooses the nearest point & selects based on x-value
    # not working here
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date'], empty='none')

    # Draw a rule at the location of the selection
    # not working here
    rules=alt.Chart(df).mark_rule(color='gray').encode(
        x='date:T',
    ).transform_filter(
        nearest
    )

    color_x = alt.condition(selection_new,
                            alt.Color('metrics:N'),
                            alt.value('white',))

    tooltip = [
        alt.Tooltip(field="date",
                    type="temporal",
                    title="Time",
                    format="%I:%M:%S %p",),
        alt.Tooltip(field='metrics',
                    title = 'metric',
                    type="ordinal",),
        alt.Tooltip(field='y',
                    title='value',
                    type="ordinal",),
    ]


    opacity_x = alt.condition(selection_new, alt.value(1.0), alt.value(0))
    line = alt.Chart(df).mark_line(interpolate='linear').encode(
        alt.X('date:T'),
        alt.Y('y:Q'),
        opacity = opacity_x,
        color = color_x,
        tooltip = tooltip
    ).add_selection(
        selection_new
    ).properties(
        width=800, height=400
    )
    return(line.interactive())
    # not working
    return alt.layer(
        line.interactive(), rules
    ).properties(
        width=800, height=400
    )

def overview_v2(df, restart_headers, os_details):
    # position for reboot text
    y_pos = df['y'].max()/2
    rule_field = []
    z_field = []
    for header in restart_headers:
        xval = header.split()[-1]
        date_str, format = ddf.format_date(os_details)
        z = pd.to_datetime(
            f'{date_str} {xval}', format=format)
        z_field.append(z)
        rule = alt.Chart(pd.DataFrame({'x': [z]})).mark_rule(color='black').encode(
            x='x', size=alt.value(1), strokeDash=(alt.value([5,5])))
        
        rule_field.append(rule)

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

    for rule in rule_field:
        line += rule

    reboot_text = alt.Chart(pd.DataFrame({'Date': z_field, 'y': y_pos})).mark_text(
        text='RESTART', angle=90, color='black', fontSize=11).encode(x='Date:T', y='y:Q'
    )
    line += reboot_text

    return line.interactive()
