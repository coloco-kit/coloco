from collections import deque
from dataclasses import dataclass
from itertools import islice
from typing import Any, Awaitable, Callable
import asyncio
import os

from rich.align import Align
from rich.ansi import AnsiDecoder
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
import cyclopts

app = cyclopts.App()

MAX_LINES_BUFFERED = 100


@dataclass
class Process:
    title: str
    function: Callable[[], Awaitable[Any]] | None = None
    command: list[str] | None = None


async def terminate_process(proc: asyncio.subprocess.Process) -> None:
    if proc.returncode is not None:
        return
    proc.terminate()
    try:
        await asyncio.wait_for(proc.wait(), timeout=3.0)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()


async def read_process(process: Process, buffer):
    proc: asyncio.subprocess.Process | None = None
    try:
        if process.command:
            env = os.environ.copy()
            env["FORCE_COLOR"] = "1"
            env["CLICOLOR_FORCE"] = "1"
            env["PYTHONUNBUFFERED"] = "1"

            proc = await asyncio.create_subprocess_exec(
                *process.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )
            assert proc.stdout is not None
            async for raw in proc.stdout:
                buffer.append(raw.decode(errors="replace").rstrip())

            await proc.wait()
            buffer.append(f"[process exited: {proc.returncode}]")
        if process.function:
            result = await process.function(buffer)
            buffer.append(result)
    except asyncio.CancelledError:
        if proc is not None:
            await terminate_process(proc)
        raise


def decode_line(decoder: AnsiDecoder, line: str | Text):
    if isinstance(line, str):
        text = decoder.decode_line(line)
    elif isinstance(line, Text):
        text = line
    else:
        raise ValueError(f"Invalid line type: {type(line)}")

    text.overflow = "ellipsis"
    text.no_wrap = True
    return text


async def _run_multiprocesses(processes: list[Process]):
    console = Console()
    layout = Layout()
    layout.split_row(
        *[Layout(name=p) for p in range(len(processes))],
    )
    queues = [deque(maxlen=MAX_LINES_BUFFERED) for _ in processes]

    tasks = [
        asyncio.create_task(read_process(process, queues[p])) for p, process in enumerate(processes)
    ]

    decoder = AnsiDecoder()
    try:
        with Live(layout, console=console, screen=True, refresh_per_second=10):
            while not all(t.done() for t in tasks):
                available_rows = console.height - 2

                for p, queue in enumerate(queues):
                    # Take the last X lines
                    text = Text(no_wrap=True, overflow="ellipsis")
                    start_index = max(0, len(queue) - available_rows)
                    queue_slice = islice(queue, start_index, None)
                    for line in queue_slice:
                        text.append(decode_line(decoder, line) + "\n")
                    text_lines = text.split("\n")
                    panel_content = Group(*Text("\n").join(text_lines[-available_rows:]))
                    panel = Panel(panel_content, title=processes[p].title, border_style="bold")
                    layout[p].update(panel)

                console.render(layout, console.options)

                await asyncio.sleep(0.1)
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def run_multiprocesses(processes: list[Process]):
    try:
        asyncio.run(_run_multiprocesses(processes))
    except KeyboardInterrupt:
        pass
