"""
    Generate a graph of frame times
    for the specified number of seconds on an Android device.
"""
#############################################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
##############################################################################################

import argparse
import sys
import time
import subprocess
import numpy
import matplotlib.pyplot as plot

PARSER = argparse.ArgumentParser(
    description='Generate frame time graph for a connected ADB device.')
PARSER.add_argument('package_name', metavar='package', nargs=1,
                    help='package to target (ex: com.google.android)')
PARSER.add_argument('num_seconds', metavar='seconds', type=int, nargs='?',
                    default=1, help='number of seconds to collect data')
PARSER.add_argument('graph_title', metavar='title', nargs='?',
                    default='ms_per_frame', help='title to use for graph')
PARSER.add_argument('device', metavar='device', nargs='?',
                    help='direct to a specific ADB device')
ARGS = PARSER.parse_args()

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

            if in_section and len(line) > 0:
                if "View hierarchy:" == line:
                    in_section = False
                else:
                    results.append(line.split())
            else:
                if "Draw	Prepare	Process	Execute" == line:
                    in_section = True

        print "\tRound {} done, now have {} frames.".format(second, len(results))
        if second < seconds:
            time.sleep(1)

    return numpy.array(results, dtype=float)

def draw_frames(collected_frames):
    """Get the times for each stage of rendering."""
    collected_draw = numpy.array(zip(*collected_frames)[0])
    collected_prepare = numpy.array(zip(*collected_frames)[1])
    collected_process = numpy.array(zip(*collected_frames)[2])
    collected_execute = numpy.array(zip(*collected_frames)[3])

    #Create a bar graph for each stage and stack them.
    collected_indexes = numpy.arange(len(collected_frames))
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

    plot.ylabel('ms')
    plot.xlabel('frame')
    plot.title(ARGS.graph_title)
    plot.legend(
        (draw_bar[0], prepare_bar[0], process_bar[0], execute_bar[0]),
        ('Draw', 'Prepare', 'Process', 'Execute'))

    info_y_coordinate = numpy.amax(collected_totals) * 0.9
    info_x_coordinate = len(collected_totals) * 0.1

    median = round(numpy.median(collected_totals))
    average = round(numpy.average(collected_totals))

    plot.text(info_x_coordinate, info_y_coordinate,
              "Median: {}ms \nAverage: {}ms".format(median, average))

    #Save to disk.
    filename = ARGS.graph_title + ".png"
    plot.savefig(filename)
    print "Saved {} frames to graph as {}.".format(len(collected_totals), filename)

FRAMES = scrape_gfxinfo(ARGS.device, ARGS.num_seconds, ARGS.package_name[0])
if len(FRAMES) > 1:
    draw_frames(FRAMES)
else:
    print "Got no frames. Is collection enabled & the app drawing?"
    sys.exit()
