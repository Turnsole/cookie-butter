# cookie-butter

Python script for making graphics performance charts for an Android device. To use, enable "Profile GPU rendering" from Developer Options, and restart the app you want to measure. Requires the matplotlib python library. 

Usage: 

    generate_frametime_graphs.py [-h] package [seconds] [title] [device]

Example: 
    
    python generate_frametime_graphs.py com.google.android.deskclock 5 example_graph 078f1fe513d

![Example Graph](example_graph.png "Example Graph")

