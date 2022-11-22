import curses
import pyttsx3
import threading
from queue import Queue

def progress_bar(size, progress, sep=0.1, levels=['-', '*', chr(9608)]):
    progress_int = min(int(progress / sep), size * len(levels))
    fill_type = (progress_int - 1) // size
    prev_fill_char = levels[fill_type - 1] if fill_type > 0 else ' '
    fill_char = levels[fill_type]
    fill_cnt = progress_int - fill_type * size

    return f'[{fill_char * fill_cnt}{prev_fill_char * (size - fill_cnt)}]'

def main(stdscr):
    engine = pyttsx3.init()

    # UI and state
    buf = ''
    volume = engine.getProperty('volume')
    rate = engine.getProperty('rate')
    token_sep = ' '

    queue = Queue()
    cur = ''

    last_press = -1
    chastity_cage = threading.Lock()
    def draw():
        chastity_cage.acquire()

        stdscr.clear()
        stdscr.addstr(0, 0, f'Volume: {volume:.1f} {progress_bar(10, volume)}')
        stdscr.addstr(1, 0, f'Rate: {rate} {progress_bar(10, rate, sep=20)}')
        stdscr.addstr(2, 0, f'Token Separator: {repr(token_sep)}')
        stdscr.addstr(3, 0, f'Last Press: {last_press}')

        stdscr.addstr(5, 0, f'Buffer: {repr(buf)}')

        stdscr.addstr(6, 0, f'Words Being Spoken ({queue.qsize()} words remaining):')
        stdscr.addstr(7, 4, repr(cur))
        # for e, row in enumerate(queue, 8):
        #     stdscr.addstr(row, 4, repr(e))
        stdscr.refresh()

        chastity_cage.release()

    # Talking thread
    def talk_loop():
        nonlocal queue
        nonlocal cur

        while True:
            speech = queue.get(True)
            while not queue.empty():
                speech += ' ' + queue.get(True)
            cur = speech
            draw()

            if speech.strip():
                engine.say(speech)
                engine.runAndWait()
            if queue.empty():
                cur = ''
            draw()

    talk_thread = threading.Thread(target=talk_loop)
    talk_thread.start()

    draw()
    while True:
        c = stdscr.getch()
        last_press = c
        if c == curses.KEY_UP:
            volume += 0.1
            engine.setProperty('volume', volume)
        elif c == curses.KEY_DOWN:
            volume -= 0.1
            engine.setProperty('volume', volume)
        elif c == curses.KEY_RIGHT:
            rate += 20
            engine.setProperty('rate', rate)
        elif c == curses.KEY_LEFT:
            rate -= 20
            engine.setProperty('rate', rate)
        elif c == curses.KEY_BACKSPACE:
            buf = buf[:-1]
        elif c == 1:
            token_sep = ' ' if token_sep == '\n' else '\n'
        else:
            c = chr(c)
            if c == token_sep:
                queue.put(buf)
                buf = ''
            else:
                buf += c

        draw()

curses.wrapper(main)
