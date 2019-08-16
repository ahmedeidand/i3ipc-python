from subprocess import Popen
import pytest

from i3ipc.aio import Connection
from i3ipc.model import CommandReply

import math
from random import random
import asyncio

from Xlib import display
from .window import Window


class IpcTest:
    timeout_thread = None
    i3_conn = None

    @pytest.fixture(scope='class')
    def event_loop(self):
        return asyncio.get_event_loop()

    @pytest.fixture(scope='class')
    async def i3(self):
        process = Popen(['i3', '-c', 'test/i3.config'])
        # wait for i3 to start up
        tries = 0

        while True:
            try:
                IpcTest.i3_conn = await Connection().connect()
                break
            except Exception:
                tries += 1

                if tries > 1000:
                    raise Exception('could not start i3')
                await asyncio.sleep(0.001)

        yield IpcTest.i3_conn
        process.kill()
        IpcTest.i3_conn = None

    async def command_checked(self, cmd):
        i3 = IpcTest.i3_conn
        assert i3

        result = await i3.command(cmd)

        assert type(result) is list

        for r in result:
            assert type(r) is CommandReply
            assert r.success is True

        return result

    async def open_window(self):
        d = display.Display()
        window = Window(d)
        await self.i3_conn.command('nop')
        return window.window.id

    async def fresh_workspace(self):
        i3 = IpcTest.i3_conn
        assert i3

        workspaces = await i3.get_workspaces()
        while True:
            new_name = str(math.floor(random() * 100000))
            if not any(w for w in workspaces if w['name'] == new_name):
                await i3.command('workspace %s' % new_name)
                return new_name
