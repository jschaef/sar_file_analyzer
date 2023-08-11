#!/usr/bin/python3
import time
import altair as alt
import dataframe_funcs as ddf
import pandas as pd

my_tz = time.tzname[0]
#https://altair-viz.github.io/user_guide/faq.html#maxrowserror-how-can-i-plot-large-datasets
alt.data_transformers.disable_max_rows()

def draw_single_chart_v1(df, property, restart_headers, os_details, width, hight,
                         ylabelpadd=10, font_size=None, title=None):

    #df['date'] = df['date'].dt.tz_localize('UTC', ambiguous=True)
    df['date_utc'] = df['date'].dt.tz_localize('UTC')
    rule_field, z_field, y_pos = create_reboot_rule(
        df, property, restart_headers, os_details)

    if 'metric' in df.columns:
        color_item = 'metric'
    else:
        color_item = 'file'

    nearest = alt.selection_point(nearest=True, on='mouseover',
                            fields=['date_utc'], empty=False)

    selectors = alt.Chart(df).mark_point().encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
        opacity=alt.value(0),
    ).add_params(
        nearest
    )

    c = alt.Chart(df).mark_line(point=False, interpolate='natural').encode(
        alt.X('utchoursminutes(date_utc)', type='temporal',
              scale=alt.Scale(zero=True),
              axis=alt.Axis(domain=True, labelBaseline='line-top',
                            title='date')),
        alt.Y(property, scale=alt.Scale(zero=False),
              axis=alt.Axis(labelPadding=ylabelpadd,
                            titlePadding=5,
                            ),
              ),
        color=alt.Color(f'{color_item}:N', legend=None)
    ).properties(
    width = width,
    height = hight,
    title=title
    )

    legend = alt.Chart(df).mark_point().encode(
        y=alt.Y(f'{color_item}:N', axis=alt.Axis(orient='right')),
        color=alt.Color(f'{color_item}:N',)
    )


    rules = alt.Chart(df).mark_rule(color='gray').encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
    ).transform_filter(
        nearest
    )

    points = c.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    text = c.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, f'{property}:Q', alt.value(' '))
    )
    
    reboot_text = return_reboot_text(z_field, y_pos, col='dummy', col_value='dummy')
    if reboot_text:
        reboot_text = reboot_text.encode(
        color=alt.Color('dummy:N', legend=None)
    )

    for rule in rule_field:
        rule = rule.encode(
            color=alt.Color('dummy:N', legend=None)
        )
        c += rule

    if reboot_text:
        c += reboot_text
    mlayer = alt.layer(c, selectors,points, rules, text, ).interactive()
    return (mlayer | legend
            ).configure_axis(
        labelFontSize=font_size,
        titleFontSize=font_size,
    ).configure_title(fontSize=font_size)

def create_reboot_rule(df, property, restart_headers, os_details, col=None, col_value=None):
    y_pos = df[property].max()/2
    rule_field = []
    z_field = []
    for header in restart_headers:
        xval = header.split()[-1]
        date_str, format = ddf.format_date(os_details)
        z = pd.to_datetime(
            f'{date_str} {xval}', format="mixed")
        z = z.tz_localize('UTC')
        z_field.append(z)
        if col is None:
            col = 'dummy'
        mdf = pd.DataFrame({'x': [z], col:col_value})
        rule = alt.Chart(mdf).mark_rule(color='red').encode(
             x=alt.X('utchoursminutes(x)', type='temporal', axis=alt.Axis(title='date')), 
             size=alt.value(2), strokeDash=(alt.value([5, 5])))

        rule_field.append(rule)
    return rule_field, z_field, y_pos

def return_reboot_text(z_field, y_pos, col=None, col_value=None):
    if z_field:
        mdf = pd.DataFrame({'date': z_field, 'y': y_pos, col:col_value})
        reboot_text = alt.Chart(mdf).mark_text(
            text='RESTART', angle=90, color='black', fontSize=12).\
            encode(alt.X('utchoursminutes(date)', type='temporal'), y=':Q',
                   )
    else:
        reboot_text = None
    return reboot_text

