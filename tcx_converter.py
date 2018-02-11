from lxml import etree, objectify
import requests
import re
import os
import sys
import csv
import shutil
from datetime import datetime, timedelta


TEMP_DATA_FILE = 'tmp_data.txt'
TEMP_META_FILE = 'tmp_meta.txt'
TEMP_LIST = [TEMP_META_FILE, TEMP_DATA_FILE]

def strip_ns(string):
    return string.split('}')[1]

def parse_time(string):
    time = datetime.strptime(string[:-5], '%Y-%m-%dT%H:%M:%S')
    ms = timedelta(
        microseconds=int(string[-4:-1] + '000')
    )
    return time+ms

headerDi = {
    "DistanceMeters": "Distance(m)",
    "Cadence": "Cadence(1/min)",
    "Time": "Time(s)"
}

def main():
    in_filename = sys.argv[1]
    tree = etree.parse(in_filename)
    root = tree.getroot()
    # Activites node
    root = root.getchildren()[0]
    # write each activity in new file
    for activity in root:
        act_name = activity.get('Sport')
        datestring = activity.find('{*}Id').text
        datestring = parse_time(datestring).strftime('%Y%m%dT%H%M%SZ')
        out_filename = './' + datestring + '_' + act_name + '.csv'
        # actual tabular data written to temporary file for merging with lap data
        with open(TEMP_DATA_FILE, mode='w') as tmp_dataF:
            csvwriter = csv.writer(tmp_dataF, lineterminator='\n')
            for i, lap in enumerate(activity.findall('{*}Lap')):
                lap_n = str(i + 1)
                metadata = []
                metadata.append("Lap " + lap_n)
                metadata.append("Start_time " + str(lap.get("StartTime")))
                metadata.append("Duration(s) " + str(lap.find("{*}TotalTimeSeconds").text))
                metadata.append("Distance(m) " + str(lap.find("{*}DistanceMeters").text))
                metadata.append("Calories " + str(lap.find("{*}Calories").text))
                metadata.append("Avg_HeartRate(bpm) " + str(lap.find("{*}AverageHeartRateBpm").find("{*}Value").text))
                metadata.append("Cadence " + str(lap.find("{*}Cadence").text))
                tracking = lap.find("{*}Track")
                for j, tp in enumerate(tracking.findall("{*}Trackpoint")):
                    dp_n = str(j + 1)
                    headerL = []
                    instL = []
                    headerL.append("Lap")
                    instL.append(lap_n)
                    for node in tp:
                        if node.tag[-10:] == "Extensions":
                            continue
                        if i == j == 0:
                            headerL.append(strip_ns(node.tag))
                            if node.tag[-4:] == "Time":
                                datestring = node.text
                                metadata.append("Lap_first_time " + datestring) 
                                startime = parse_time(datestring)
                        #
                        valueSt = ""
                        if not len(node.getchildren()) == 0:
                            valueSt = "_".join(
                                [str(b_node.text) for b_node in node.iter() if not b_node.text.isspace()]
                            )
                        elif not node.text.isspace():
                            if strip_ns(node.tag) == 'Time':
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
            with open(TEMP_META_FILE, 'w') as metaF:
                for s in metadata:
                    metaF.write("# " + s + "\n")
                metaF.write("#"*64 + "\n")
            with open(out_filename, 'xb') as wfd:
                for filename in TEMP_LIST:
                    with open(filename,'rb') as fd:
                        shutil.copyfileobj(fd, wfd, 1024*1024*10)
                    os.remove(filename)

if __name__ == '__main__':
   main()
