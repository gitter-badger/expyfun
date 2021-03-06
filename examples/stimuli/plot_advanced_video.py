# -*- coding: utf-8 -*-
"""
======================
Play sample video file
======================

This shows how to control various properties of a video file in expyfun.

@author: drmccloy
"""

import numpy as np
from expyfun import (ExperimentController, fetch_data_file, building_doc,
                     analyze as ea)

print(__doc__)


movie_path = fetch_data_file('video/example-video.mp4')

ec_args = dict(exp_name='advanced video example', window_size=(720, 480),
               full_screen=False, participant='foo', session='foo',
               version='dev', enable_video=True, output_dir=None)
colors = [x for x in 'rgbcmyk']

with ExperimentController(**ec_args) as ec:
    screen_period = 1. / ec.estimate_screen_fs()
    all_presses = list()
    ec.load_video(movie_path)
    ec.video.set_scale('fill')
    ec.screen_prompt('press 1 during video to toggle pause.', max_wait=1.)
    ec.listen_presses()  # to catch presses on first pass of while loop
    t_zero = ec.video.play()
    this_sec = 0
    while not ec.video.finished:
        if ec.video.playing:
            fliptime = ec.flip()
        else:  # to catch presses reliably, need delay between loop executions
            ec.wait_secs(screen_period / 5)
        presses = ec.get_presses(live_keys=[1], relative_to=t_zero)
        ec.listen_presses()
        # change the background color every 1 second
        if this_sec != int(ec.video.time):
            this_sec = int(ec.video.time)
            ec.set_background_color(colors[this_sec])
        # shrink the video, then move it rightward
        if ec.video.playing:
            if 1 < ec.video.time < 3:
                ec.video.set_scale(ec.video.scale * 0.99)
            if 4 < ec.video.time < 5:
                ec.video.set_pos(ec.video.position + np.array((0.01, 0)))
        # parse button presses
        if len(presses):
            all_presses.extend(presses)
            if len(presses) % 2:  # if even number of presses, do nothing
                if ec.video.playing:
                    ec.video.set_visible(False)
                    ec.video.pause()
                    ec.screen_text('pause!', color='k', font_size=32,
                                   wrap=False)
                    ec.flip()
                else:
                    ec.video.set_visible(True)
                    ec.video.play()
        screenshot = ec.screenshot()
        if building_doc:
            break
    ec.delete_video()
    preamble = 'press times:' if len(all_presses) else 'no presses'
    msg = ', '.join(['{0:.3f}'.format(x[1]) for x in all_presses])
    ec.flip()
    ec.screen_prompt('\n'.join([preamble, msg]), max_wait=1.)

ea.plot_screen(screenshot)