def overview_v1(df, restart_headers, os_details, font_size=None, width=None, height=None,
        title=None):
    df['date_utc'] = df['date'].dt.tz_localize('UTC')
    rule_field, z_field, y_pos = create_reboot_rule(
        df, 'y', restart_headers, os_details)

    selection_new = alt.selection_point(fields=['metrics'])

    color_x = alt.condition(selection_new,
                            alt.Color('metrics:N', legend=None),
                            alt.value(''))

    opacity_x = alt.condition(selection_new, alt.value(1.0), alt.value(0))
    line = alt.Chart(df).encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
        alt.Y('y:Q'),
        opacity = opacity_x
    ).properties(
        width=width, height=height,
        title=title
    )

    final_line = line.mark_line(strokeWidth=2).add_params(selection_new).encode(
        color=color_x
    )
    
    legend = alt.Chart(df).mark_point().encode(
        y=alt.Y('metrics:N', axis=alt.Axis(orient='right')),
        color=color_x
    ).add_params(
        selection_new
    )

    nearest = alt.selection_point(nearest=True, on='mouseover',
                            fields=['date'], empty=False)

    selectors = alt.Chart(df).mark_point().encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
        opacity=alt.value(0),
    ).add_params(
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
        fontSize = font_size,
        lineBreak = "\n",
    ).encode(
        text = alt.condition(nearest, 
        alt.Text('y:Q'),
        alt.value(' '),
    ),
        opacity=alt.condition(selection_new, alt.value(1), alt.value(0)),
        color = color_x
    )
    for rule in rule_field:
        rule = rule.encode(
            color=alt.Color('dummy:N', legend=None)
        )

        final_line += rule
    reboot_text = return_reboot_text(
        z_field, y_pos, col='dummy', col_value='dummy')

    if reboot_text:
        reboot_text = reboot_text.encode(
            color=alt.Color('dummy:N', legend=None)
        )

        final_line += reboot_text
    
    mlayer = alt.layer(final_line, selectors, rules,  tooltip_text).interactive()
    #mlayer = mlayer|legend
    mlayer = alt.hconcat(mlayer, legend).configure_concat(
        spacing=50
    )
    return mlayer.configure_axis(
        labelFontSize=font_size,
        titleFontSize=font_size
    ).configure_title(fontSize=font_size)

def overview_v3(collect_field, reboot_headers, width, height, lsel, font_size, title=None):
    color_item = lsel
    b_df = pd.DataFrame()
    z_fields = []
    rule_fields = []
    for data in collect_field:
        df = data[0]
        if not df.empty:
            df['date_utc'] = df['date'].dt.tz_localize('UTC')
            property = data[1]
            filename = df['file'][0]
            for header in reboot_headers:
                if header[0]:
                    hostname = header[1].split()[2].strip("()")
                    date = header[1].split()[3]
                    if hostname in filename and date in filename:
                        rule_field, z_field, y_pos = create_reboot_rule(
                            df, property, header[0], header[1], col=color_item, col_value=filename)
                        rule_fields.append(rule_field)
                        z_fields.append([z_field, filename])
            
        b_df = pd.concat([b_df, df], ignore_index=False)

    nearest = alt.selection_point(nearest=True, on='mouseover',
                            fields=['date_utc'], empty=False)

    selectors = alt.Chart(b_df).mark_point().encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
        opacity=alt.value(0),
    ).add_params(
        nearest
    )

    selection = alt.selection_point(fields=[color_item],)
    color_x = alt.condition(selection,
                            alt.Color(f'{color_item}:N', legend=None),
                            alt.value('',))
    opacity_x = alt.condition(selection, alt.value(1.0), alt.value(0))

    c = alt.Chart(b_df).mark_line(point=False, interpolate='natural').encode(
        alt.X('utchoursminutes(date_utc)', type='temporal',
              scale=alt.Scale(zero=False),
              axis=alt.Axis(domain=True, labelBaseline='line-top',
                            title='date')),
        alt.Y(property, type='quantitative', scale=alt.Scale(zero=False),
              axis=alt.Axis(titlePadding=5,
                            ),
              ),
        opacity=opacity_x
    ).properties(
        width=width, height=height,
        title=title
    )

    final_img = c.mark_line(strokeWidth=2).add_params(selection).encode(
        color=color_x
    )

    rules = alt.Chart(b_df).mark_rule(color='gray').encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
    ).transform_filter(
        nearest
    )

    legend = alt.Chart(b_df).mark_point().encode(
        y=alt.Y('file:N', axis=alt.Axis(orient='right')),
        color=color_x
    ).add_params(
        selection
    )
    
    xpoints = c.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        color=color_x
    )


    tooltip_text = c.mark_text(
        align="left",
        dx=-10,
        dy=-25,
        fontSize=font_size,
        lineBreak="\n",
    ).encode(
        text=alt.condition(nearest,
                           alt.Text(f'{property}:Q',),
                           alt.value(' '),
                           ),
        opacity=alt.condition(selection, alt.value(1), alt.value(0)),
        color=color_x
    )

    if z_fields:
        while rule_fields:
            rule_field = rule_fields.pop()
            while rule_field:
                rule = rule_field.pop()
                rule = rule.encode(
                    opacity=alt.condition(selection, alt.value(1), alt.value(0)),
                    color=color_x,
                )
                final_img += rule
        while z_fields:
            t_field = z_fields.pop()
            z_field = t_field[0]
            filename = t_field[1]
            reboot_text = return_reboot_text(z_field, y_pos, col=color_item, col_value=filename)
            reboot_text = reboot_text.encode(
                opacity=alt.condition(selection, alt.value(1), alt.value(0)),
                color=color_x
                )
            final_img += reboot_text
        mlayer = alt.layer(final_img, selectors, rules, xpoints,
                       tooltip_text, ).interactive()
    else:
        mlayer = alt.layer(final_img, selectors, rules, xpoints,
                       tooltip_text).interactive()
    return (mlayer | legend).configure_axis(
        labelFontSize=font_size,
        titleFontSize=font_size
    ).configure_title(fontSize=font_size)

