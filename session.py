from threading import Thread
from threading import Event
from pyrad import client
from pyrad import packet
from ras_type import MikrotikRas
import time
import random
import IPy


STATE_READY = "READY"
STATE_AUTH = "AUTH"
STATE_START_ACCT = "START-ACCT"
STATE_UPDATE_ACCT = "UPDATE-ACCT"
STATE_STOP_ACCT = "STOP-ACCT"

def getAllStateValues():
    states = []
    for k,v in globals().iteritems():
        if k.startswith("STATE_"):
            states.append(v)
    return states

class Session(Thread):
    """
        This represent a user/session to be simulated
    """
    def __init__(self,test_target, ready_event, username, password, ip, ras):
        Thread.__init__(self)
        self.test_target = test_target
        self.test_sequence = None
        self.ras = ras
        self.username = username
        self.password = password
        self.mac = self.ras.genMACAddress()
        self.ip = ip
        self.nas_port = 0
        self.nas_port_id = 0
        self.session_id = ""
        
        self.input_octet = 0       
        self.output_octet = 0       
        self.input_pkts = 0   
        self.output_pkts = 0   
        self.input_gigawords = 0
        self.output_gigawords = 0
        
        self.do_continue = True

        self.stop_event = Event()
        self.ready_event = ready_event
        self.start_time = 0
        self.last_state = STATE_READY
        self.update_interval_count = 0

        # restart simulation from Auth when test is finished or failed
        self.restart_sequence = True
        self.all_seq = [self.authenticate, self.start_accounting, self.update_accounting, self.stop_accounting]
        self.all_seq_name = [ STATE_AUTH, STATE_START_ACCT, STATE_UPDATE_ACCT, STATE_STOP_ACCT ]
        self.createTestSequence()

        self.stat = {"total_pkts":0, "timeouts":0,
                     "auth_req":0, "auth_retry":0, "auth_delay_time":0,
                     "acct_req":0, "update_acct_retry":0, "start_acct_delay_time":0,
                     "stop_acct_retry":0, "stop_acct_delay_time":0,
                     }

    def _updateStats(self, req, duration, attempts, timeouts):
        pkt_count = max(attempts, 1)
        self.stat["total_pkts"] += pkt_count
        self.stat["timeouts"] += timeouts
        if isinstance(req, packet.AcctPacket):
            self.stat["auth_req"] += 1
            self.stat["auth_retry"] += pkt_count
        else:
            self.stat["acct_req"] += 1
            if req["Acct-Status-Type"] == "Alive":
                self.stat["update_acct_retry"] += attempts
                self.stat[""]

    def createTestSequence(self):
        self.test_sequence = self.all_seq[ self.all_seq_name.index(self.test_target) : ]

    def log(self, msg):
        return
        print "=> %s(%s): %s\n"%(self.username, self.last_state, msg)

    def run(self):
        self.simulate()

    def simulate(self):
        self.ras.setUserSessionInfo( self )
        self.ready_event.wait()
        while self.do_continue:
            for action in self.test_sequence:
                continue_seq = action()
                if not continue_seq:
                    break

            if not self.restart_sequence:
                break
            else:
                self.test_sequence = self.all_seq
        
    def sendReq(self, req):
        start = time.time()
        try:
            resp, attempts, timeouts = self.ras.srv.SendPacket( req )
        except client.Timeout:
            return None
        
        duration = time.time()-start
        self._updateStats(req, duration, attempts, timeouts)

        return resp
    
    def authenticate(self):
        self.ras.setUserSessionInfo( self )
        self.last_state = STATE_AUTH
        accepted = False
        while not accepted:
            if not self.do_continue: 
                break
            req = self.ras.createAccessRequest( self )
            resp = self.sendReq( req )
            if isinstance(resp, packet.AuthPacket) and resp.code==packet.AccessAccept:
                accepted = True
                self.start_time = time.time()
                return True

    def start_accounting(self):
        self.last_state = STATE_START_ACCT
        req = self.ras.createStartAcctRequest( self )
        resp = self.sendReq( req )

        if isinstance(resp, packet.AcctPacket):
            return True

        return False

    def update_accounting(self):
        self.last_state = STATE_UPDATE_ACCT
        self.stop_event.wait(self.ras.update_interval)

        while self.do_continue:
            req = self.ras.createUpdateAcctRequest( self )
            resp = self.sendReq( req )
            #if isinstance(resp, packet.AcctPakcet):
            #    return True
            #else:   
            self.stop_event.wait(self.ras.update_interval)

    def stop_accounting(self):
        self.last_state = STATE_STOP_ACCT
        term_cause = random.choice(["User-Request","User-Request","User-Request","Port-Error","Admin-Reset"])
        req = self.ras.createStopAcctRequest( self, term_cause )
        resp = self.sendReq( req )
        if isinstance(resp, packet.AcctPacket):
            return True
        else:
            return True

    def __repr__(self):
        sess_time = ""
        if self.start_time:
            sess_time = time.time() - self.start_time
        return "%s:  %s  (%s)"%(self.username, self.last_state, sess_time)



if __name__ == "__main__":
    test_targets = [STATE_AUTH]*3#, "UPDATE-ACCT", "STOP-ACCT"]
    ras_obj = MikrotikRas("Test-Ras", "192.168.1.237", "test", "127.0.0.1", 2)
    ips = []
    for ip in IPy.IP("172.250.0.0/19"):
        if str(ip).endswith("0") or "255" in str(ip):
            continue
        ips.append( str(ip) )

    ready_event = Event()
    users = []
    start_stat = {}
    for i in xrange(50):
        test_target = random.choice(test_targets)
        start_stat[ test_target ] = 1 + start_stat.get(test_target, 0)
        u = Session(test_target, ready_event, "vtest-%s"%i, "vtest-%s"%i, "00:00:00:11:45:46", ips.pop(0), ras_obj)
        u.start()
        users.append(u)

    print "MAN: All Clients Ready ...\n"
    for item, count in start_stat.iteritems():
        print "%s:\t%s"%(item, count)

    ready_event.set()
    print "MAN: All Clients Started ...\n"

    while True:
        i = raw_input("Comm# ")
        if i == "stop":
            for user in users:
                user.do_continue = False
                user.stop_event.set()

        elif i == "stat":
            stat = {}
            for user in users:
                stat[ user.last_state ] = 1 + stat.get(user.last_state, 0)
            for item in getAllStateValues():
                print "%s:\t%s"%(item, stat.get(item, 0))

        elif i == "quit":
            break

