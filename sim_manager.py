from threading import Event, Thread
from multiprocessing import Process, current_process
import random
import IPy
import time
from ras_type import MikrotikRas
from session import Session



class SimulationManager(Process):
    def __init__(self, sim_profile, stop_event):
        Process.__init__(self)
        self.__stop_event = stop_event
        self.__sim_profile = sim_profile
        self.__sessions = []
        self.__ras_obj = None
        self.__ready_event = Event()
        self.__sim_stats = {}
        self.__start_sessions = {}
        self.__start_time = None
    
    def run(self):
        #my_pid = current_process().pid
        self.prepSimProfile()
        self.startSimulation()
        
    def prepSimProfile(self):
        """
            Prepare data and create User Sessions (to be simulated). 
            each of them will wait for the start signal.
        """
        # @todo: implement a mechanism to load and use other types of RAS (from ras_type.py)
        self.__ras_obj = MikrotikRas(self.__sim_profile.nas_id,
                                     self.__sim_profile.nas_ip,
                                     self.__sim_profile.radius_secret, 
                                     self.__sim_profile.aaa_server_ip)
        
        # @todo: we better save and keep track of the used IP
        ips = []
        for ip in IPy.IP( self.__sim_profile.user_ips ):
            if str(ip).endswith("0") or "255" in str(ip):
                continue
            ips.append( str(ip) )
        
        for i in xrange( self.__sim_profile.total_sessions ):
            session_type = random.choice( self.__sim_profile.session_types )
            self.__start_sessions[ session_type ] = 1 + self.__start_sessions.get(session_type, 0)
            username, password = self.__genUserPass(i)
            sess = Session(session_type, self.__ready_event,
                     username, password,
                     ips.pop(0), self.__ras_obj)
            
            sess.start()
            self.__sessions.append(sess)
    
    def __genUserPass(self, num):
        num = str(num)
        while 10**(len(num)-1) < self.__sim_profile.total_sessions :
            num = "0"+num
        
        return self.__sim_profile.usernames_prefix+num, self.__sim_profile.passwords_prefix+num
    
    def startSimulation(self):
        self.__start_time = time.time()
        self.__ready_event.set()
        self.__stop_event.wait()
    
    def stopSimulation(self):
        for session in self.__sessions:
            session.do_continue = False
            session.stop_event.set()
    
    def getStats(self):
        return self.__sim_stats
    
    def getSessionStatus(self):
        stat = {}
        for session in  self.__sessions:
            stat[ session.last_state ] = 1 + stat.get(session.last_state, 0)
        
        return stat
