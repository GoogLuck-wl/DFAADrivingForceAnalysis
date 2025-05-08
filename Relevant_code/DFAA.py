import numpy as np
from osgeo import gdal
import os

def get_data(bandfile):
    input_dataset = gdal.Open(bandfile)
    input_band = input_dataset.GetRasterBand(1)
    nodata = input_band.GetNoDataValue()
    input_data = input_band.ReadAsArray()
    return [input_dataset, input_data, nodata]

def cal_single_event(data, nodata_value, target):
    events = []
    gan_start_now = 0
    gan_end_now = 0
    flood_start_now = 0
    flood_end_now = 0
    band_now = 0
    cal_mode = ''
    if target == 'gan':
        cal_mode = 'search drought start'
    else:
        cal_mode = 'search flood start'
    while band_now <= len(data) - 1:
        value_now = data[band_now]
        if value_now == nodata_value:
            break
        if cal_mode == 'search drought start':
            if value_now <= -0.5:
                search_result = search_day('drought', 'start', data, band_now)
                if search_result['search_result'] == 'success':
                    gan_start_now = search_result['stay_index'] - 9
                    cal_mode = 'search drought end'
                    band_now = search_result['stay_index'] + 1
                else:
                    band_now = search_result['stay_index']
            else:
                band_now += 1
        elif cal_mode == 'search drought end':
            if value_now > -0.5:
                gan_end_now = band_now - 1
                events.append({
                    'start': gan_start_now + 89,
                    'end': gan_end_now + 89,
                    'continue':  gan_end_now - gan_start_now + 1,
                    's': np.sum(data[gan_start_now: gan_end_now + 1])
                })
                cal_mode = 'search drought start'
                gan_start_now = 0
                gan_end_now = 0
            band_now += 1
        elif cal_mode == 'search flood start':
            if value_now >= 0.5:
                search_result = search_day('flood', 'start', data, band_now)
                if search_result['search_result'] == 'success':
                    flood_start_now = search_result['stay_index'] - 9
                    cal_mode = 'search flood end'
                    band_now = search_result['stay_index'] + 1
                else:
                    band_now = search_result['stay_index']
            else:
                band_now += 1
        elif cal_mode == 'search flood end':
            if value_now < 0.5:
                flood_end_now = band_now - 1
                events.append({
                    'start': flood_start_now + 89,
                    'end': flood_end_now + 89,
                    'continue': flood_end_now - flood_start_now + 1,
                    's': np.sum(data[flood_start_now: flood_end_now + 1])
                })
                cal_mode = 'search flood start'
                flood_start_now = 0
                flood_end_now = 0
            band_now += 1
    return events

def search_day(target_event, target_mode, vector_data, start_index):
    search_times = 1
    index_now = start_index
    if target_event == 'drought' and target_mode == 'start':
        while search_times < 10:
            index_now += 1
            if index_now >= len(vector_data):
                return {
                    'search_result': 'fail',
                    'stay_index': index_now
                }
            search_value_now = vector_data[index_now]
            if search_value_now <= -0.5:
                search_times += 1
                continue
            else:
                return {
                    'search_result': 'fail',
                    'stay_index': index_now
                }
        return {
            'search_result': 'success',
            'stay_index': index_now
        }
    elif target_event == 'flood' and target_mode == 'start':
        while search_times < 10:
            index_now += 1
            if index_now >= len(vector_data):
                return {
                    'search_result': 'fail',
                    'stay_index': index_now
                }
            search_value_now = vector_data[index_now]
            if search_value_now >= 0.5:
                search_times += 1
                continue
            else:
                return {
                    'search_result': 'fail',
                    'stay_index': index_now
                }
        return {
            'search_result': 'success',
            'stay_index': index_now
        }

def merge(events, data):
    event_last = 0
    processing = True
    while processing:
        event_last = 0
        for event_index in range(0, len(events)):
            event = events[event_index]
            if event_last == 0:
                event_last = event
                if event_index == len(events) - 1:
                    processing = False
                    break
                continue
            if event['start'] - event_last['end'] - 1 <= 2:
                s_event_last = event_last['s']
                s_interval = 0
                index_now = event_last['end'] - 89 + 1
                while index_now <= event['start'] - 89 - 1:
                    s_interval += abs(1 - abs(data[index_now]))
                    index_now += 1
                if s_interval / s_event_last <= 0.2:
                    new_event = {
                        'start': event_last['start'],
                        'end': event['end'],
                        'continue': event['end'] - event_last['start'] + 1,
                        's': event_last['s'] + event['s']
                    }
                    events[event_index - 1] = new_event
                    del events[event_index]
                    event_last = 0
                    break
                else:
                    if event_index == len(events) - 1:
                        processing = False
                        break
                    event_last = event
                    continue
            else:
                if event_index == len(events) - 1:
                    processing = False
                    break
                event_last = event
                continue
    return events