def overview_v4(collect_field, reboot_headers, width, height, font_size):
    color_item = 'metric'
    b_df = pd.DataFrame()
    for data in collect_field:
        z_field = []
        df = data[0]
        property = data[1]
        filename = df['file'][0]
        for header in reboot_headers:
            if header[0]:
                hostname = header[1].split()[2].strip("()")
                date = header[1].split()[3]
                if hostname in filename and date in filename:
                    rule_field, z_field, y_pos = create_reboot_rule(
                        df, property, header[0], header[1], col=color_item, col_value=filename)

        b_df[property] = df[property]
    
    b_df = b_df.reset_index().melt('date', var_name='metrics', value_name='y')
    b_df['date_utc'] = b_df['date'].dt.tz_localize('UTC')
    
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date_utc'], empty='none')

    selectors = alt.Chart(b_df).mark_point().encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
        opacity=alt.value(0),
    ).add_params(
        nearest
    )

    selection = alt.selection_point(fields=['metrics'],)
    color_x = alt.condition(selection,
                            alt.Color(f'metrics:N',legend=None),
                            alt.value('',))

    opacity_x = alt.condition(selection, alt.value(1.0), alt.value(0))

    #line = alt.Chart(b_df).encode(
    line = alt.Chart(b_df).mark_line(point=False, interpolate='natural').encode(
        alt.X('utchoursminutes(date_utc)', type='temporal', title='date'),
        alt.Y('y:Q'),
        opacity=opacity_x
        ).properties(
            width=width, height=height
        )

    final_line = line.mark_line(strokeWidth=2).add_params(selection).encode(
        color=color_x
    )

    rules = alt.Chart(b_df).mark_rule(color='gray').encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
    ).transform_filter(
        nearest
    )

    legend = alt.Chart(b_df).mark_point().encode(
        y=alt.Y('metrics:N', axis=alt.Axis(orient='right')),
        color=color_x
    ).add_params(
        selection
    )

    xpoints = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        color=color_x
    )

    
    tooltip_text = line.mark_text(
        align="left",
        dx=-10,
        dy=-25,
        fontSize=font_size,
        lineBreak="\n",
    ).encode(
        text=alt.condition(nearest,
                           alt.Text('y:Q',),
                           alt.value(' '),
                           ),
        opacity=alt.condition(selection, alt.value(1), alt.value(0)),
        color=color_x
    )

    if z_field:
        while rule_field:
            rule = rule_field.pop()
            rule = rule.encode(
                #opacity=alt.condition(selection, alt.value(1), alt.value(0)),
                color='filename:N'
            )
            final_line += rule

        reboot_text = return_reboot_text(
            z_field, y_pos, col=color_item, col_value=filename)
        reboot_text = reboot_text.encode(
            #opacity=alt.condition(selection, alt.value(1), alt.value(0)),
            color='filename:N',
        )
        mlayer = alt.layer(final_line, selectors, rules, 
                           tooltip_text, reboot_text, xpoints).interactive()
    else:
        mlayer = alt.layer(final_line, selectors, rules, xpoints, 
                           tooltip_text).interactive()
    return (mlayer | legend).configure_axis(
        labelFontSize=font_size,
        titleFontSize=font_size
    )

