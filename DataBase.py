#########################################################
# CUED Python Statistical Spoken Dialogue System Software
#########################################################
#
# Copyright 2015-16  Cambridge University Engineering Department 
# Dialogue Systems Group
#
# Principal Authors:  Dongho Kim and David Vandyke
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#########################################################

'''
DataBase.py - loads db file into a dict 
====================================================

Author: Dongho Kim  (Copyright CUED Dialogue Systems Group 2015)

.. Note::
    Called by :class:`Settings` to load database into global variable db

.. seealso:: CUED Imports/Dependencies: 

    import :class:`ContextLogger`

************************

'''

import operator
import math

import ContextLogger
logger = ContextLogger.getLogger('')


def get_slot(string):
    '''Utility function for location parsing in database.

    :param string: e.g. 'north("52.222544,0.131237")'
    :returns: (str) e.g. 'north'
    '''
    slot = string.split('(')
    return slot[0]


def get_field(string):
    '''Utility function for extracting arguments from strings. 
    '''
    if '"' in string:
        temp = string.split('"')
        return temp[1].lower()
    else:
        temp = string.split('(')
        temp = temp[1]
        temp = temp.split(')')
        temp = temp[0]
        return temp.lower()


def get_dist(c1, c2):
    '''Utility function for calculating the distance between 2 points on Earth.

    :param c1: (2-tuple floats) latitude,longitude
    :param c2: (2-tuple floats) latitude,longitude
    :returns: (float) distance
    '''
    lat1 = c1[0]
    lon1 = c1[1]
    lat2 = c2[0]
    lon2 = c2[1]
    dlat = (lat1-lat2)*math.pi/180
    dlon = (lon1-lon2)*math.pi/180
    x = math.sin(dlat/2)
    y = math.sin(dlon/2)
    a = x ** 2 + math.cos(lat1*math.pi/180) * math.cos(lat2*math.pi/180) * y ** 2
    return 2 * 6371 * math.atan2(math.sqrt(a), math.sqrt(1-a))


