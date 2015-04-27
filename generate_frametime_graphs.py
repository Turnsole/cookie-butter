#############################################################################################
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
##############################################################################################
"""
    Generate a graph of frame times
    for the specified number of seconds on an Android device.
"""
import argparse
import sys
import time
import subprocess
import numpy
import matplotlib.pyplot as plot

def estimate_dropped_frames(fps, collected_totals):
    max_time = 1000 / float(fps)

    dropped_frames = 0
    for frame_time in collected_totals:
        if frame_time > max_time:
            dropped_frames += 1
    return dropped_frames

def scrape_display_info(device):
    """Grab frame rate info via dumpsys display. Return fps as a string."""
    target = "" if (device is None or len(device) == 0) else "-s " + device 
    cmd = "adb {} shell dumpsys display | grep -i mphys | cut -d ',' -f 2".format(target)
    try:
        return subprocess.check_output([cmd], shell=True).split()[0]
    except subprocess.CalledProcessError:
        print "Unable to execute ADB command."
        print "If there is more than one device, specify which."
        sys.exit()

def scrape_gfxinfo(device, seconds, package):
    """Grab frame info via dumpsys gfxinfo. Return numpy array of floats."""
    results = []

    for second in range(seconds):
        in_section = False
        target = "" if (device is None or len(device) == 0) else "-s " + device 
        cmd = "adb {} shell dumpsys gfxinfo {}".format(target, package)
        try:
            dumpsys_output = subprocess.check_output([cmd], shell=True)
        except subprocess.CalledProcessError:
            print "Unable to execute ADB command."
            print "If there is more than one device, specify which."
            sys.exit()

        for line in dumpsys_output.split("\n"):
            line = line.strip()

            if in_section:
                if len(line) == 0:
                    in_section = False
                else:
                    results.append(line.split())
            else:
                if "Process Execute".split() == line.split()[-2:]:
                    in_section = True

        print "\tRound {} done, now have {} frames.".format(second, len(results))
        if second < seconds:
            time.sleep(1)

    return numpy.array(results, dtype=float)

def draw_frames(collected_frames, title, fps):
    """Get the times for each stage of rendering."""
    number_stages = len(collected_frames[0])
    number_frames = len(collected_frames)

    collected_draw = numpy.array(zip(*collected_frames)[0])
    if number_stages > 3:
        collected_prepare = numpy.array(zip(*collected_frames)[1])
    else:
        collected_prepare = numpy.zeros(number_frames)
    collected_process = numpy.array(zip(*collected_frames)[number_stages - 2])
    collected_execute = numpy.array(zip(*collected_frames)[number_stages - 1])

    #Create a bar graph for each stage and stack them.
    collected_indexes = numpy.arange(number_frames)
    draw_bar = plot.bar(collected_indexes, collected_draw,
                        width=1.0,
                        color='#7C4DFF', # purple 
                        edgecolor="none")
    prepare_bar = plot.bar(collected_indexes, collected_prepare,
                           width=1.0,
                           color='#00796B', # green
                           edgecolor="none",
                           bottom=collected_draw)
    collected_totals = collected_draw + collected_prepare
    process_bar = plot.bar(collected_indexes, collected_process,
                           width=1.0,
                           color='#727272', # grey
                           edgecolor="none",
                           bottom=collected_totals)
    collected_totals = collected_totals + collected_process
    execute_bar = plot.bar(collected_indexes, collected_execute,
                           width=1.0,
                           color='#FFA000', # orange 
                           edgecolor="none",
                           bottom=collected_totals)
    collected_totals = collected_totals + collected_execute

    plot.ylabel('time in ms')
    plot.xlabel('frame')
    plot.title(title)
    plot.legend(
        (draw_bar[0], prepare_bar[0], process_bar[0], execute_bar[0]),
        ('Draw', 'Prepare', 'Process', 'Execute'))

    info_y_coordinate = numpy.amax(collected_totals) * 0.9
    info_x_coordinate = len(collected_totals) * 0.1

    median = round(numpy.median(collected_totals))
    average = round(numpy.average(collected_totals))
    est_dropped = estimate_dropped_frames(fps, collected_totals)

    summary = """Median: {}ms \nAverage: {}ms \nDevice framerate: {} \nEstimated dropped frames: {}""".format(median, average, fps, est_dropped)
    print summary

    #Plot and save to disk.
    plot.text(info_x_coordinate, info_y_coordinate, summary)
    filename = title + ".png"
    plot.savefig(filename)
    print "Saved {} frames to graph as {}.".format(len(collected_totals), filename)

def main(sys_args):
    parser = argparse.ArgumentParser(description='Generate frame time graph for a connected ADB device.')
    parser.add_argument('package_name', metavar='package', nargs=1,
                        help='package to target (ex: com.google.android)')
    parser.add_argument('num_seconds', metavar='seconds', type=int, nargs='?',
                        default=1, help='number of seconds to collect data')
    parser.add_argument('graph_title', metavar='title', nargs='?',
                        default='ms_per_frame', help='title to use for graph')
    parser.add_argument('device', metavar='device', nargs='?',
                        help='direct to a specific ADB device')
    args = parser.parse_args(sys_args)

    frames = scrape_gfxinfo(args.device, args.num_seconds, args.package_name[0])
    if len(frames) > 1:
        fps = scrape_display_info(args.device)
        draw_frames(frames, args.graph_title, fps)
    else:
        print "Got no frames. Is collection enabled & {} drawing?".format(args.package_name[0])

if __name__ == "__main__":
    main(sys.argv[1:]) 
