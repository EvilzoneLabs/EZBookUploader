#!/usr/bin/python
from gi.repository import Gtk
import os

class QuitDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Quit?", parent, 0,(Gtk.STOCK_CANCEL, \
                         Gtk.ResponseType.CANCEL,Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.set_default_size(150, 100)
        label = Gtk.Label("Are you sure you want to quit?")
        box = self.get_content_area()
        box.add(label)
        self.show_all()

class EvilWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Evilzone Ebook Uploader")
        self.set_size_request(600, 350)
        self.set_icon_from_file('favicon.png')
        self.set_border_width(10)
#        self.connect("delete-event", Gtk.main_quit)
#        self.connect("delete-event", self.quit)

        #create a vertical box to hold it all
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        vbox.set_visible(True)
        self.add(vbox)

        #lets get the introductions out of the way
        introbox = Gtk.Box(spacing=6)
        vbox.pack_start(introbox, True, False, 0)
        intro = Gtk.Label()
        intro.set_markup("Process, upload and post ebooks on <a" \
                 " href=\"https://evilzone.org\" title=\"Evilzone Forum and Community\">Evilzone</a>")
        introbox.pack_start(intro, True, False, 0)

        #lets add a frame to hold items with borders
        frame = Gtk.Frame()
        vbox.pack_start(frame, True, False, 0)

        #vertical box in a frame, easily supports borders. which is kewl
        fvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        frame.add(fvbox)

        #create horizontal box to hold input for files dialog
        hbox1 = Gtk.Box(spacing=6)
        #add horizontal box to vertical box
        fvbox.pack_start(hbox1,True, False, 6)

        #We actually can enter a file here or look for it
        self.fileentry = Gtk.Entry()
        self.fileentry.set_text('*')
        hbox1.pack_start(self.fileentry, True, True, 0)

        #ok, lets give them a book, or multiple if we so choose
        self.filebutton = Gtk.Button(label="Choose a Book")
        self.filebutton.set_size_request(30, 30)
        self.filebutton.set_border_width(5)
        self.filebutton.connect("clicked", self.choose_files)
        hbox1.pack_start(self.filebutton, False, False, 0)

        #now we need to get a folder, lets create space for it
        hbox2 = Gtk.Box(spacing=6)
        fvbox.pack_start(hbox2, True, False, 6)

        #entry point for a folder
        self.folderentry = Gtk.Entry()
        self.folderentry.set_text(os.path.expanduser('~'))
        hbox2.pack_start(self.folderentry, True, True, 0)

        #door way to the folder dialog.
        self.folderbutton =Gtk.Button(label='Select a Folder')
        self.folderbutton.set_size_request(30, 30)
        self.folderbutton.set_border_width(5)
        self.folderbutton.connect("clicked", self.choose_folder)
        hbox2.pack_start(self.folderbutton, False, False, 0)

        #this should load the file(s)/files in folder specified
        self.loadbutton = Gtk.Button(label= "Process and Upload the Book(s)")
        self.loadbutton.set_size_request(30, 30)
        self.loadbutton.set_border_width(5)
        self.loadbutton.connect("clicked", self.load_files)
        fvbox.pack_start(self.loadbutton, False, False, 0)

        #comeon fellaz, who needs progress.
        self.progressbar = Gtk.ProgressBar()
        fvbox.pack_start(self.progressbar, True, True, 6)

        #this box will hold checkboxes
        hbox3 = Gtk.Box(spacing=6)
        fvbox.pack_start(hbox3,True, True, 0)

        #maybe i don't need to upload it
        self.check_upload = Gtk.CheckButton("Upload the files after processing.")   
        self.check_upload.connect("toggled", self.is_upload)
        self.check_upload.set_active(True)
        hbox3.pack_start(self.check_upload, True, False, 6)

        #Or maybe, i don't need to post it on Evilzone.
        self.check_post = Gtk.CheckButton("Post new thread on Forum.")   
        self.check_post.connect("toggled", self.is_post)
        self.check_post.set_active(True)
        hbox3.pack_start(self.check_post, True, False, 6)

        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_size_request(100, 70)
        self.scrolledwindow.set_hexpand(True)
        self.scrolledwindow.set_vexpand(True)
        vbox.pack_start(self.scrolledwindow, True, True, 6)

        self.log = Gtk.TextView()
        self.log.set_border_width(5)
        #self.log.set_pixels_below_lines(2)
        self.log.set_editable(False)
        self.log.set_cursor_visible(False)
        self.log.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textbuffer = self.log.get_buffer()
        self.textbuffer.set_text("This is the debug and log window. Enjoy XD:\n"
                                  +"1) Choose a Book, Books or folder to process, upload and post to Evilzone.\n"
                                  +"2) Check the upload and/or post options.\n"
                                  +"3) Press \"Process and Upload the Books\" Button.\n"
                                  +"4) Log onto 'irc.evilzone.org' and wait for Spacecow to say 'balls'.\n")
        self.scrolledwindow.add(self.log)

    def choose_files(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a file",self,Gtk.FileChooserAction.OPEN, \
                  (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_select_multiple(True)
        #patterns = Gtk.FileFilter(); patterns.add_pattern("*.pdf")
        #Gtk.FileChooser.add_filter(dialog, patterns)
        self.add_filters(dialog)
        dialog.set_current_folder(os.getcwd())
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            #print("Open clicked")
            #print("File selected: " + str(dialog.get_filenames()))
            self.fileentry.set_text(str(dialog.get_filenames()))
            self.files = dialog.get_filenames()
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")
            self.files = []
        dialog.destroy()

    def add_filters(self, dialog):
        filter_pdf = Gtk.FileFilter()
        filter_pdf.set_name("Pdf files")
        filter_pdf.add_mime_type("application/pdf")
        dialog.add_filter(filter_pdf)
        filter_epub = Gtk.FileFilter()
        filter_epub.set_name("Epub files")
        filter_epub.add_mime_type("application/epub+zip")
        dialog.add_filter(filter_epub)
        filter_mobi = Gtk.FileFilter()
        filter_mobi.set_name("Mobi files")
        filter_mobi.add_pattern("*.mobi")
        dialog.add_filter(filter_mobi)
        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)            

    def is_post(self, widget):
        self.post_thread = widget.get_active()

    def load_files(self, widget):
        print("Loading")
        #calculate percentage for progress bar
    def choose_folder(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a folder", self,\
                 Gtk.FileChooserAction.SELECT_FOLDER, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, \
                 "Select", Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)
        dialog.set_current_folder(os.getcwd())
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            #print("Select clicked")
            #print("Folder selected: " + dialog.get_filename())
            self.folderentry.set_text(dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")
        dialog.destroy()
    def is_upload(self, widget):
       value = widget.get_active()
       #print(value)
       self.folderentry.set_editable(value)

    def quit(self, obj, event):
        import sys
        quit = QuitDialog(self)
        response = quit.run()
        if response == Gtk.ResponseType.OK:
            Gtk.main_quit
            sys.exit()#for some reason the window gets destroyed but program doesn't quit
        else:
            pass
        quit.destroy()

win = EvilWindow()
win.connect("delete-event", win.quit)
win.show_all()
Gtk.main()
