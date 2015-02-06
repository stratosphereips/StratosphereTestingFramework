
import ZODB, ZODB.FileStorage
import persistent
import transaction
from datetime import datetime

from stf.common.out import *
from stf.core.experiment import __experiments__



class Database:
    def __init__(self):
        storage = ZODB.FileStorage.FileStorage('/tmp/stf.zodb')
        db = ZODB.DB(storage)

        # During testing just create it on memory
        #db = ZODB.DB(None)

        connection = db.open()
        self.root = connection.root

        # Experiments
        self.root.experiments = __experiments__
        # Datasets
        # Connections
        # Models
        # Comparisons
        transaction.commit()
       
