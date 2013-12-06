from sim_manager import SimulationManager
#from sim_profile import loadSimProfiles
import sim_profile
from multiprocessing import Event
import ConfigParser
import getopt
import sys


conf = None
simulations = []
global_stop_event = None

def loadConfig(path):
    conf = ConfigParser.ConfigParser()
    conf.read(path)
    return conf


def commStat():
    print "com stat called"
    stats = []
    for sim in simulations:
        stats.append( sim.getStats() )
    return stats
commStat.command = "stat"

def commStopAll():
    global_stop_event.set()
    for sim in simulations:
        sim.stopSimulation()
        
commStopAll.command = "stopall"

def shell_forever():
    commands = {}
    for item, obj in globals().iteritems():            
        if hasattr(obj, "command"):
            commands[ obj.command ] = obj
    
    while True:
        comm = raw_input("#")
        if comm.lower() == "help":
            print "Commands: "+", ".join(commands.keys())
        elif comm.lower() == "quit":
            break
        elif comm in commands:
            commands[ comm ]()
        else:
            print "Invalid Command"


def start(argv):
    try:
        opts, args = getopt.getopt(argv,"hc:",["conf="])
    except getopt.GetoptError:
        print 'test.py -c <config file>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'rasd.py -c <config file>'
            sys.exit()
        elif opt in ("-c", "--conf"):
            conf_path = arg
         
    global conf
    conf =loadConfig( conf_path )
    global global_stop_event
    global_stop_event = Event()
    
    for profile in sim_profile.loadSimProfiles(conf):
        s_manager = SimulationManager( profile, global_stop_event )
        s_manager.start()
        simulations.append( s_manager )
    
    shell_forever()
    

if __name__ == "__main__":
    start(sys.argv[1:])