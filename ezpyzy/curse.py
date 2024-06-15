
import curses

def main(stdscr):
    try:
        # Clear screen
        stdscr.clear()

        # Turn off cursor blinking
        curses.curs_set(0)

        # Don't wait for input when calling getch
        stdscr.nodelay(1)

        key = ''
        while key != ord('q'):
            key = stdscr.getch()
            if key != -1:
                stdscr.addstr(0, 0, f'Pressed: {chr(key)}')
                stdscr.refresh()
            # Perform other non-blocking operations here
            # curses.napms(100)
    except Exception as e:
        # Handle any exceptions and cleanup before exiting
        stdscr.addstr(1, 0, f"Exception: {str(e)}")
        stdscr.refresh()
        curses.napms(2000)
    finally:
        # Ensure the terminal is reset to its normal state
        curses.endwin()

if __name__ == "__main__":
    import time

    print('Hello World!')
    time.sleep(1)

    curses.wrapper(main)
    # Resume normal execution after curses application ends
    print("Curses application has ended. Resuming normal execution.")
    # You can add any additional code here that you want to run after the curses application ends
