class SimulationProfile:
    # what and how of simulation.
    ras_type      = "Mikrotik"
    nas_id        = "MY-AWESOME-DUMMY-RAS" # Nas-Identifier
    nas_ip        = "192.168.10.10" # Nas-IP-Address
    radius_secret = "secret"
    aaa_server_ip = "127.0.0.1"
    auth_port     = 1812
    acct_port     = 1813
    timeout       = 3
    retries       = 2
    
    # Number of session to be simulated
    total_sessions = 100
    
    # type of session in regard to radius request types
    # types will be chosen randomly.
    # you can influence the total result with putting 
    # multiple items of same type, for example:
    # [AUTH,AUTH,AUTH,STOP] will result in more than 2 to 1 favor
    # for AUTH against STOP
    session_types = []
    
    # simulated users' ip address for Framed-IP-Address
    user_ips = "172.250.0.0/19"
    
    # user/pass of simulated users for authentication 
    usernames_prefix = "test"
    passwords_prefix = "test"
    
    # restart users connection after session stop
    # after sending stop acct, restart by auth
    restart_sessions = True



def loadSimProfiles(conf):
    sim_profiles = []
    for section in conf.sections():
        if section.startswith("sim_profile"):
            s_profile = SimulationProfile()
            s_profile.total_sessions   = conf.getint(section, "total_sessions")
            s_profile.ras_type         = conf.get(section, "ras_type")
            s_profile.nas_id           = conf.get(section, "nas_id", "SIMULATED-RAS")
            s_profile.nas_ip           = conf.get(section, "nas_ip")
            s_profile.radius_secret    = conf.get(section, "radius_secret")
            s_profile.aaa_server_ip    = conf.get(section, "aaa_server_ip")
            s_profile.auth_port        = conf.getint(section, "auth_port")
            s_profile.acct_port        = conf.getint(section, "acct_port")
            s_profile.user_ips         = conf.get(section, "user_ips", None)
            s_profile.usernames_prefix = conf.get(section, "usernames_prefix")
            s_profile.passwords_prefix = conf.get(section, "passwords_prefix")
            s_profile.restart_sessions = conf.getboolean(section, "restart_sessions")
            for sess_type in conf.get(section, "session_types").split(","):
                s_profile.session_types.append(sess_type)
            sim_profiles.append( s_profile )

    return sim_profiles
