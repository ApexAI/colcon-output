# Copyright 2022 Apex.AI, Inc.
# Licensed under the Apache License, Version 2.0

from collections import defaultdict
import sys

from colcon_core.event.job import JobEnded
from colcon_core.event.output import StdoutLine
from colcon_core.event_handler import EventHandlerExtensionPoint
from colcon_core.plugin_system import satisfies_version
from colcon_core.subprocess import SIGINT_RESULT


class ConsoleStdoutOnFailureEventHandler(EventHandlerExtensionPoint):
    """
    Output all stdout of an unsuccessful task at once.

    The output is batched up until the task has ended in order to not
    interleave the output from parallel tasks.
    When the task was aborted / exited with a SIGINT no output is shown.

    The extension handles events of the following types:
    - :py:class:`colcon_core.event.output.StdoutLine`
    - :py:class:`colcon_core.event.job.JobEnded`
    """

    # the priority should be slightly higher than the default priority
    # in order to output errors early
    PRIORITY = 110

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            EventHandlerExtensionPoint.EXTENSION_POINT_VERSION, '^1.0')
        self._stdout_lines = defaultdict(list)
        self.enabled = False  # disable by default

    def __call__(self, event):  # noqa: D102
        data = event[0]

        if isinstance(data, StdoutLine):
            job = event[1]
            self._stdout_lines[job].append(data.line)

        elif isinstance(data, JobEnded):
            job = event[1]
            if job in self._stdout_lines:
                if data.rc != 0 and data.rc != SIGINT_RESULT:
                    msg = '--- stdout: {data.identifier}\n'
                    print(msg.format_map(locals()) + b''.join(
                        self._stdout_lines[job]
                    ).decode() + '---', flush=True)
                del self._stdout_lines[job]
