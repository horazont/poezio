#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# Copyright 2010 Le Coz Florent <louizatakk@fedoraproject.org>
#
# This file is part of Poezio.
#
# Poezio is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# Poezio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Poezio.  If not, see <http://www.gnu.org/licenses/>.

import curses

class Win(object):
    def __init__(self, height, width, y, x, parent_win):
        self._resize(height, width, y, x, parent_win)

    def _resize(self, height, width, y, x, parent_win):
        self.height, self.width, self.x, self.y = height, width, x, y
        self.win = parent_win.subwin(height, width, y, x)

    def refresh(self):
        self.win.noutrefresh()

class UserList(Win):
    def __init__(self, height, width, y, x, parent_win, visible):
        Win.__init__(self, height, width, y, x, parent_win)
        self.visible = visible
        self.win.attron(curses.color_pair(2))
        self.win.vline(0, 0, curses.ACS_VLINE, self.height)
        self.win.attroff(curses.color_pair(2))
        self.color_dict = {'moderator': 3,
                           'participant':2,
                           'visitor':4}

    def refresh(self, users):
        if not self.visible:
            return
        self.win.clear()
        y = 0
        for user in users:
            try:
                color = self.color_dict[user.role]
            except:
                color = 1
            self.win.attron(curses.color_pair(color))
            self.win.addnstr(y, 1, user.nick, self.width-1)
            self.win.attroff(curses.color_pair(color))
            y += 1
            if y == self.height:
                break
        self.win.refresh()

    def resize(self, height, width, y, x, stdscr, visible):
        self.visible = visible
        if not visible:
            return
        self._resize(height, width, y, x, stdscr)

class Topic(Win):
    def __init__(self, height, width, y, x, parent_win, visible):
        self.visible = visible
        Win.__init__(self, height, width, y, x, parent_win)

    def resize(self, height, width, y, x, stdscr, visible):
        self._resize(height, width, y, x, stdscr)

    def refresh(self, room_name):
        if not self.visible:
            return
        self.win.clear()
        try:
            self.win.addnstr(0, 0, room_name + " "*(self.width-len(room_name)-1), self.width-1
                             , curses.color_pair(1))
        except:pass
        self.win.refresh()

class RoomInfo(Win):
    def __init__(self, height, width, y, x, parent_win, visible):
        self.visible = visible
        Win.__init__(self, height, width, y, x, parent_win)

    def resize(self, height, width, y, x, stdscr, visible):
        self._resize(height, width, y, x, stdscr)

    def refresh(self, rooms, current):
        if not self.visible:
            return
        def compare_room(a, b):
            return a.nb - b.nb
        self.win.clear()
        self.win.addnstr(0, 0, current.name+" [", self.width-1
                             ,curses.color_pair(1))
        sorted_rooms = sorted(rooms, compare_room)
        for room in sorted_rooms:
            if current == room:
                color = 10
            else:
                color = room.color_state
            try:
                self.win.addstr(str(room.nb), curses.color_pair(color))
                self.win.addstr(",", curses.color_pair(1))
            except:             # end of line
                break
        (y, x) = self.win.getyx()
        try:
            self.win.addstr(y, x-1, ']'+(' '*((self.width-1)-x)), curses.color_pair(1))
        except:
            pass
        self.win.refresh()

