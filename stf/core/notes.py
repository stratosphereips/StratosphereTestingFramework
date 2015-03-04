import persistent
import BTrees.IOBTree
import tempfile
import os

from stf.common.out import *

###############################
###############################
###############################
class Note(persistent.Persistent):
    """
    The Note
    """
    def __init__(self, id):
        self.id = id
        self.text = ""

    def get_id(self):
        return self.id

    def edit(self):
        # Create a new temporary file.
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.md')
        # Write the text that we have into the temp file
        tmp.write(self.text)
        tmp.file.flush()
        # Open the temporary file with the default editor, or with nano.
        os.system('"${EDITOR:-nano}" ' + tmp.name)
        # Go to the beginning of the file
        tmp.file.flush()
        tmp.file.seek(0)
        self.text = tmp.file.read()
        # Finally, remove the temporary file.
        os.remove(tmp.name)

    def get_text(self):
        return self.text 

    def delete_text(self):
        """ Delete the text of the note """
        self.text = ""

    def get_note(self):
        """ Return text of the note """
        return self.text

    def get_short_note(self):
        """ Return text of the note until the first enter"""
        enter = self.text.index('\n')
        return self.text[:enter]

    def __repr__(self):
        return self.text

###############################
###############################
###############################
class Group_of_Notes(persistent.Persistent):
    """ This class holds all the notes"""
    def __init__(self):
        self.notes = BTrees.IOBTree.BTree()
        # We are not storing here the relationship between the note and the object to which the note is related. The relationship is stored in the other object.
        
    def get_note(self, note_id):
        """ Return all the notes """
        try:
            return self.notes[note_id]
        except KeyError:
            return False

    def get_notes(self):
        """ Return all the notes """
        return self.notes.values()

    def new_note(self):
        """ Creates a new note and returns its id """
        # Get the new id for this note
        try:
            # Get the id of the last note in the database
            note_id = self.notes[list(self.notes.keys())[-1]].get_id() + 1
        except (KeyError, IndexError):
            note_id = 0
        new_note = Note(note_id)
        # Store it
        self.notes[note_id] = new_note
        return note_id
    
    def delete_note(self, note_id):
        try:
            # Just in case delete the text of the note before
            note = self.notes[note_id]
            note.delete_text()
            # Delete the note
            self.notes.pop(note_id)
        except KeyError:
            print_error('No such note id.')

    def edit_note(self, note_id):
        """ Edit a note """
        try:
            note = self.notes[note_id]
            note.edit()
        except KeyError:
            print_error('No such note id')

    def get_short_note(self, note_id):
        try:
            note = self.notes[note_id]
            return note.get_short_note()
        except KeyError:
            return ''

    def list_notes(self):
        """ List all the notes """
        rows = []
        print_info('Note Id | Text')
        for note in self.get_notes():
            print'Note id {}'.format(note.get_id())
            print '##############'
            print'{}'.format(note.get_text())


__notes__ = Group_of_Notes()
