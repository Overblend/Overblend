# System imports
import json
import datetime
import os
from shutil import rmtree
import sys
# External imports
from decord import VideoReader, cpu
import soundfile as sf
import av
from uuid import uuid4
import numpy as np
#PYTHON FILES 
from tools import commandline as uf
from render import render as rd
from generate_frames import gen_frame as gf
from preview import preview as pv
#Project File
class VideoEditor: 
    def __init__(self,filename="untitled.json",temp_folder = "temp"):
            self.filename = filename
            self.export_file = "output.mp4"
            if not os.path.exists(temp_folder): 
            #     rmtree(temp_folder)
                os.makedirs(temp_folder)
            self.temp_folder = temp_folder
            self.project = None
            self.elements = None
            self.settings = None
            self.length = None
            self.current_backup = 0
            #Project Settings
            self.name = None
            self.toolkits = None
            self.time_created = None
            self.active_section = None
            self.tracks = None 
            self.track_by_id = None
            self.imported_files = None
            #Retrieving Video Settings
            self.aspect_ratio = None
            self.base_quality = None
            self.preview_fps = None
            self.preview_quality = None
            self.export_fps = None
            self.export_quality = None
            #default_settings 
            self.default_file_length = 5000
            self.min_file_length = 10 
            self.supported_types = ["video", "audio", "image", "gif", "text"]

            #Loading the project
            if os.path.exists(filename) :
                self.load_project()
            else : 
                self.create_project(filename)
    #PROJECT_FILES

    def load_project(self,filename = None):
        try : 
            if not os.path.exists(self.filename):
                raise Exception(f"{self.filename} was not found.")
            if filename is None : 
                with open(self.filename, "r") as f:
                    self.project = json.load(f)
            else : 
                with open(filename,"r") as f:
                    self.project = json.load(f)
                
            for i, item in enumerate(self.project):
                if item.get("type") == "project_information":
                    self.elements = self.project.copy()
                    self.elements.pop(i)
                    break
            self.settings = None
            #Finding the project-information json
            for item in self.project :
                if item.get("type") == "project_information" :
                    self.settings = item

            #Retrieving Project Settings
            self.name = self.settings.get("name", "default")
            self.toolkits = self.settings.get("imported_toolkits",["default.toolkit"])
            self.time_created = self.settings.get("time_created","29-03-25_23:36:25")
            self.length = self.compute_project_duration() if self.compute_project_duration() != 0 else 60
            self.active_section = self.settings.get("section", [0,-1])
            self.tracks = self.settings.get("tracks", [])
            self.track_by_id = {track["id"]: track for track in self.tracks}
            self.imported_files = self.settings.get("imported_files", ["overblend.png"])
            #Retrieving Video Settings
            self.aspect_ratio = self.settings.get("aspect_ratio",[9,16])
            self.base_quality = int(self.settings.get("base_quality", "1080"))
            self.preview_fps = float(self.settings.get("preview_settings")["fps"])
            self.preview_quality = int(self.settings.get("preview_settings")["quality"])
            self.export_fps = float(self.settings.get("export_settings")["fps"])
            self.export_quality = int(self.settings.get("export_settings")["quality"])
            return True
        except : 
            return False
    def update_changes(self):
        try :
            for i, item in enumerate(self.project):
                    if item.get("type") == "project_information":
                        self.elements = self.project.copy()
                        self.elements.pop(i)
                        break
            self.settings = None
            #Finding the project-information json
            for item in self.project :
                if item.get("type") == "project_information" :
                    self.settings = item

            #Retrieving Project Settings
            self.name = self.settings.get("name", "default")
            self.toolkits = self.settings.get("imported_toolkits",["default.toolkit"])
            self.time_created = self.settings.get("time_created","29-03-25_23:36:25")
            self.length = self.compute_project_duration()
            self.active_section = self.settings.get("section", [0,-1])
            self.tracks = self.settings.get("tracks", [])
            self.track_by_id = {track["id"]: track for track in self.tracks}
            self.imported_files = self.settings.get("imported_files", ["overblend.png"])
            #Retrieving Video Settings
            self.aspect_ratio = self.settings.get("aspect_ratio",[9,16])
            self.base_quality = int(self.settings.get("base_quality", "1080"))
            self.preview_fps = float(self.settings.get("preview_settings")["fps"])
            self.preview_quality = int(self.settings.get("preview_settings")["quality"])
            self.export_fps = float(self.settings.get("export_settings")["fps"])
            self.export_quality = int(self.settings.get("export_settings")["quality"])
            return True
        except : 
            return False
    def save(self):
        try:
            i = self.get_project_settings_index()
            if i is not None:
                self.project[i]["aspect_ratio"] = self.aspect_ratio  # 🔁 Met à jour l'aspect ratio

            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.project, f, indent=4)
            return True
        except:
            return False

    #CHECKUPS
    def check_files_existence(self):
        try :
            issues = []
            for file in self.settings.get("imported_files").keys(): 
                if not os.path.exists(file):
                    issues.append(file)
            if len(issues) != 0 : 
                return issues
            else :
                return []
        except : 
            return False
    #retrieve data
    def compute_project_duration(self):
        try :
            max_time = 0.0
            for item in self.elements:
                if not item.get("is_visible", True):
                    continue

                media_type = item.get("type")
                start = item.get("timeline_position", 0) / 1000.0

                duration = 0

                if media_type in ["video", "audio"]:
                    timestamps = item.get("timestamps", [])
                    if timestamps:
                        if timestamps[1] == -2:
                            continue
                        elif timestamps[1] == -1:
                            # Durée jusqu'à la fin → on ouvre la vidéo pour la connaître
                            try:
                                vr = VideoReader(item["file_path"], ctx=cpu(0))
                                fps = vr.get_avg_fps()
                                full_duration = len(vr) / fps
                                duration = full_duration - (timestamps[0] / 1000.0)
                            except Exception as e:
                                print(f"Erreur durée compute: {e}")
                                duration = 0
                        else:
                            duration = (timestamps[1] - timestamps[0]) / 1000.0
                else:
                    timeline_place = item.get("timeline_place", [])
                    if timeline_place and timeline_place[1] != -2:
                        duration = (timeline_place[1] - timeline_place[0]) / 1000.0
                        start = timeline_place[0] / 1000.0

                max_time = max(max_time, start + duration)
            return max_time
        except : 
            return False
    def get_file_duration(self,file):
        VIDEO_EXT = ["mp4"]
        AUDIO_EXT = ["mp3","wav"]
        IMG_EXT = ["png","jpg"]
        FONT_EXT = ["ttf"]
        GIF_EXT = ["gif"]
        LUT_EXT = ["cube"] 
        file_extension = file.split(".")[-1]
        if file_extension in VIDEO_EXT :
            vr = VideoReader(file, ctx=cpu(0))
            fps = vr.get_avg_fps()
            return (len(vr) / fps)*1000
        if file_extension in AUDIO_EXT :
            sample_rate = av.open(file).streams.audio[0].codec_context.sample_rate
            left_audio = []
            if file.lower().endswith(".wav"):
                # 🔹 Lire l'audio avec soundfile
                audio_data, file_sample_rate = sf.read(file, dtype="float32")  

                # Vérifier si la fréquence du fichier correspond à celle attendue
                if file_sample_rate != sample_rate:
                    sample_rate = file_sample_rate  # Mettre à jour la valeur pour éviter le slow-down

                # Si mono, duplique le canal
                if len(audio_data.shape) == 1:
                    left_audio = audio_data
                else:
                    left_audio = audio_data[:, 0]
            else :
                for frame in av.open(file).decode(audio=0):
                    audio_array = frame.to_ndarray()

                    # Séparer directement les canaux en une ligne avec NumPy
                    left_audio.append(audio_array[0])
                # Stack d'un coup au lieu de concaténer en boucle
                left_audio = np.hstack(left_audio)
            return (left_audio.shape[0]/sample_rate)*1000
        if file_extension in IMG_EXT :
            return -1
        if file_extension in GIF_EXT :
            return -1
        if file_extension in FONT_EXT : 
            return -2
        if file_extension in LUT_EXT : 
            return -2
    def get_file_index(self,id):
        for i in range(len(self.project)) :
            if self.project[i].get("id","") == id : 
                return i 
    def get_track_type(self, track_id):
        track = self.track_by_id.get(track_id)
        return track.get("type") if track else None
    def get_project_settings_index(self):
        for i in range(len(self.project)):
            if self.project[i].get("type","") == "project_information" :
                return i
    def get_time_in_clip(self,id,t):
        try : 
            index = self.get_file_index(id)
            if self.project[index].get("timeline_position",-69) != -69 : 
                start = self.project[index]["timeline_position"]
                delta = t-start 
            else : 
                start = self.project[index]["timeline_place"][0]
                delta = t-start
            return delta
        except : 
            return False
    def get_timeline_start(self,id):
        try : 
            index = self.get_file_index(id)
            if self.project[index].get("timeline_position",-69) != -69 : 
                return self.project[index]["timeline_position"]
            else : 
                return self.project[index]["timeline_place"][0]
        except : 
            return False
    def get_instance_length(self,id):
        try :
            
            index = self.get_file_index(id)
            
            if self.project[index].get("timestamps",-69) != -69 :
                return self.project[index]["timestamps"][1] - self.project[index]["timestamps"][0]
            else : 
                return self.project[index]["timeline_place"][1]-self.project[index]["timeline_place"][0]
        except :
            return False
    def get_element_channel(self,id):
        try :
            index = self.get_file_index(id)
            if self.project[index].get("channel",-69) != -69 :
                return self.project[index]["channel"]
        except :
            return False
    def get_file_path(self,id):
        try : 
            index = self.get_file_index(id)
            return self.project[index]["file_path"]
        except : 
            return False
    def is_active(self,id,t):
        try :
            start = self.get_timeline_start(id)
            length = self.get_instance_length(id)
            if t >= start and t <= start+length :
                return True
            return False
        except : 
            return None
    def get_percentage(self,interval,value):
        try :
            return (value - interval[0])/(interval[1]-interval[0])*100
        except : 
            return False
    #FILE OPERATIONS 
    def cut(self,id,t):
        try :
            index = self.get_file_index(id)
            file_path = self.project[index]["file_path"]
            file_type = self.project[index]["type"]
            channel = self.project[index]["channel"]
            if self.is_active(id,t) : #not self.is_active(id,t):
                t_in_clip = self.get_time_in_clip(id,t)
                if self.project[index].get("timeline_position",-69) != -69 : 
                    old_end = self.project[index]["timestamps"][1]
                    self.project[index]["timestamps"][1] = self.project[index]["timestamps"][0] + t_in_clip
                    second_id = self.add_file(file_type,file_path,channel,self.project[index]["timeline_position"] + t_in_clip + 1)
                    self.update_left_timestamp(second_id,self.project[index]["timestamps"][1]+1)
                    self.update_right_timestamp(second_id,old_end)
                else :
                    old_end = self.project[index]["timeline_place"][1]
                    self.project[index]["timeline_place"][1] = self.get_timeline_start(id) + t_in_clip
                    second_id = self.add_file(file_type,file_path,channel,self.project[index]["timeline_place"][1]+1)
                    self.update_right_timestamp(second_id,old_end)
                self.update_changes()
                return second_id
            else : 
                return False
        except : 
            return False
    #MODIFICATIONS
    def add_project_file(self,file_path):
        try :
            for i in range(len(self.project)) :
                if (self.project[i].get("type") == "project_information") and not (file_path in self.project[i]["imported_files"].keys()): 
                     self.project[i]["imported_files"][file_path] = {
                         "max_length" : self.get_file_duration(file_path),
                         "description" : ""
                     }
                     break
            return self.update_changes()
        except Exception as e:
            print(e) 
            return False
    def remove_project_file(self,file_path):
        try :
            for i in range(len(self.project)) :
                if (self.project[i].get("type") == "project_information") and (file_path in self.project[i]["imported_files"].keys()): 
                    del self.project[i]["imported_files"][file_path] 
                    break
            return self.update_changes()
        except Exception as e:
            print(e) 
            return False
    def add_file(self,type,file_path,channel,start) : 
        try :
            temporal_types = ["video","audio"]
            visual_types = ["video","image","gif"]
            audio_types = ["video","audio"]
            id_  = str(uuid4())
            data = {
                "id" : id_,
                "type" : type,
                "file_path" : file_path,
                "channel" : channel,
            }
            if type in temporal_types : 
                data["timeline_position"] = start
                data["timestamps"] = [0,self.get_file_duration(file_path)]
            else : 
                data["timeline_place"] = [start,
                                          start+self.default_file_length]
            if type in visual_types : 
                data["position"] = {
                    "0": ["start",[50,50]],
                    "100": ["linear",[50,50]]
                }
                data["visual_effects"] = {}
            if type in audio_types :
                data["audio_effects"] = {}
            self.project.append(data)
            self.add_project_file(file_path)
            self.update_changes()
            return id_
        except :
            return False
    def remove_file(self,id):
        try :
            self.project.pop(self.get_file_index(id))
            return self.update_changes()
        except :
            return False

    def add_track(self, type, z):
        id_ = str(uuid4())

        # Décaler les pistes existantes si elles ont un z >= z
        for track in self.tracks:
            if track["z"] >= z:
                track["z"] += 1

        data = {
            "id": id_,
            "type": type,
            "z": int(z)
        }

        if type not in ["audio"]:
            data["is_visible"] = True
        if type in ["audio", "video"]:
            data["is_muted"] = False

        for bloc in self.project:
            if bloc.get("type") == "project_information":
                bloc["tracks"].append(data)
        # Re-normaliser tous les z pour qu'ils soient consécutifs
        tracks = sorted([t for t in self.tracks], key=lambda t: t["z"])
        for i, track in enumerate(tracks):
            track["z"] = i

        self.update_changes()
        return id_

    def remove_track(self,id):
        try :
            #Step 1, removing the track in itself
            for i in range(len(self.project)):
                if self.project[i]["type"] == "project_information" :
                    for y in range(len(self.project[i]["tracks"])) :
                        if self.project[i]["tracks"][y].get("id") == id :
                            self.project[i]["tracks"].pop(y)
                            break
                    break
            #Step 2, removing the other shit | Cascade style (ifykyk)
            id_list = []
            for i in range(len(self.project)):
                if self.project[i].get("channel") == id :
                    id_list.append(self.project[i]["id"])
            for id in id_list :
                self.remove_file(id)
            print(id_list)
            return self.update_changes()
        except : 
            return False

    #file related 
    def update_timeline_placement(self,id,new_position):
        try : 
            new_position = max(new_position,0)
            if self.project[self.get_file_index(id)].get("timeline_position",-69) != -69 : 
                self.project[self.get_file_index(id)]["timeline_position"] = new_position
            else : 
                current_section = self.project[self.get_file_index(id)]["timeline_place"] 
                delta = new_position - current_section[0]
                self.project[self.get_file_index(id)]["timeline_place"]  = [new_position, current_section[1] + delta]
            return self.update_changes()
        except : 
            return False
    def update_right_timestamp(self,id,new):
        try : 
            if self.project[self.get_file_index(id)].get("timestamps",-69) != -69 :
                timestamps = self.project[self.get_file_index(id)]["timestamps"]
                new = min(self.settings["imported_files"][self.project[self.get_file_index(id)]["file_path"]]["max_length"],new)
                new = max(new,timestamps[0]+self.min_file_length)
                self.project[self.get_file_index(id)]["timestamps"][1] = new
            else : 
                timestamps = self.project[self.get_file_index(id)]["timeline_place"]
                self.project[self.get_file_index(id)]["timeline_place"][1] = max(new,timestamps[0]+self.min_file_length)
            return self.update_changes()
        except : 
            return False
    def update_left_timestamp(self,id,new):
        try :
            if self.project[self.get_file_index(id)].get("timestamps",-69) != -69 :
                timestamps = self.project[self.get_file_index(id)]["timestamps"]
                new = max(0,new)
                new = min(new,timestamps[1]-self.min_file_length)
                self.project[self.get_file_index(id)]["timestamps"][0] = new
            else : 
                timestamps = self.project[self.get_file_index(id)]["timeline_place"]
                new = max(0,new)
                new = min(new,timestamps[1]-self.min_file_length)
                self.project[self.get_file_index(id)]["timeline_place"][0] = new
            return self.update_changes()
        except : 
            return False
    #visual related (visual_related)
    def add_visual_effect(self,id,effect,*args):
        try :
            keys = list(self.project[self.get_file_index(id)]["visual_effects"].keys())
            keys = [int(x) for x in keys]
            entry =  max(keys)+1 if len(keys) != 0 else 0
            self.project[self.get_file_index(id)]["visual_effects"][entry] = {}
            self.project[self.get_file_index(id)]["visual_effects"][entry][effect] = {}
            for timestamp in args[0].keys() :
                self.project[self.get_file_index(id)]["visual_effects"][entry][effect][timestamp] = args[0][timestamp]
            return self.update_changes()
        except Exception as e : 
            return False
    def update_effect_placement(self, id, old_timestamps):
        try:
            index = self.get_file_index(id)
            obj = self.project[index]

            # Nouvelle plage de timestamps (en ms)
            if obj.get("timestamps", -69) != -69:
                new_timestamps = obj["timestamps"]
            else:
                new_timestamps = obj["timeline_place"]

            # Convertir les nouvelles bornes en pourcentages de l'ancien clip
            section = [self.get_percentage(old_timestamps, ts) for ts in new_timestamps]

            # 🔁 Position
            if "position" in obj:
                updated_position = {}
                for k, v in obj["position"].items():
                    try:
                        k = int(k)
                        new_k = int(self.get_percentage(section, k))
                        updated_position[str(new_k)] = v
                    except:
                        continue
                obj["position"] = updated_position

            # 🔁 Visual Effects
            if "visual_effects" in obj:
                for effect_idx in obj["visual_effects"]:
                    effect_data = obj["visual_effects"][effect_idx]
                    for effect_name in effect_data:
                        updated_effect = {}
                        for k, v in effect_data[effect_name].items():
                            k = int(k)
                            new_k = int(self.get_percentage(section, k))
                            updated_effect[str(new_k)] = v
                        obj["visual_effects"][effect_idx][effect_name] = updated_effect

            # 🔁 Audio Effects
            if "audio_effects" in obj:
                for effect_idx in obj["audio_effects"]:
                    effect_data = obj["audio_effects"][effect_idx]
                    for effect_name in effect_data:
                        updated_effect = {}
                        for k, v in effect_data[effect_name].items():
                            k = int(k)
                            new_k = int(self.get_percentage(section, k))
                            updated_effect[str(new_k)] = v
                        obj["audio_effects"][effect_idx][effect_name] = updated_effect

            return self.update_changes()

        except Exception as e:
            print(f"[ERROR] update_effect_placement failed: {e}")
            return False

    def remove_visual_effect(self,id,number):
        try : 
            del self.project[self.get_file_index(id)]["visual_effects"][str(number)]
            l = len(list(self.project[self.get_file_index(id)]["visual_effects"].keys()))
            for item in range(l+1): 
                if int(item) > int(number) : 
                    temp = self.project[self.get_file_index(id)]["visual_effects"][str(item)]
                    del self.project[self.get_file_index(id)]["visual_effects"][str(item)]
                    self.project[self.get_file_index(id)]["visual_effects"][str(int(item)-1)] = temp
            return self.update_changes()
        except :
            return False
    def visual_swap_order(self,id,pos1,pos2):
        try :
            copy  = self.project[self.get_file_index(id)]["visual_effects"][str(pos1)]
            length = len(list(self.project[self.get_file_index(id)]["visual_effects"].keys()))
            self.remove_visual_effect(id,pos1)
            temp = {}
            for x in range(length) :
                if x < pos2:
                    temp[str(x)]  = self.project[self.get_file_index(id)]["visual_effects"][str(x)] 
                if x == pos2 : 
                    temp[str(x)]  = copy
                else : 
                    temp[str(x)]  = self.project[self.get_file_index(id)]["visual_effects"][str(x-1)]
            self.project[self.get_file_index(id)]["visual_effects"] = temp
            return self.update_changes()
        except : 
            return False
    def remove_all_visual_effects(self,id):
        try : 
            l = len(list(self.project[self.get_file_index(id)]["visual_effects"].keys()))
            if l != 0 :
                for item in range(l):
                    del self.project[self.get_file_index(id)]["visual_effects"][str(item)]
            return self.update_changes()
        except : 
            return False

    #audio related (audio_related)
    def update_audio_effect(self,id,number,effect,*args):
        try :
            self.project[self.get_file_index(id)]["audio_effects"][str(number)][effect] = {}
            for timestamp in args[0].keys() :
                self.project[self.get_file_index(id)]["audio_effects"][str(number)][effect][timestamp] = args[0][timestamp]
            return self.update_changes()
        except :
            return False
    def remove_audio_effect(self,id,number):
        try : 
            del self.project[self.get_file_index(id)]["audio_effects"][str(number)]
            l = len(list(self.project[self.get_file_index(id)]["audio_effects"].keys()))
            for item in range(l+1): 
                if int(item) > int(number) : 
                    temp = self.project[self.get_file_index(id)]["audio_effects"][str(item)]
                    del self.project[self.get_file_index(id)]["audio_effects"][str(item)]
                    self.project[self.get_file_index(id)]["audio_effects"][str(int(item)-1)] = temp
            return self.update_changes()
        except :
            return False
    def audio_swap_order(self,id,pos1,pos2):
        try :
            copy  = self.project[self.get_file_index(id)]["audio_effects"][str(pos1)]
            length = len(list(self.project[self.get_file_index(id)]["audio_effects"].keys()))
            self.remove_visual_effect(id,pos1)
            temp = {}
            for x in range(length) :
                if x < pos2:
                    temp[str(x)]  = self.project[self.get_file_index(id)]["audio_effects"][str(x)] 
                if x == pos2 : 
                    temp[str(x)]  = copy
                else : 
                    temp[str(x)]  = self.project[self.get_file_index(id)]["audio_effects"][str(x-1)]
            self.project[self.get_file_index(id)]["audio_effects"] = temp
            return self.update_changes()
        except : 
            return False
    def remove_all_audio_effects(self,id):
        try : 
            l = len(list(self.project[self.get_file_index(id)]["audio_effects"].keys()))
            if l != 0 :
                for item in range(l):
                    del self.project[self.get_file_index(id)]["audio_effects"][str(item)]
            return self.update_changes()
        except : 
            return False
    def get_z_level(self,item):
        ch = item.get("channel")
        track = self.track_by_id.get(ch)
        return track.get("z", 0) if track else 0