class DataBase():
    '''Reads into a Python dictionary or TinyDB object via internal self._loaddb() method. Also sets member variable *ent_by_feat_method* which subsequently controls how database is interacted with (*text based* or using *tinydb*).  

    :param dbfile: (str) path to database file
    '''
    def __init__(self, dbfile):
        if '.json' in dbfile:
            # use the tinydb json database format
            from tinydb import TinyDB,where
            logger.error("USE THE OLD .txt METHOD: Bugs exist with queries in tinydb format. Not clear for now that we need more domains or gain anything by integrating json format -- on hold!")
            self.ent_by_feat_method = 'tinydb'
            self.db = TinyDB(dbfile)
            global opts 
            opts =  {   '=': operator.eq,
                        '!=': operator.ne}

        else:
            self.ent_by_feat_method = 'txt'
            self.db = self._loaddb(dbfile)


    def _loaddb(self, dbfile):
        f = open(dbfile)
        lines = f.readlines()
        db = {}
        location = {}
        for i in range(len(lines)):
            line = lines[i]

            # Load location
            if line.startswith('id("00")'):
                i += 1
                line = lines[i]
                while '(' in line:
                    # SFR and SFH have slightly different format on this id("00") -- area's are wrapped in ""
                    line = self.__fix_SFR_SFH_areas(line)
                    locname = get_slot(line)
                    loc = get_field(line)
                    loc = loc.split(',')
                    loc[0] = float(loc[0])
                    loc[1] = float(loc[1])
                    location[locname] = loc
                    i += 1
                    line = lines[i]

            # New item
            if line.startswith('id('):
                id = get_field(line)
                db[id] = {}
                0
                i += 1
                line = lines[i]
                while '(' in line:
                    slot = get_slot(line)

                    if slot != 'location':
                        value = get_field(line)
                    else:
                        if len(location) == 0:
                            value = get_field(line)
                        else:
                            entloc = get_field(line)
                            entloc = entloc.split(',')
                            entloc[0] = float(entloc[0])
                            entloc[1] = float(entloc[1])
                            bestloc = ''
                            mindist = 100000
                            for locname in location:
                                index = location[locname]
                                dist = get_dist(index, entloc)
                                if dist < mindist:
                                    mindist = dist
                                    bestloc = locname

                            slot = 'area'
                            value = bestloc

                    db[id][slot] = value
                    i += 1
                    line = lines[i]

        f.close()
        return db

    def __fix_SFR_SFH_areas(self,line):
        """
         called for SFR and SFH where database is like: 
         id("00")                                                                                                                   "frederick douglass haynes gardens"("37.779701232910156,-122.42639923095703")
         rather than
         east("x,y")
        """
        if line[0] != '"':
            return line
        else:
            quotes = [i for i, ltr in enumerate(line) if ltr == '"']
            assert(len(quotes) == 4)
            return line[0:quotes[1]+1].replace('"','') + line[quotes[1]+1:]

    def entity_by_features(self, constraints):
        '''Retrieves from database all entities matching the given constraints. 
       
        :param constraints: features. Dict {slot:value, ...} or List [(slot, op, value), ...] (NB. the tuples in the list are actually a :class:`dact` instances)
        :returns: (list) all entities (each a dict)  matching the given features.
 
        .. Note::
            Is just a **wrapper** function handing off to txt (:meth:`entity_by_features_txt`)  or tinydb (:meth:`entity_by_features_tinydb`) based entity retrieval method.
        '''
        if self.ent_by_feat_method == 'tinydb':
            return self.entity_by_features_tinydb(constraints)
        elif self.ent_by_feat_method == 'txt':
            return self.entity_by_features_txt(constraints)

    def entity_by_features_tinydb(self,constraints):
        '''Retrieves all database entities given constraints **via tinydb** 

        :param constraints: features. Dict {slot:value, ...} or List [(slot, op, value), ...]
        :returns: (list) all entities (each a dict)  matching the given features.
        '''
        if type(constraints) == dict:
            constraints_wo_dontcare = {slot:value for slot,value in constraints.items() if value != 'dontcare'}
            # djv27
            #print constraints_wo_dontcare
            #raw_input('by DICT')
            return self._tinydb_constraints_by_dict(constraints_wo_dontcare)

        elif type(constraints) == list:
            constraints_wo_dontcare = [const for const in constraints if const.val != 'dontcare']
            return self._tinydb_constraints_by_list(constraints_wo_dontcare)

        else:
            logger.error('No other constraints type implemented.')

    def entity_by_features_txt(self, constraints):
        '''Retrieves from database all entities matching the given constraints **via string processing**

        :param constraints: features. Dict {slot:value, ...} or List [(slot, op, value), ...]
        :returns: (list) all entities (each a dict)  matching the given features.
        '''
        result = []
        for id in self.db:
            entity = self.db[id]
            match = True
            if type(constraints) == dict:
                for slot in constraints:
                    value = constraints[slot]
                    if value in [None, '**NONE**']:
                        logger.error('Invalid constraint %s=%s' % (slot, value))
                    if value == 'dontcare':
                        continue
                    if slot not in entity:
                        match = False
                        break
                    if entity[slot] != value:
                        match = False
                        break

            elif type(constraints) == list:
                for const in constraints:
                    slot = const.slot
                    op = const.op
                    value = const.val
                    if value == [None, '**NONE**']:
                        logger.error('Invalid constraint %s=%s' % (slot, value))
                    if op == '=' and value == 'dontcare':
                        continue
                    if slot not in entity:
                        match = False
                        break
                    if (op == '=' and entity[slot] != value) or (op == '!=' and entity[slot] == value):
                        match = False
                        break

            else:
                logger.error('Invalid constraint format:' + str(constraints))

            if match:
                result.append(self.db[id])
                '''
        print result
        print type(result)
        raw_input('check result')
        print constraints
        raw_input('^ constraints')
        '''
        return result

    def _tinydb_constraints_by_dict(self, c):
        # c is constraints_without_dontcare 
        numConst = len(c)
        # not possible to implement slot!=value via dict method of constraints
        if numConst == 0:
            return self.db.all()
        slots,vals = c.keys(),c.values()
        # djv27
        print c
        raw_input('^ constraints dict in _tiny .. dict')
        print slots
        print vals
        raw_input('slots,vals')
        if numConst == 1:
            return self.db.search(where(slots[0])==vals[0])
        elif numConst == 2:
            return self.db.search((where(slots[0])==vals[0])&(where(slots[1])==vals[1]))
        elif numConst == 3:
            return self.db.search((where(slots[0])==vals[0])&(where(slots[1])==vals[1])&(where(slots[2])==vals[2]))


    def _tinydb_constraints_by_list(self, c):
        # c is constraints_without_dontcare 
        numConst = len(c)
        # not possible to implement slot!=value via dict method of constraints
        if numConst == 0:
            return self.db.all()
        print c
        raw_input('check constraints')
        s0,o0,v0 = c[0].slot, c[0].op, c[0].val
        if numConst == 1:
            return self.db.search( opts[o0](where(s0),v0))
        s1,o1,v1 = c[1].slot, c[1].op, c[1].val
        if numConst == 2:
            return self.db.search( (opts[o0](where(s0),v0)) & (opts[o1](where(s1),v1)) )
        s2,o2,v2 = c[2].slot, c[2].op, c[2].val
        if numConst == 3:
            return self.db.search( (opts[o0](where(s0),v0)) & (opts[o1](where(s1),v1)) & (opts[o2](where(s2),v2)) )



# END OF FILE