class TextWin(object):
    """
    keep a dict of {winname: window}
    when a new message is received in a room, just add
    the line at the bottom (and scroll if needed)
    when the current room is changed, just refresh the
    associated window
    When the term is resized, rebuild ALL the windows
    (the complete lines lists are keeped in the Room class)
    """
    def __init__(self, height, width, y, x, parent_win, visible):
        self.visible = visible
        self.height = height
        self.width = width
        self.y = y
        self.x = x
        self.parent_win = parent_win
        self.wins = {}

    def rebuild(self, lines):
        """
        deprecated
        """
        pass # TODO

    def redraw(self, room):
        """
        called when the buffer changes or is
        resized (a complete redraw is needed)
        """
        if not self.visible:
            return
        win = self.wins[room.name].win
        win.clear()
        win.move(0, 0)
        for line in room.lines:
            self.add_line(room, line)

    def refresh(self, winname):
        if self.visible:
            self.wins[winname].refresh()

    def add_line(self, room, line):
        if not self.visible:
            return
        win = self.wins[room.name].win
        users = room.users
        if len(line) == 2:
            try:
                win.addstr('\n['+line[0].strftime("%H:%M:%S") + "] ")
                win.attron(curses.color_pair(8))
                win.addstr(line[1])
                win.attroff(curses.color_pair(8))
            except:pass
        elif len(line) == 3:
            for user in users:
                if user.nick == line[1]:
                    break
            try:
                try:win.addstr('\n['+line[0].strftime("%H:%M:%S") + "] <")
                except:pass
                length = len('['+line[0].strftime("%H:%M:%S") + "] <")
                try:win.attron(curses.color_pair(user.color))
                except:pass
                win.addstr(line[1])
                try:win.attroff(curses.color_pair(user.color))
                except:pass
                win.addstr("> ")
                win.addstr(line[2])
            except:pass

    def new_win(self, winname):
        newwin = Win(self.height, self.width, self.y, self.x, self.parent_win)
        newwin.win.idlok(True)
        newwin.win.scrollok(True)
        self.wins[winname] = newwin

    def resize(self, height, width, y, x, stdscr, visible):
        self.visible = visible
        if not visible:
            return
        for winname in self.wins.keys():
            self.wins[winname]._resize(height, width, y, x, stdscr)
            self.wins[winname].win.idlok(True)
            self.wins[winname].win.scrollok(True)

class Input(Win):
    """
    """
    def __init__(self, height, width, y, x, stdscr, visible):
        Win.__init__(self, height, width, y, x, stdscr)
        self.visible = visible
        self.history = []
        self.text = u''
        self.pos = 0
        self.histo_pos = 0

    def resize(self, height, width, y, x, stdscr, visible):
        self.visible = visible
        if not visible:
            return
        self._resize(height, width, y, x, stdscr)
        self.win.clear()
        self.win.addnstr(0, 0, self.text.encode('utf-8'), self.width-1)

    def key_dc(self):
        """delete char"""
        if self.pos == len(self.text):
            return
        (y, x) = self.win.getyx()
        self.text = self.text[:self.pos]+self.text[self.pos+1:]
        self.win.delch(y, x)
        self.refresh()

    def key_up(self):
        if not len(self.history):
            return
        self.win.clear()
        if self.histo_pos >= 0:
            self.histo_pos -= 1
        self.text = self.history[self.histo_pos+1]
        if len(self.text) >= self.width-1:
            self.win.addstr(self.history[self.histo_pos+1][:self.width-1].encode('utf-8'))
        else:
            self.win.addstr(self.history[self.histo_pos+1].encode('utf-8'))
        self.pos = len(self.text)
        self.refresh()

    def key_down(self):
        if not len(self.history):
            return
        self.win.clear()
        if self.histo_pos < len(self.history)-1:
            self.histo_pos += 1
            self.text = self.history[self.histo_pos]
            if len(self.text) >= self.width-1:
                self.win.addstr(self.history[self.histo_pos][:self.width-1].encode('utf-8'))
            else:
                self.win.addstr(self.history[self.histo_pos].encode('utf-8'))
            self.pos = len(self.text)
        else:
            self.histo_pos = len(self.history)-1
            self.text = u''
            self.pos = 0
        self.refresh()

    def key_home(self):
        self.pos = 0
        if len(self.text) >= self.width-1:
            txt = self.text[:self.width-1]
            self.clear_text()
            self.win.addstr(txt)
        self.win.move(0, 0)
        self.refresh()

    def key_end(self):
        self.pos = len(self.text)
        if len(self.text) >= self.width-1:
            txt = self.text[-(self.width-1):]
            self.clear_text()
            self.win.addstr(txt)
            self.win.move(0, self.width-1)
        else:
            self.win.move(0, len(self.text))
        self.refresh()

    def key_left(self):
        (y, x) = self.win.getyx()
        if self.pos > 0:
            self.pos -= 1
            if x == 0:
                txt = self.text[self.pos:self.pos+self.width-1]
                self.clear_text()
                self.win.addstr(txt)
                self.win.move(y, 0)
            else:
                self.win.move(y, x-1)
            self.refresh()

    def key_right(self):
        (y, x) = self.win.getyx()
        if self.pos < len(self.text):
            self.pos += 1
            if x == self.width-1:
                txt = self.text[self.pos-(self.width-1):self.pos]
                open('fion', 'w').write(txt)
                self.clear_text()
                self.win.addstr(txt)
                self.win.move(y, self.width-1)
            else:
                self.win.move(y, x+1)
            self.refresh()

    def key_backspace(self):
        (y, x) = self.win.getyx()
        if len(self.text) > 0 and self.pos != 0:
            self.text = self.text[:self.pos-1]+self.text[self.pos:]
            self.pos -= 1
            self.win.delch(y, x-1)
            self.refresh()

    def do_command(self, key):
        (y, x) = self.win.getyx()
        if x == self.width-1:
            self.win.delch(0, 0)
            self.win.move(y, x-1)
            x -= 1
        try:
            self.text = self.text[:self.pos]+key.decode('utf-8')+self.text[self.pos:]
            self.win.insstr(key)
        except:
            return
        self.win.move(y, x+1)
        self.pos += 1
        self.refresh()

    def get_text(self):
        txt = self.text
        self.text = u''
        self.pos = 0
        self.history.append(txt)
        self.histo_pos = len(self.history)-1
        return txt.encode('utf-8')

    def refresh(self):
        if not self.visible:
            return
        self.win.noutrefresh()

    def clear_text(self):
        self.win.clear()