def get_gan_to_shi(gan_events, shi_events, data):
    results = []
    for gan in gan_events:
        for shi in shi_events:
            interval_now = shi['start'] - gan['end'] - 1
            if interval_now <= 5 and interval_now >= -5:
                results.append({
                    'start': gan['start'],
                    'end': shi['end'],
                    'continue': shi['end'] - gan['start'] + 1,
                    'intensity': abs(round((np.sum(data[shi['start'] - 89: shi['start'] - 89 + interval_now]) - np.sum(data[gan['end'] - 89 - interval_now + 1: gan['end'] - 89 + 1])) / interval_now, 2))
                })
                break
    return results

def get_shi_to_gan(gan_events, shi_events, data):
    results = []
    for shi in shi_events:
        for gan in gan_events:
            interval_now = gan['start'] - shi['end'] - 1
            if interval_now <= 5 and interval_now >= -5:
                results.append({
                    'start': shi['start'],
                    'end': gan['end'],
                    'continue': gan['end'] - shi['start'] + 1,
                    'intensity': abs(round((np.sum(data[gan['start'] - 89: gan['start'] - 89 + interval_now]) - np.sum(data[shi['end'] - 89 - interval_now + 1: shi['end'] - 89 + 1])) / interval_now, 2))
                })
                break
    return results

def process_data(data_list, year):
    dataset_test = data_list[0][0]
    nodata_value = data_list[0][2]
    rows = dataset_test.RasterYSize
    colmns = dataset_test.RasterXSize
    projinfo = dataset_test.GetProjection()
    geotransform = dataset_test.GetGeoTransform()
    data_first = np.full((len(data_list), rows, colmns), np.nan)
    data_result_start = np.full((9, rows, colmns), np.nan)
    data_result_end = np.full((9, rows, colmns), np.nan)
    data_result_continue = np.full((9, rows, colmns), np.nan)
    data_result_intensity = np.full((9, rows, colmns), np.nan)
    for i in range(len(data_list)):
        data_first[i, :, :] = data_list[i][1]
    for row in range(rows):
        for col in range(colmns):
            vector_now = data_first[:, row, col]
            results_gan = cal_single_event(vector_now, nodata_value, 'gan')
            results_shi = cal_single_event(vector_now, nodata_value, 'shi')
            if len(results_gan) == 0 or len(results_shi) == 0:
                continue
            merged_gan = merge(results_gan, vector_now)
            merged_shi = merge(results_shi, vector_now)
            gan_to_shi_events = get_shi_to_gan(merged_gan, merged_shi, vector_now)     #每次修改此行
            for index in range(len(gan_to_shi_events)):
                result_now = gan_to_shi_events[index]
                data_result_start[index, row, col] = result_now['start']
                data_result_end[index, row, col] = result_now['end']
                data_result_continue[index, row, col] = result_now['continue']
                data_result_intensity[index, row, col] = result_now['intensity']
    save_data(data_result_start, rows, colmns, geotransform, projinfo, year, 'start')
    save_data(data_result_end, rows, colmns, geotransform, projinfo, year, 'end')
    save_data(data_result_continue, rows, colmns, geotransform, projinfo, year, 'continue')
    save_data(data_result_intensity, rows, colmns, geotransform, projinfo, year, 'intensity')


def save_data(data, rows, colmns, geotransform, projinfo, year, name):
    driver = gdal.GetDriverByName("GTiff")
    dst_ds = driver.Create(r'E:\\' + str(year) + '_' + name + '.tif', colmns,
                           rows, 9, gdal.GDT_Float64)
    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(projinfo)
    for i in range(1, 10):
        dst_ds.GetRasterBand(i).WriteArray(data[i - 1, :, :])
    del dst_ds

input_dir = r'E:\'
for year in range(2001, 2023):
    year_data = []
    for day in range(89, 298):
        file_name = 'SWAP' + str(year)
        if day >= 100:
            day_str = str(day)
        else:
            day_str = '0' + str(day)
        file_name += day_str
        year_data.append(get_data(input_dir + '\\' + file_name + '.tif'))
    process_data(year_data, year)
    print(year)