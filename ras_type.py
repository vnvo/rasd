from pyrad import client
from pyrad import dictionary
from pyrad import packet
import os
import random


class Ras:
    GIGAWORDS = 4294967295
    
    def __init__(self, nas_id, nas_ip, secret, aaa_ip, timeout=3, retry=2, update_interval=60):
        self.nas_id = nas_id
        self.nas_ip = nas_ip
        self.radius_secret = secret
        self.timeout = timeout
        self.retry = retry
        self.update_interval = update_interval
        self.aaa_ip = aaa_ip
        self.auth_port = 1812
        self.acct_port = 1813

        self.createServer()

        self.ras_stats = dict(total_pkts=0, 
                              auth_pkts=0,
                              start_acct_pkts=0, 
                              update_acct_pkts=0,
                              stop_acct_pkts=0, 
                              auth_timedout=0,
                              update_acct_timedout=0, 
                              start_acct_pkts_timedout=0)

    def createServer(self):
        self.srv=client.Client(
                  server=self.aaa_ip,
                  secret=self.radius_secret,
                  authport=self.auth_port,
                  acctport=self.acct_port,
                  dict=self.createDict())
        self.srv.timeout = self.timeout
        self.srv.retries = self.retry

    def createDict(self):
        DICTIONARIES_ROOT = os.getcwd() + "/dictionaries/"
        return dictionary.Dictionary("%s/dictionary"%DICTIONARIES_ROOT)

    def setUserConnInfo(self, user, req):
        """
            update user(connection) specific info in request
        """
        raise NotImplementedError()
    
    def setUserSessionInfo(self, user):
        """
            set session specific info in user instance
        """
        raise NotImplementedError()
    
    def genMACAddress(self):
        """
            Generate a random MAC Address
        """
        mac = [ 0x00, 0x16, 0x1e,
            random.randint(0x00, 0x7f),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff) ]
        
        return ':'.join(map(lambda x: "%02x" % x, mac))        

    def genSessionID(self):
        """
            Generate New Acct-Session-Id value
        """
        return str(random.random())
    
    def genPortID(self):
        """
            Generate New Nas-Port
        """
        return str(random.random())[2:10]
    
    def updateSessionUsage(self, user, req):
        """
            Simulate User Traffic Usage
        """
        out_octet = random.randrange(100, 8388608) # user recv
        in_octet = out_octet/5  # user send
        user.input_octet  += in_octet
        user.output_octet += out_octet
        user.input_pkts   += 100
        user.output_pkts  += 100
        
        if user.input_octet > self.GIGAWORDS :
            user.input_octet = user.input_octet - self.GIGAWORDS
            user.input_gigawords += 1
        if user.output_octet > self.GIGAWORDS:
            user.output_octet = user.output_octet - self.GIGAWORDS
            user.output_gigawords += 1
        
        req["Acct-Input-Octets"]     = user.input_octet
        req["Acct-Output-Octets"]    = user.output_octet
        req["Acct-Input-Packets"]    = user.input_pkts
        req["Acct-Output-Packets"]   = user.output_pkts    
        req["Acct-Input-Gigawords"]  = user.input_gigawords
        req["Acct-Output-Gigawords"] = user.output_gigawords
    
    def setNasInfo(self, req):
        req["NAS-IP-Address"] = self.nas_ip
        req["NAS-Identifier"] = self.nas_id
    
    ################## Requests
    def createAccessRequest(self, user):
        """
            Currently only PAP method is supported.
        """
        req=self.srv.CreateAuthPacket(
                       code=packet.AccessRequest,
                       User_Name=user.username)

        req["User-Password"]=req.PwCrypt(user.password)
        self.setNasInfo(req)
        self.setUserConnInfo( user, req )
        return req
    
    def createStartAcctRequest(self, user):
        req=self.srv.CreateAcctPacket(User_Name=user.username)        
        req["Acct-Status-Type"] = "Start"
        self.setNasInfo(req)
        self.setUserConnInfo( user, req )
        return req

    def createUpdateAcctRequest(self, user):
        req=self.srv.CreateAcctPacket(User_Name=user.username)
        self.updateSessionUsage(user, req)
        req["Acct-Status-Type"] = "Alive"
        self.setNasInfo(req)
        self.setUserConnInfo( user, req )
        return req
    
    def createStopAcctRequest(self, user, term_cause):
        req=self.srv.CreateAcctPacket(User_Name=user.username)
        self.updateSessionUsage(user, req)
        req["Acct-Status-Type"] = "Stop"
        req["Acct-Terminate-Cause"] = term_cause
        self.setNasInfo(req)
        self.setUserConnInfo( user, req )
        return req
    

########################  Ras Types

class MikrotikRas(Ras):
    def setUserConnInfo(self, user, req):
        """
            PPP Connection
        """

        if user.ip:
            req["Framed-IP-Address"] = user.ip
        if user.mac:
            req["Calling-Station-Id"] = user.mac
        if user.session_id:
            req["Acct-Session-Id"] = user.session_id

        req["NAS-Identifier"]   = self.nas_id
        req["Service-Type"]     = "Framed-User"
        req["NAS-Port-Type"]    = "Ethernet"
        req["NAS-Port"]         = user.nas_port
        req["NAS-Port-Id"]      = user.nas_port_id
        req["Framed-Protocol"]  = "PPP"

    def setUserSessionInfo(self, user):
        user.nas_port_id = self.genPortID()
        user.nas_port = long(user.nas_port_id)
        user.session_id = self.genSessionID()

#######