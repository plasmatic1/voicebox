import curses
import threading
from collections import deque
from gtts import gTTS, tts
import playsound

# im listening dw dwdwdwdwdw
aliases = {
        'im': 'i\'m',
}

def transform(s):
    for k, v in aliases.items():
        s = s.replaceall(k, v)
    return s

def progress_bar(size, progress, sep=0.1, levels=['-', '*', chr(9608)]):
    progress_int = min(int(progress / sep), size * len(levels))
    fill_type = (progress_int - 1) // size
    prev_fill_char = levels[fill_type - 1] if fill_type > 0 else ' '
    fill_char = levels[fill_type]
    fill_cnt = progress_int - fill_type * size

    return f'[{fill_char * fill_cnt}{prev_fill_char * (size - fill_cnt)}]'

def main(stdscr):
    # engine = pyttsx3.init()

    # UI and state
    buf = ''
    token_sep = ' '
    retries = -1

    queue = deque()
    say_evt = threading.Event()
    cur = ''

    last_press = -1
    chastity_cage = threading.Lock() 
    def draw():
        chastity_cage.acquire()

        stdscr.clear()
        stdscr.addstr(0, 0, f'Token Separator: {repr(token_sep)}')
        stdscr.addstr(1, 0, f'Last Press: {last_press}')

        stdscr.addstr(3, 0, f'Buffer: {repr(buf)}')
        stdscr.addstr(4, 0, f'Words Being Spoken: {repr(cur)}')
        stdscr.addstr(5, 0, f'Queue ({len(queue)} words remaining):')
        if retries != -1:
            stdscr.addstr(6, 0, f'!! Attempted Retry, {retries} retries remaining !!')
        for row, e in enumerate(queue, 8):
            stdscr.addstr(row, 2, '- ' + repr(e))
        stdscr.refresh()

        chastity_cage.release()

    # Talking thread
    def talk_loop():
        nonlocal queue
        nonlocal cur
        nonlocal retries

        while True:
            say_evt.wait(3) # wait timeout of 3 seconds in case something gets "stuck" (event flag is off, queue non-empty)
            if not queue: continue 

            # get next string of words to say
            speech = queue.popleft()
            while queue:
                speech += ' ' + queue.popleft()
            cur = speech
            draw()

            # say words and clear event
            if speech.strip():
                # engine.say(speech)
                # engine.runAndWait()
                # gtts.tts.gTTSError
                while True:
                    try:
                        g = gTTS(speech)
                        g.save('last.mp3')
                        playsound.playsound('last.mp3')
                        break
                    except tts.gTTSError:
                        if retries == 0:
                            break
                        elif retries == -1:
                            retries = 3

                        retries -= 1
                    draw()

                retries = -1

            if not queue:
                cur = ''
                say_evt.clear()
            draw()

    talk_thread = threading.Thread(target=talk_loop)
    talk_thread.start()

    draw()
    while True:
        c = stdscr.getch()
        last_press = c
        if c == curses.KEY_BACKSPACE:
            buf = buf[:-1]
        elif c == 1:
            token_sep = ' ' if token_sep == '\n' else '\n'
        else:
            c = chr(c)
            if c == token_sep:
                queue.append(buf)
                say_evt.set()
                buf = ''
            else:
                buf += c

        draw()

curses.wrapper(main)
