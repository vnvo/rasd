rasd is a RADIUS client simulator for testing a AAA or RADIUS server.
It can create thousands of sessions which would then simulate actual active
users by generating RADIUS requests.

You can have control over simulation by creating a RAS type. Currently, RAS type
for Mikrotik devices is useable.

Configuration:
You would create one or more simulation profiles. available parameters are explained
in the sample rasd.conf

Run:
python ./rasd.py -c rasd.conf


For more information take a look at the rasd.conf .

