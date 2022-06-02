import helpers
import alt

def final_overview(sar_structure, headers, entry, wanted_sub_devices, start, end, statistics,
        os_details, restart_headers, font_size, width, height, show_metric):
    df_field = []
    collect_field = []
    if sar_structure.get(headers[entry], None):
        header = entry
        device_num = 1
        title = entry
        dup_bool = 0
        df_describe = 0
        df_display = 0
        metrics = 0
        dup_check = 0
        if 'generic' in sar_structure[headers[entry]].keys():
            df = sar_structure[headers[entry]]['generic']
            df_field.append([df, 0])
        else:
            device_list = list(
                sar_structure[headers[entry]].keys())
            device_list.sort()
            if entry in wanted_sub_devices:
                for device in device_list:
                    df = sar_structure[headers[entry]][device]
                    df_field.append([df, device])
            elif 'all' in device_list:
                device = 'all'
                device_num = len(device_list) -1
                df = sar_structure[headers[entry]][device]
                title = device
                df_field.append([df, device])
            else:
                device = device_list[0]
                df = sar_structure[headers[entry]][device]
                df_field.append([df, device])

        for df_tuple in df_field:
            if df_tuple[1]:
                #title = f"{title} {df_tuple[1]}"
                title = f"{entry} {df_tuple[1]}"
            else:
                title = title
            df = df_tuple[0]
            if start in df.index and end in df.index:
                df = df[start:end]

            if statistics:
                df_display = df.copy()
                df_describe = df_display.describe()
                dup_check = df_display[df_display.index.duplicated()]
                # remove duplicate indexes
                if not dup_check.empty:
                    dup_bool = 1
                    df = df[~df.index.duplicated(keep='first')].copy()

            helpers.restart_headers(
                df, os_details, restart_headers=restart_headers, display=False)
            df = df.reset_index().melt('date', var_name='metrics', value_name='y')
            chart = alt.overview_v1(df, restart_headers, os_details, font_size=font_size,
                width=width, height=height, title=title)
            if show_metric:
                metrics = df['metrics'].drop_duplicates().tolist()
            collect_field.append({'df' :df, 'chart' : chart, 'title' : title , 'metrics' : metrics, 
                'header': header, 'df_display': df_display, 'device_num' : device_num, 'dup_bool':
                dup_bool, 'dup_check' : dup_check, 'df_describe' : df_describe})
                #dup_bool, 'df_table' : df_table})
        return collect_field


