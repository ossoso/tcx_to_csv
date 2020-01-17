from lxml import etree, objectify
import requests
import re
import os
import io
import sys
import csv
import shutil
import time
from datetime import datetime, timedelta

TEMP_DATA_FILE = 'tmp_data.txt'
TEMP_META_FILE = 'tmp_meta.txt'
TEMP_LIST = (TEMP_META_FILE, TEMP_DATA_FILE)

def strip_ns(string):
    return string.split('}')[1]

def parse_time(string):
    time = datetime.strptime(string[:-5], '%Y-%m-%dT%H:%M:%S')
    ms = timedelta(
        microseconds=int(string[-4:-1] + '000') #truncate trailing Z in timestamp
    )
    return time+ms

headerDi = {
    "DistanceMeters": "Distance(m)",
    "Cadence": "Cadence(1/min)",
    "Time": "Time(s)"
}

def parse_source(source, src_type="file"):
    if src_type == "file":
        root = etree.parse(source, etree.XMLParser()).getroot()
        return root
    elif src_type == "string":
        return etree.fromstring(source)

def _fileOrBuffConstr(file_cont, isFile):
    if (file_cont == 'data') and isFile:
        return lambda: open(TEMP_DATA_FILE, 'w')
    elif (file_cont == 'meta') and isFile:
        return lambda: open(TEMP_META_FILE, 'w')
    else:
        return io.StringIO

def convert_to_csv(source, src_type="file"):
    isFile = src_type == 'file'
    #parse whole file
    try:
        root = parse_source(source, src_type)
    except Exception as e:
        print(e)
        raise e
    # Activites node
    root = root.getchildren()[0]
    # write each activity in new file
    created_filenames = list()
    for activity in root:
        act_name = activity.get('Sport')
        # namespaces handled by find methods * wildcards
        datestring = activity.find('{*}Id').text
        datestring = parse_time(datestring).strftime('%Y%m%dT%H%M%SZ')
        try_filename = './' + datestring + '_' + act_name
        out_extension = '.csv'
        if not isFile:
            outL = list()
            csvStr = ""
        # actual tabular data written to temporary file for merging with lap data
        with _fileOrBuffConstr('data', isFile)() as tmp_data:
            csvwriter = csv.writer(tmp_data, lineterminator='\n')
            for i, lap in enumerate(activity.findall('{*}Lap')):
                lap_n = str(i + 1)
                metadata = []
                metadata.append("Lap " + lap_n)
                metadata.append("Start_time " + str(lap.get("StartTime")))
                metadata.append("Duration(s) " + str(lap.find("{*}TotalTimeSeconds").text))
                metadata.append("Distance(m) " + str(lap.find("{*}DistanceMeters").text))
                metadata.append("Calories " + str(lap.find("{*}Calories").text))
                metadata.append("Avg_HeartRate(bpm) " + str(lap.find("{*}AverageHeartRateBpm").find("{*}Value").text))
                metadata.append("Avg_Cadence " + str(lap.find("{*}Cadence").text))
                tracking = lap.find("{*}Track")
                for j, tp in enumerate(tracking.findall("{*}Trackpoint")):
                    dp_n = str(j + 1)
                    headerL = []
                    instL = []
                    headerL.append("Lap")
                    instL.append(lap_n)
                    for node in tp:
                        bare_tag = etree.QName(node.tag).localname
                        if bare_tag == "Extensions":
                            continue
                        if i == j == 0:
                            headerL.append(bare_tag)
                            if bare_tag == "Time":
                                datestring = node.text
                                metadata.append("Lap_first_time " + datestring) 
                                startime = parse_time(datestring)
                        #
                        valueSt = ""
                        if not len(node.getchildren()) == 0:
                            valueSt = "_".join(
                                [str(b_node.text) for b_node in node.iter() if
                                 not (
                                     b_node.text is None or
                                     b_node.text.isspace()
                                 )]
                            )
                        elif not node.text.isspace():
                            if bare_tag == 'Time':
                                delta_s = parse_time(node.text) - startime
                                valueSt = str(delta_s.total_seconds())
                            else:
                                valueSt = node.text
                        instL.append(valueSt)
                    # Extensions
                    instL.append(tp.find('.//{*}Watts').text)
                    if i == j == 0:
                        headerL.append("Power(Watts)")
                        headerL = map(lambda s: headerDi.get(s, s), headerL)
                        csvwriter.writerow(headerL)
                    csvwriter.writerow(instL)
            if not isFile:
                csvStr += tmp_data.getvalue()
            with _fileOrBuffConstr('meta', isFile)() as meta:
                for s in metadata:
                    meta.write("# " + s + "\n")
                meta.write("#"*64 + "\n")
                if not isFile:
                    csvStr = meta.getvalue() + csvStr
            out_filename = try_filename + out_extension
            while os.path.exists(out_filename):
                file_num_sep = '__'
                file_num_str = '1'
                file_basename = try_filename
                fileL = out_filename.split(file_num_sep)
                if len(fileL) > 1:
                    file_basename = file_num_sep.join(fileL[:-1])
                    file_num_str = str(int(fileL[-1][:-len(out_extension)]) + 1)
                out_filename = file_basename + file_num_sep + file_num_str + out_extension
            created_filenames.append(out_filename)
        if isFile:
            with open(out_filename, 'xb') as wfd:
                for filename in TEMP_LIST:
                    with open(filename,'rb') as fd:
                        shutil.copyfileobj(fd, wfd, 1024*1024*10)
                    os.remove(filename)
        else:
            outL.append((out_filename, csvStr,))
    if not isFile:
        created_filenames = tuple((fname, csvStr) for fname, csvStr in outL)
    return created_filenames



def import_tcx(source, src_type):
    csv_files = convert_to_csv(source, src_type)
    dfTup = tuple(import_csv(fname, fname) for fname in csv_files)
    return dfTup

def main():
    in_filename = sys.argv[1]
    convert_to_csv(in_filename)

if __name__ == '__main__':
   main()