class Window(object):
    """
    The whole "screen" that can be seen at once in the terminal.
    It contains an userlist, an input zone and a chat zone
    """
    def __init__(self, stdscr):
        """
        name is the name of the Tab, and it's also
        the JID of the chatroom.
        A particular tab is the "Info" tab which has no
        name (None). This info tab should be unique.
        The stdscr should be passed to know the size of the
        terminal
        """
        self.size = (self.height, self.width) = stdscr.getmaxyx()
        if self.height < 10 or self.width < 60:
            visible = False
        else:
            visible = True
        if visible:
            stdscr.attron(curses.color_pair(2))
            stdscr.vline(1, 9*(self.width/10), curses.ACS_VLINE, self.height-2)
            stdscr.attroff(curses.color_pair(2))
        self.user_win = UserList(self.height-3, (self.width/10)-1, 1, 9*(self.width/10)+1, stdscr, visible)
        self.topic_win = Topic(1, self.width, 0, 0, stdscr, visible)
        self.info_win = RoomInfo(1, self.width, self.height-2, 0, stdscr, visible)
        self.text_win = TextWin(self.height-3, (self.width/10)*9, 1, 0, stdscr, visible)
        self.input = Input(1, self.width, self.height-1, 0, stdscr, visible)

    def resize(self, stdscr):
        """
        Resize the whole tabe. i.e. all its sub-windows
        """
        self.size = (self.height, self.width) = stdscr.getmaxyx()
        if self.height < 10 or self.width < 60:
            visible = False
        else:
            visible = True
        if visible:
            stdscr.attron(curses.color_pair(2))
            stdscr.vline(1, 9*(self.width/10), curses.ACS_VLINE, self.height-2)
            stdscr.attroff(curses.color_pair(2))
        self.user_win.resize(self.height-3, (self.width/10)-1, 1, 9*(self.width/10)+1, stdscr, visible)
        self.topic_win.resize(1, self.width, 0, 0, stdscr, visible)
        self.info_win.resize(1, self.width, self.height-2, 0, stdscr, visible)
        self.text_win.resize(self.height-3, (self.width/10)*9, 1, 0, stdscr, visible)
        self.input.resize(1, self.width, self.height-1, 0, stdscr, visible)

    def refresh(self, rooms):
        """
        'room' is the current one
        """
        room = rooms[0]         # get current room
        self.text_win.redraw(room)
        self.text_win.refresh(room.name)
        self.user_win.refresh(room.users)
        self.topic_win.refresh(room.topic)
        self.info_win.refresh(rooms, room)
        self.input.refresh()

    def do_command(self, key):
        self.input.do_command(key)
        self.input.refresh()

    def new_room(self, room):
        self.text_win.new_win(room.name)
