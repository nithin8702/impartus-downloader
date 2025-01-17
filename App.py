#!/usr/bin/env python3
import tkinter.messagebox
import tkinter as tk
from tkinter import font
from functools import partial
from tksheet import Sheet
import os
import ast
import threading

from config import Config
from impartus import Impartus
from utils import Utils


class App:
    def __init__(self):
        # ui elements
        self.user_box = None
        self.pass_box = None
        self.url_box = None
        self.show_videos_button = None

        # element groups
        self.frame_auth = None
        self.frame_videos = None
        self.sheet = None

        # sort options
        self.sort_by = None
        self.sort_order = None

        self.threads = list()

        # root container
        self.app = None

        # backend
        self.impartus = None
        self.conf = None

        # fields
        self.columns = None

        self.colorscheme_config = None
        self.colorscheme = None

        self._init_backend()
        self._init_ui()

    def _init_backend(self):
        """
        backend initialization.
        """
        self.impartus = Impartus()
        self.conf = Config.load()

        self.columns = {k: v for k, v in enumerate([
            # data fields
            {'name': 'Subject', 'show': True, 'type': 'data', 'mapping': 'subjectNameShort', 'title_case': False,
             'sortable': True, 'truncate': False, 'header': 'Subject'},
            {'name': 'Lecture #', 'show': True, 'type': 'data', 'mapping': 'seqNo', 'title_case': False,
             'sortable': True, 'truncate': False, 'header': 'Lecture #'},
            {'name': 'Professor', 'show': True, 'type': 'data', 'mapping': 'professorName_raw', 'title_case': True,
             'sortable': True, 'truncate': True, 'header': 'Professor'},
            {'name': 'Topic', 'show': True, 'type': 'data', 'mapping': 'topic_raw', 'title_case': True,
             'sortable': True, 'truncate': True, 'header': 'Topic'},
            {'name': 'Date', 'show': True, 'type': 'data', 'mapping': 'startDate', 'title_case': False,
             'sortable': True, 'truncate': False, 'header': 'Date'},
            {'name': 'Duration', 'show': True, 'type': 'data', 'mapping': 'actualDurationReadable', 'title_case': False,
             'sortable': True, 'truncate': False, 'header': 'Duration'},
            {'name': 'Tracks', 'show': True, 'type': 'data', 'mapping': 'tapNToggle', 'title_case': False,
             'sortable': True, 'truncate': False, 'header': 'Tracks'},
            # progress bar
            {'name': 'Downloaded?', 'show': True, 'type': 'progressbar', 'title_case': False, 'sortable': True,
             'header': 'Downloaded?'},
            # buttons
            {'name': 'Download Video', 'show': True, 'type': 'button', 'function': self.download_video,
             'sortable': False, 'text': '⬇', 'header': 'Video'},
            {'name': 'Open Folder', 'show': True, 'type': 'button', 'function': self.open_folder,
             'sortable': False, 'text': '⏏', 'header': 'Folder'},
            {'name': 'Play Video', 'show': True, 'type': 'button', 'function': self.play_video,
             'sortable': False, 'text': '▶', 'header': 'Video'},
            {'name': 'Download Slides', 'show': True, 'type': 'button', 'function': self.download_slides,
             'sortable': False, 'text': '⬇', 'header': 'Slides'},
            {'name': 'Show Slides', 'show': True, 'type': 'button', 'function': self.show_slides,
             'sortable': False, 'text': '▤', 'header':  'Slides'},
            {'name': 'download_video_state', 'show': False, 'type': 'state', 'header': 'download_video_state'},
            {'name': 'open_folder_state', 'show': False, 'type': 'state', 'header': 'open_folder_state'},
            {'name': 'play_video_state', 'show': False, 'type': 'state', 'header': 'play_slides_state'},
            {'name': 'download_slides_state', 'show': False, 'type': 'state', 'header': 'download_slides_state'},
            {'name': 'show_slides_state', 'show': False, 'type': 'state', 'header': 'show_slides_state'},
            # index
            {'name': 'Index', 'show': False, 'type': 'auto', 'header': 'Index'},
            # video / slides data
            {'name': 'metadata', 'show': False, 'type': 'metadata', 'header': 'metadata'},
        ])}
        self.headers = [x['header'] for x in self.columns.values()]
        self.names = [x['name'] for x in self.columns.values()]

    def _init_ui(self):
        """
        UI initialization.
        """
        self.colorscheme_config = Config.load('color-schemes.conf')
        self.colorscheme = self.colorscheme_config.get(self.colorscheme_config.get('default'))

        self.app = tkinter.Tk()
        pad = 3
        self.screen_width = self.app.winfo_screenwidth() - pad
        self.screen_height = self.app.winfo_screenheight() - pad
        geometry = '{}x{}+0+0'.format(self.screen_width, self.screen_height)
        self.app.geometry(geometry)
        self.app.title('Impartus Downloader')
        self.app.rowconfigure(0, weight=0)
        self.app.rowconfigure(1, weight=1)
        self.app.columnconfigure(0, weight=1)
        self.app.config(bg=self.colorscheme['root']['bg'])

        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family=self.conf.get('content_font'), size=14)
        text_font = font.nametofont("TkTextFont")
        text_font.configure(family=self.conf.get('content_font'), size=14)

        self.add_auth_frame(self.app)

        self.app.mainloop()

    def add_auth_frame(self, anchor):
        """
        Adds authentication widgets and blank frame for holding video/lectures data.
        """
        cs = self.colorscheme
        label_options = {
            'padx': 5,
            'pady': 5,
            'sticky': 'ew',
        }
        entry_options = {
            'padx': 5,
            'pady': 5,
        }

        color_options = {
            'fg': cs['root']['fg'],
            'bg': cs['root']['bg'],
        }

        frame_auth = tk.Frame(anchor, padx=0, pady=0, bg=cs['root']['bg'])
        frame_auth.grid(row=0, column=0)
        self.frame_auth = frame_auth

        frame_videos = tk.Frame(anchor, padx=0, pady=0, bg=cs['root']['bg'])
        frame_videos.grid(row=1, column=0, sticky='nsew')
        self.frame_videos = frame_videos

        # URL Label and Entry box.
        tk.Label(frame_auth, text='URL', **color_options).grid(row=0, column=0, **label_options)
        url_box = tk.Entry(frame_auth, width=30, **color_options)
        url_box.insert(tk.END, self.conf.get('impartus_url'))
        url_box.grid(row=0, column=1, **entry_options)
        self.url_box = url_box

        # Login Id Label and Entry box.
        tk.Label(frame_auth, text='Login (email) ', **color_options).grid(row=1, column=0, **label_options)
        user_box = tk.Entry(frame_auth, width=30, **color_options)
        user_box.insert(tk.END, self.conf.get('login_email'))
        user_box.grid(row=1, column=1, **entry_options)
        self.user_box = user_box

        tk.Label(frame_auth, text='Password ', **color_options).grid(row=2, column=0, **label_options)
        pass_box = tk.Entry(frame_auth, text='', show="*", width=30, **color_options)
        pass_box.bind("<Return>", self.get_videos)
        pass_box.grid(row=2, column=1, **entry_options)
        self.pass_box = pass_box

        show_videos_button = tk.Button(frame_auth, text='Show Videos', command=self.get_videos)
        show_videos_button.grid(row=2, column=2)
        self.show_videos_button = show_videos_button

        # set focus to user entry if it is empty, else to password box.
        if user_box.get() == '':
            user_box.focus()
        else:
            pass_box.focus()

    def get_videos(self, event=None):  # noqa
        """
        Callback function for 'Show Videos' button.
        Fetch video/lectures available to the user and display on the UI.
        """

        self.show_videos_button.config(state='disabled')
        username = self.user_box.get()
        password = self.pass_box.get()
        root_url = self.url_box.get()
        if username == '' or password == '' or root_url == '':
            return

        if not self.impartus.session:
            success = self.impartus.authenticate(username, password, root_url)
            if not success:
                self.impartus.session = None
                tkinter.messagebox.showerror('Error', 'Error authenticating, see console logs for details.')
                self.show_videos_button.config(state='normal')
                return
        subjects = self.impartus.get_subjects(root_url)

        # show table of videos under frame_videos
        frame = self.frame_videos
        self.set_display_widgets(subjects, root_url, frame)
        self.show_videos_button.config(state='normal', text='Reload')

    def sort_table(self, args):
        """
        Sorts the table content.
        """
        col = args[1]
        self.sheet.deselect("all")
        if not self.columns[col].get('sortable'):
            return
        sort_by = self.names[col]
        if sort_by == self.sort_by:
            sort_order = 'asc' if self.sort_order == 'desc' else 'desc'
        else:
            sort_order = 'desc'
        self.sort_by = sort_by
        self.sort_order = sort_order

        reverse = True if sort_order == 'desc' else False

        table_data = self.sheet.get_sheet_data()
        table_data.sort(key=lambda x: x[col], reverse=reverse)

        self.set_headers(sort_by, sort_order)
        self.set_button_status()

    def set_display_widgets(self, subjects, root_url, anchor):
        """
        Create the table/sheet.
        Fill in the data for table content, Set the buttons and their states.
        """
        cs = self.colorscheme

        sheet = Sheet(
            anchor, frame_bg=cs['table']['bg'],
            table_bg=cs['table']['bg'],
            table_fg=cs['table']['fg'],
            table_grid_fg=cs['table']['grid'],
            top_left_bg=cs['header']['bg'],
            top_left_fg=cs['header']['bg'],
            header_bg=cs['header']['bg'],
            header_fg=cs['header']['fg'],
            header_font=(self.conf.get("content_font"), 12, "bold"),
            font=(self.conf.get('content_font'), 14, "normal"),
            align='center',
            header_grid_fg=cs['table']['grid'],
            index_grid_fg=cs['table']['grid'],
            header_align='center',
            empty_horizontal=0,
            empty_vertical=0,
            header_border_fg=cs['table']['grid'],
            index_border_fg=cs['table']['grid'],
        )
        self.sheet = sheet

        sheet.enable_bindings((
            "single_select",
            "column_select",
            "column_width_resize",
            "row_height_resize",
            "rc_select"
        ))

        self.set_headers()

        indexes = [x for x, v in self.columns.items() if v['show']]
        sheet.display_columns(indexes=indexes, enable=True)
        anchor.columnconfigure(0, weight=1)
        anchor.rowconfigure(0, weight=1)

        row = 0
        for subject in subjects:
            videos = self.impartus.get_videos(root_url, subject)
            slides = self.impartus.get_slides(root_url, subject)
            video_slide_mapping = self.impartus.map_slides_to_videos(videos, slides)

            videos = {x['ttid']:  x for x in videos}

            for ttid, video_metadata in videos.items():
                video_metadata = Utils.add_fields(video_metadata, video_slide_mapping)
                video_metadata = Utils.sanitize(video_metadata)

                video_path = self.impartus.get_mkv_path(video_metadata)
                slides_path = self.impartus.get_slides_path(video_metadata)

                video_exists = os.path.exists(video_path)
                slides_exist = video_slide_mapping.get(ttid)
                slides_exist_on_disk, slides_path = self.impartus.slides_exist_on_disk(slides_path)

                metadata = {
                    'video_metadata': video_metadata,
                    'video_path': video_path,
                    'video_exists': video_exists,
                    'slides_exist': slides_exist,
                    'slides_exist_on_disk': slides_exist_on_disk,
                    'slides_url': video_slide_mapping.get(ttid),
                    'slides_path': slides_path,
                }
                row_items = list()
                button_states = list()
                for col, item in self.columns.items():
                    text = ''
                    if item['type'] == 'auto':
                        text = row
                    if item['type'] == 'data':
                        text = video_metadata[item['mapping']]
                        # title case
                        text = text.strip().title() if item.get('title_case') else text

                        # truncate long fields
                        if item['truncate'] and len(text) > self.conf.get('max_content_chars'):
                            text = '{}..'.format(text[0:self.conf.get('max_content_chars')])
                    elif item['type'] == 'progressbar':
                        value = 100 if video_exists else 0
                        text = self.progress_bar_text(value)
                    elif item['type'] == 'button':
                        button_states.append(self.get_button_state(
                            self.names[col], video_exists, slides_exist, slides_exist_on_disk)
                        )
                        text = item.get('text')
                    elif item['type'] == 'state':
                        text = button_states.pop(0)
                    elif item['type'] == 'metadata':
                        text = metadata

                    row_items.append(text)
                sheet.insert_row(values=row_items, idx='end')
                row += 1

        self.reset_column_sizes()
        self.decorate()

        sheet.extra_bindings('column_select', self.sort_table)
        sheet.extra_bindings('cell_select', self.on_click_button_handler)

        # update button status
        self.set_button_status()

        sheet.grid(row=0, column=0, sticky='nsew')

    def set_headers(self, sort_by=None, sort_order=None):
        """
        Set the table headers.
        """
        # set column title to reflect sort status
        headers = self.headers.copy()
        for x, h in enumerate(headers):
            
            if not self.columns[x].get('sortable'):
                continue

            # only sortable headers.
            sort_icon = None
            if h == sort_by:
                sort_icon = '▼' if sort_order == 'desc' else '▲'
            else:
                sort_icon = '⇅'
            headers[x] += ' {}'.format(sort_icon)
        self.sheet.headers(headers)

    def decorate(self):
        """
        calls multiple ui related tweaks.
        """
        self.odd_even_color()
        self.progress_bar_color()

    def progress_bar_color(self):
        """
        Set progress bar color.
        """
        col = self.names.index('Downloaded?')
        num_rows = self.sheet.total_rows()
        cs = self.colorscheme

        for row in range(num_rows):
            odd_even_bg = cs['odd_row']['bg'] if row % 2 else cs['even_row']['bg']
            self.sheet.highlight_cells(
                row, col, fg=cs['progressbar']['fg'], bg=odd_even_bg, redraw=True)
            self.sheet.align_columns(col, 'w')

    def odd_even_color(self):
        """
        Apply odd/even colors for table for better looking UI.
        """
        cs = self.colorscheme
        num_rows = self.sheet.total_rows()

        self.sheet.highlight_rows(
            list(range(0, num_rows, 2)),
            bg=cs['even_row']['bg'],
            fg=cs['even_row']['fg']
        )
        self.sheet.highlight_rows(
            list(range(1, num_rows, 2)),
            bg=cs['odd_row']['bg'],
            fg=cs['odd_row']['fg']
        )

    def reset_column_sizes(self):
        """
        Adjust column sizes after data has been filled.
        """
        # resize cells
        self.sheet.set_all_cell_sizes_to_text()
        # reset column widths to fill the screen
        pad = 50
        extra_width = self.frame_videos.winfo_width() - sum(self.sheet.get_column_widths()) - pad

        # adjust extra width only to data columns.
        sortable_columns = {x: True for x, v in self.columns.items() if v.get('show') and not v['type'] == 'progressbar'}
        for col_num, col_width in enumerate(self.sheet.get_column_widths()):
            if sortable_columns.get(col_num):
                self.sheet.column_width(col_num, col_width + extra_width // len(sortable_columns))

    def set_button_status(self):
        """
        reads the states of the buttons from the hidden state columns, and sets the button states appropriately.
        """
        col_indexes = [x for x, v in enumerate(self.columns.values()) if v['type'] == 'state']
        num_buttons = len(col_indexes)
        for row, row_item in enumerate(self.sheet.get_sheet_data()):
            for col in col_indexes:
                # data set via sheet.insert_row retains tuple/list's element data type,
                # data set via sheet.set_cell_data makes everything a string.
                # Consider everything coming out of a sheet as string to avoid any issues.
                state = str(row_item[col])

                if state == 'True':
                    self.enable_button(row, col - num_buttons, redraw=False)
                elif state == 'False':
                    self.disable_button(row, col - num_buttons, redraw=False)
        self.sheet.redraw()

    def get_button_state(self, key, video_exists, slides_exist, slides_exist_on_disk):  # noqa
        """
        Checks to identify when certain buttons should be enabled/disabled.
        """
        state = True
        if key == 'Download Video' and video_exists:
            state = False
        elif key == 'Open Folder' and not video_exists:
            state = False
        elif key == 'Play Video' and not video_exists:
            state = False
        elif key == 'Download Slides' and (slides_exist_on_disk or not slides_exist):
            state = False
        elif key == 'Show Slides' and not slides_exist_on_disk:
            state = False
        return state

    def on_click_button_handler(self, args):
        """
        On click handler for all the buttons, calls the corresponding function as defined by self.columns
        """
        (event, row, col) = args
        self.sheet.deselect('all', redraw=True)

        if self.columns[col]['type'] != 'button':
            return

        state_button_col = col + len([x for x, v in self.columns.items() if v['type'] == 'state'])
        state = self.sheet.get_cell_data(row, state_button_col)
        if state == 'False':    # data read from sheet is all string.
            print("[{},{}] button disabled!".format(row, col))
            return

        # disable the pressed button (only Download buttons)
        if self.names[col] in ['Download Video', 'Download Slides']:
            self.disable_button(row, col)

        func = self.columns[col]['function']
        func(row, col)

    def disable_button(self, row, col, redraw=True):
        """
        Disable a button given it's row/col position.
        """
        cs = self.colorscheme
        self.sheet.highlight_cells(
            row, col, bg=cs['disabled']['bg'],
            fg=cs['disabled']['fg'],
            redraw=redraw
        )
        # update state field.
        state_button_col = col + len([x for x, v in self.columns.items() if v['type'] == 'state'])
        self.sheet.set_cell_data(row, state_button_col, False, redraw=redraw)

    def enable_button(self, row, col, redraw=True):
        """
        Enable a button given it's row/col position.
        """
        cs = self.colorscheme
        odd_even_bg = cs['odd_row']['bg'] if row % 2 else cs['even_row']['bg']
        odd_even_fg = cs['odd_row']['fg'] if row % 2 else cs['even_row']['fg']
        self.sheet.highlight_cells(row, col, bg=odd_even_bg, fg=odd_even_fg, redraw=redraw)

        # update state field.
        state_button_col = col + len([x for x, v in self.columns.items() if v['type'] == 'state'])
        self.sheet.set_cell_data(row, state_button_col, True, redraw=redraw)

    def get_index(self, row):
        """
        Find the values stored in the hidden column named 'Index', given a row record.
        In case the row value has been updated due to sorting the table, Index field helps identify the new location
        of the associated record.
        """
        # find where is the Index column
        index_col = self.names.index('Index')
        # original row value as per the index column
        return self.sheet.get_cell_data(row, index_col)

    def get_row_after_sort(self, index_value):
        # find the new correct location of the row_index
        col_index = self.names.index('Index')
        col_data = self.sheet.get_column_data(col_index)
        return col_data.index(index_value)

    def progress_bar_text(self, value):
        """
        return progress bar text, calls the unicode/ascii implementation.
        """
        if self.conf.get('progress_bar') == 'unicode':
            text = self.progress_bar_text_unicode(value)
        else:
            text = self.progress_bar_text_ascii(value)
        percent_text = '{:3d}%'.format(value)
        pad = ' ' * 4   # to keep the cell wide enough even with all videos at 0%.
        return '[{}] {}{}'.format(text, percent_text, pad)

    def progress_bar_text_ascii(self, value):   # noqa
        """
        progress bar implementation with ascii characters.
        """
        bars = 50
        # ascii char 'l' takes up least width for most fonts.
        return ' {} '.format('l' * (value * bars // 100))

    def progress_bar_text_unicode(self, value):    # noqa
        """
        progress bar implementation with unicode blocks.
        """
        chars = ['▏', '▎', '▍', '▌', '▋', '▊', '▉', '█']

        # 1 unicode block = 8 percent values. => 13 unicode blocks needed to represent counter 100, with right half of
        # the last block being empty.
        # To make it visually symmetric, we add one regular whitespace to the left.
        unicode_space = ' '
        ascii_space = ' '
        if value > 0:
            progress_text = '{}{}'.format(chars[-1] * (value // 8), chars[value % 8])
            empty_text = '{}'.format(unicode_space * (13-len(progress_text)))
            full_text = '{}{}{}'.format(ascii_space, progress_text, empty_text)
        else:
            # same 13 chars of unicode blocks, and 1 regular whitespace.
            full_text = '{}{}'.format(ascii_space, unicode_space * 13)
        return full_text

    def progress_bar_callback(self, count, row, col):
        """
        Callback function passed to the backend, where it computes the download progress.
        Every time the function is called, it will update the progress bar value.
        """
        updated_row = self.get_row_after_sort(row)
        new_text = self.progress_bar_text(count)
        if new_text != self.sheet.get_cell_data(updated_row, col):
            self.sheet.set_cell_data(updated_row, col, new_text, redraw=True)

    def _download_video(self, video_metadata, filepath, root_url, row, col):
        """
        Download a video in a thread. Update the UI upon completion.
        """

        # create a new Impartus session reusing existing token.
        imp = Impartus(self.impartus.token)
        pb_col = None
        for i, item in enumerate(self.columns.values()):
            if item['type'] == 'progressbar':
                pb_col = i
                break
        # voodoo alert:
        # It is possible for user to sort the table while download is in progress.
        # In such a case, the row index supplied to the function call won't match the row index
        # required to update the correct progressbar/open/play buttons, which now exists at a new
        # location.
        # The hidden column index keeps the initial row index, and remains unchanged.
        # Use row_index to identify the new correct location of the progress bar.
        row_index = self.get_index(row)
        imp.process_video(video_metadata, filepath, root_url, 0,
                          partial(self.progress_bar_callback, row=row_index, col=pb_col))

        # download complete, enable open / play buttons
        updated_row = self.get_row_after_sort(row_index)
        self.enable_button(updated_row, self.names.index('Open Folder'))
        self.enable_button(updated_row, self.names.index('Play Video'))

    def download_video(self, row, col):
        """
        callback function for Download button.
        Creates a thread to download the request video.
        """
        data = self.read_metadata(row)

        video_metadata = data.get('video_metadata')
        filepath = data.get('video_path')
        root_url = self.url_box.get()

        # note: args is a tuple.
        thread = threading.Thread(target=self._download_video, args=(video_metadata, filepath, root_url, row, col,))
        self.threads.append(thread)
        thread.start()

    def _download_slides(self, ttid, file_url, filepath, root_url, row):
        """
        Download a slide doc in a thread. Update the UI upon completion.
        """
        # create a new Impartus session reusing existing token.
        imp = Impartus(self.impartus.token)
        if imp.download_slides(ttid, file_url, filepath, root_url):
            # download complete, enable show slides buttons
            self.enable_button(row, self.names.index('Show Slides'))
        else:
            tkinter.messagebox.showerror('Error', 'Error downloading slides, see console logs for details.')
            self.enable_button(row, self.names.index('Download Slides'))

    def download_slides(self, row, col):
        """
        callback function for Download button.
        Creates a thread to download the request video.
        """
        data = self.read_metadata(row)

        video_metadata = data.get('video_metadata')
        ttid = video_metadata['ttid']
        file_url = data.get('slides_url')
        filepath = data.get('slides_path')
        root_url = self.url_box.get()

        # note: args is a tuple.
        thread = threading.Thread(target=self._download_slides,
                                  args=(ttid, file_url, filepath, root_url, row,))
        self.threads.append(thread)
        thread.start()

    def read_metadata(self, row):
        """
        We saved a hidden column 'metadata' containing metadata for each record.
        Extract it, and eval it as python dict.
        """
        metadata_col = self.names.index('metadata')
        data = self.sheet.get_cell_data(row, metadata_col)
        return ast.literal_eval(data)

    def open_folder(self, row, col):
        """
        fetch video_path's folder from metadata column's cell and open system launcher with it.
        """
        data = self.read_metadata(row)
        video_folder_path = os.path.dirname(data.get('video_path'))
        Utils.open_file(video_folder_path)

    def play_video(self, row, col):
        """
        fetch video_path from metadata column's cell and open system launcher with it.
        """
        data = self.read_metadata(row)
        Utils.open_file(data.get('video_path'))

    def show_slides(self, row, col):
        """
        fetch slides_path from metadata column's cell and open system launcher with it.
        """
        data = self.read_metadata(row)
        Utils.open_file(data.get('slides_path'))


if __name__ == '__main__':
    App()