def overview_v5(collect_field, reboot_headers, width, height, lsel, font_size, title=None):
    color_item = lsel
    b_df = pd.DataFrame()
    for data in collect_field:
        z_field = []
        df = data[0]
        property = data[1]
        filename = df['file'][0]
        for header in reboot_headers:
            if header[0]:
                hostname = header[1].split()[2].strip("()")
                date = header[1].split()[3]
                if hostname in filename and date in filename:
                    rule_field, z_field, y_pos = create_reboot_rule(
                        df, property, header[0], header[1], col=color_item, col_value=filename)

        b_df = pd.concat([b_df, df], ignore_index=False)

    b_df['date'] = b_df.index
    b_df['date_utc'] = b_df['date'].dt.tz_localize('UTC')
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date_utc'], empty='none')

    selectors = alt.Chart(b_df).mark_point().encode(
        alt.X('utchoursminutes(date)', type='temporal'),
        opacity=alt.value(0),
    ).add_params(
        nearest
    )

    selection = alt.selection_point(fields=[lsel],)
    color_x = alt.condition(selection,
                            alt.Color(f'{lsel}:N', legend=None),
                            alt.value('',))

    opacity_x = alt.condition(selection, alt.value(1.0), alt.value(0))

    line = alt.Chart(b_df).mark_line(point=False, interpolate='natural').encode(
        alt.X('utchoursminutes(date_utc)', type='temporal', title='date'),
        alt.Y(f'{property}:Q'),
        opacity=opacity_x
    ).properties(
        width=width, height=height,
        title=title,
    )

    final_line = line.mark_line(strokeWidth=2).add_params(selection).encode(
        color=color_x
    )
    rules = alt.Chart(b_df).mark_rule(color='gray').encode(
        alt.X('utchoursminutes(date_utc)', type='temporal'),
    ).transform_filter(
        nearest
    )

    legend = alt.Chart(b_df).mark_point().encode(
        y=alt.Y(f'{color_item}:N', axis=alt.Axis(orient='right')),
        color=color_x
    ).add_params(
        selection
    )

    xpoints = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        color=color_x
    )

    tooltip_text = line.mark_text(
        align="left",
        dx=-10,
        dy=-25,
        fontSize=font_size,
        lineBreak="\n",
    ).encode(
        text=alt.condition(nearest,
                           alt.Text(f'{property}:Q',),
                           alt.value(' '),
                           ),
        opacity=alt.condition(selection, alt.value(1), alt.value(0)),
        color=color_x
    )

    if z_field:
        while rule_field:
            rule = rule_field.pop()
            rule = rule.encode(
                color=f'{lsel}:N'
            )
            final_line += rule

        reboot_text = return_reboot_text(
            z_field, y_pos, col=color_item, col_value=filename)
        reboot_text = reboot_text.encode(
            color='filename:N',
        )
        mlayer = alt.layer(final_line, selectors, rules,
                           tooltip_text, reboot_text, xpoints).interactive()
    else:
        mlayer = alt.layer(final_line, selectors, rules, xpoints,
                           tooltip_text).interactive()
    return (mlayer | legend).configure_axis(
        labelFontSize=font_size,
        titleFontSize=font_size
    ).configure_title(fontSize=font_size)
