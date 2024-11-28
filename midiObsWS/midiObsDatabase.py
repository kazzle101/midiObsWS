
import sys
import asyncio
import sqlite3
import os
import json

class ObsDatabase:

    def __init__(self, scriptDir):
        self.scriptDir = scriptDir
        self.dbfile = os.path.join(scriptDir, "midiOBSws.db")
            
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
            
    def getConfig(self):
        
        con = sqlite3.connect(self.dbfile, timeout=10)
        con.row_factory = self.dict_factory
        cur = con.cursor()

        sql = """SELECT wsHostSet, wsAddress, wsPort, wsPassword, midiSet, midiIn, midiOut, 
                 midiChannel, configured FROM wsConfig WHERE id=1"""  
        cur.execute(sql)
        result = cur.fetchone()
        
        cur.close()
        con.close()        
        return result   
    
    def setConfig(self, config):
        con = sqlite3.connect(self.dbfile, timeout=10)
        cur = con.cursor()
        
        sql = "UPDATE wsConfig SET "
        values = []
        for key, value in config.items():
            values.append(f"{key} = ?")
        sql += ", ".join(values) + " WHERE id=1"
        
        cur.execute(sql, tuple(config.values()))
        con.commit() 
             
        cur.close()
        con.close()
        return
        
    def setAllConfigured(self, val):
        con = sqlite3.connect(self.dbfile, timeout=10)
        cur = con.cursor()
        
        cur.execute(f"UPDATE wsConfig SET configured=? WHERE id=1",(val,))
        con.commit() 
             
        cur.close()
        con.close()
        return
        
    def getInputsList(self, showOnSetup=True, activeOnly=False):
        
        con = sqlite3.connect(self.dbfile, timeout=10)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        
        sql = "SELECT id, inputKind, inputType, name, buttonID, changeID, buttonValue, changeValue, uuid FROM userInputs"
        if showOnSetup:
            sql += " WHERE showOnSetup = 1"
                    
        if activeOnly and showOnSetup:
            sql += " AND (buttonID >= 0 OR changeID >= 0)"
        elif activeOnly:
            sql += " WHERE (buttonID >= 0 OR changeID >= 0)"
                    
        cur.execute(sql)
        results = cur.fetchall() 
        
        cur.close()
        con.close()
        return results
    
    def getScenesList(self, activeOnly=False):
        
        con = sqlite3.connect(self.dbfile, timeout=10)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        
        if activeOnly:
            sql = "SELECT id, sceneIndex, name, buttonID, buttonValue, uuid FROM userScenes WHERE buttonID >= 0"
        else:
            sql = "SELECT id, sceneIndex, name, buttonID, buttonValue, uuid FROM userScenes"
            
        cur.execute(sql)
        results = cur.fetchall() 
    
        cur.close()
        con.close()
        return results  
        
    def getControlsList(self, activeOnly=False):
        
        con = sqlite3.connect(self.dbfile, timeout=10)
        con.row_factory = self.dict_factory
        cur = con.cursor()
        
        if activeOnly:
            sql = """SELECT id, io, ioKind, name, display, buttonID, buttonValue FROM wsControls
                    WHERE showOnSetup=1 AND ioKind='button' AND buttonID >= 0"""
        else:
            sql = """SELECT id, io, ioKind, name, display, buttonID, buttonValue FROM wsControls
                    WHERE showOnSetup=1 AND ioKind='button'"""
        cur.execute(sql)
        results = cur.fetchall() 
    
        cur.close()
        con.close()
        return results  
        
    def updateTablesWithMidiValues(self, allNames):
        
        con = sqlite3.connect(self.dbfile, timeout=10)
        cur = con.cursor()
        
        for n in allNames:
            if n["changed"] == False:
                continue
            
            try:
                section, id, type = n["name"].split("_", 2)
            except Exception as e:
                print(f"invalid name: {n['name']}")
                print(f"an error occurred: {e}")
                continue
            
            if section == "controls":
                cur.execute("UPDATE wsControls SET buttonID=? WHERE id=?",(n["midiID"], int(id)))
            elif section == "scenes":
                cur.execute("UPDATE userScenes SET buttonID=? WHERE id=?",(n["midiID"], int(id)))
            elif section == "sources":
                if type == "b":
                    cur.execute("UPDATE userInputs SET buttonID=? WHERE id=?",(n["midiID"], int(id)))
                elif type == "r":
                    cur.execute("UPDATE userInputs SET changeID=? WHERE id=?",(n["midiID"], int(id)))
        
        con.commit() 
        
        cur.close()
        con.close()
        return
        
    
    def getInputType(self, cur, inputKind):
        
        cur.execute("SELECT ioKind, showOnSetup FROM wsControls WHERE name=?;",(inputKind,))
        result = cur.fetchone()
 
        if not result:
            return False, f"Unknown inputKind: {inputKind}, I do not know if this input is Audio or Video"
 
        return result[0], result[1]
        
    def setInputsList(self, inputs):
        
        con = sqlite3.connect(self.dbfile, timeout=10)
        cur = con.cursor()
        
        data = []
        uuids = []
        
        # print("setInputs")
        # print(inputs)
        
        for i in inputs:          
            ioKind, showOnSetup = self.getInputType(cur, i["inputKind"]) 
            if not ioKind:
                print(showOnSetup)
                print(json.dumps(i, indent=4, sort_keys=False))
                continue
                                                   
            d={
                "inputKind": i["inputKind"],
                "inputType": ioKind,
                "showOnSetup": showOnSetup,
                "name": i["inputName"],
                "uuid": i["inputUuid"]
            }
            # print(json.dumps(d, indent=4, sort_keys=False))
            data.append(d)
            uuids.append(d["uuid"])
            
            cur.execute(f"SELECT id FROM userInputs WHERE uuid=?",(d['uuid'],))
            result = cur.fetchone()
            if result:
                cur.execute("UPDATE userInputs SET inputKind=?, showOnSetup=?, inputType=?, name=? WHERE id=?;",
                            (d["inputKind"], d["showOnSetup"], d["inputType"], d["name"], result[0]))
            else:
                cur.execute("INSERT INTO userInputs (inputKind, showOnSetup, inputType, name, uuid) VALUES (?, ?, ?, ?, ?)",
                            (d["inputKind"], d["showOnSetup"], d["inputType"], d["name"], d["uuid"]))
            
        con.commit() 
            
        self.tidyInputs(con, cur, uuids)
            
        cur.close()
        con.close()
        return data
        
    def tidyInputs(self, con, cur, currentUuids):
        inputsList = self.getInputsList(False)
        uuids = []
        for cl in inputsList:
            uuids.append(cl["uuid"])   
         
        for u in uuids:
            if u not in currentUuids:
                cur.execute("DELETE FROM userInputs WHERE uuid=?",(u,))
                con.commit() 
                
        return
        
    def setScenesList(self, scenes):
        
        con = sqlite3.connect(self.dbfile, timeout=10)
        cur = con.cursor()
        
        data = []
        uuids = []
        
        for s in scenes:
            d = {
                "sceneIndex": s["sceneIndex"],
                "name": s["sceneName"],
                "uuid": s["sceneUuid"]
            }
            data.append(d)
            uuids.append(d["uuid"])
            
            cur.execute(f"SELECT id FROM userScenes WHERE uuid=?",(d['uuid'],))
            result = cur.fetchone()
            if result:
                cur.execute("UPDATE userScenes SET sceneIndex=?, name=? WHERE id=?",
                            (d["sceneIndex"], d["name"], result[0]))
            else:
                cur.execute("INSERT INTO userScenes (sceneIndex, name, uuid) VALUES (?, ?, ?)",
                            (d["sceneIndex"], d["name"], d["uuid"]))
        
        con.commit() 
        
        self.tidyScenes(con, cur, uuids)
        
        cur.close()
        con.close()
        return data
        
    def tidyScenes(self, con, cur, currentUuids):
        scenesList = self.getScenesList()
        uuids = []
        for cl in scenesList:
            uuids.append(cl["uuid"])   
         
        for u in uuids:
            if u not in currentUuids:
                cur.execute("DELETE FROM userScenes WHERE uuid=?",(u,))
                con.commit() 
                
        return
        
    def createDefaultDatabase(self):
        
        try:
            con = sqlite3.connect(self.dbfile, timeout=10)
            cur = con.cursor()
        except Exception as e:    #sqlite3.Error as e:
            return True, f"sqlite error: {e}, exiting"
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wsConfig'")
        result = cur.fetchone()
        if result is not None:
            cur.close()
            con.close()
            return False, f"sqlite database ready: {self.dbfile}"
        
        sql = """CREATE TABLE wsConfig(
                    id INTEGER PRIMARY KEY ASC,
                    wsHostSet INTEGER, 
                    wsAddress TEXT, 
                    wsPort INTEGER, 
                    wsPassword TEXT, 
                    midiSet INTEGER, 
                    midiIn TEXT, 
                    midiOut TEXT, 
                    midiChannel INTEGER,
                    configured INTEGER);"""
        cur.execute(sql)
        con.commit() 
        
        sql = """INSERT INTO wsConfig
                    (wsHostSet, wsAddress, wsPort, wsPassword, midiSet, midiIn, midiOut, midiChannel, configured)
                    VALUES (0, 'localhost', 4455, '', 0, '', '', 10, 0);"""
        cur.execute(sql)
        con.commit() 
        
        sql = """CREATE TABLE wsControls (
                id INTEGER PRIMARY KEY ASC,
                io TEXT, 
                showOnSetup INTEGER,
                ioKind TEXT, 
                name TEXT, 
                display TEXT,
                buttonID INTEGER DEFAULT -1, 
                buttonValue INTEGER DEFAULT 0);"""
        
        cur.execute(sql)        
        wsControlData = [
            ("input", 1, "button", "StartRecord", "Start Recording"),
            ("input", 1, "button", "StopRecord", "Stop Recording"),
            ("input", 1, "button", "PauseRecord", "Pause Recording"),
            ("input", 1, "button", "ToggleRecord", "Toggle Recording"),
            ("input", 1, "button", "ToggleRecordPause", "Toggle Pause Recording"),
            ("input", 1, "button", "ResumeRecord","Resume Recording"),
            ("input", 1, "button", "StartVirtualCam","Start Virtual Camera"),
            ("input", 1, "button", "StopVirtualCam","Stop Virtual Camera"),
            ("input", 1, "button", "ToggleVirtualCam", "Toggle Virtual Camera"),
            ("input", 1, "button", "StartStream","Start Streaming"),
            ("input", 1, "button", "StopStream","Stop Streaming"),
            ("input", 1, "button", "ToggleStream", "Toggle Streaming"),
            ("input", 1, "button", "SetStudioModeEnabled", "Toggle Studio Mode"),
            ("input", 1, "audio", "wasapi_input_capture", "wasapi input capture"),
            ("input", 1, "audio", "wasapi_output_capture", "wasapi output capture"),
            ("input", 1, "audio", "coreaudio_input_capture", "coreaudio input capture"),
            ("input", 1, "audio", "coreaudio_output_capture", "coreaudio output capture"),
            ("input", 1, "audio", "pulse_input_capture", "pulse input capture"),
            ("input", 1, "audio", "pulse_output_capture", "pulse output capture"),
            ("input", 0, "video", "dshow_input", "dshow input"),
            ("input", 1, "video", "ffmpeg_source", "ffmpeg source"),
            ("input", 0, "video", "monitor_capture", "monitor capture"),
            ("input", 0, "video", "window_capture", "window capture"),
            ("input", 0, "video", "av_capture_input", "av capture input"),
            ("input", 0, "video", "v4l2_input", "v4l2 input"),
            ("input", 0, "video", "pipewire-screen-capture-source", "Screen Capture (PipeWire)"),
            ("output", 0, "audio", "ffmpeg_muxer", "simple_file_output"),
            ("output", 0, "video", "virtualcam_output", "virtualcam_output")                    
        ]
        
        cur.executemany("INSERT INTO wsControls (io, showOnSetup, ioKind, name, display) VALUES(?, ?, ?, ?, ?)", wsControlData)
        con.commit() 
        
        sql = """CREATE TABLE userInputs(
                    id INTEGER PRIMARY KEY ASC,
                    inputKind TEXT, 
                    showOnSetup INTEGER,
                    inputType TEXT, 
                    name TEXT, 
                    buttonID INTEGER DEFAULT -1, 
                    changeID INTEGER DEFAULT -1, 
                    buttonValue INTEGER DEFAULT 0, 
                    changeValue INTEGER DEFAULT 0, 
                    uuid TEXT);"""
        
        cur.execute(sql)
        con.commit() 
        
        sql = """CREATE TABLE userScenes (
                    id INTEGER PRIMARY KEY ASC,
                    sceneIndex INTEGER,
                    name TEXT,
                    buttonID INTEGER DEFAULT -1, 
                    buttonValue INTEGER DEFAULT 0,
                    uuid TEXT);"""
                    
        cur.execute(sql)
        con.commit() 
        
        cur.close()
        con.close()
        return False, f"sqlite database created: {self.dbfile}"