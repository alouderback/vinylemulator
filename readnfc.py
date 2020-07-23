import time
import nfc
import appsettings  # you shouldnt need to edit this file
import usersettings  # this is the file you might need to edit
import sys
import os
import argparse
import logging
import time
import sys
import pychromecast
from pychromecast.controllers.spotify import SpotifyController
import spotify_token as st
import spotipy

# this function gets called when a NFC tag is detected
def touched(tag):
    global chromecast_local

    if tag.ndef:
        for record in tag.ndef.records:
            receivedtext = record.text
            receivedtext_lower = receivedtext.lower()

            print("")
            print("Read from NFC tag: " + receivedtext)

            servicetype = ""
            castinstruction = ""

            if receivedtext_lower.startswith('spotify'):
                servicetype = "spotify"
                castinstruction = "python spotify_example.py --user " + usersettings.username + " --password " + usersettings.password + " --cast " + usersettings.chromecast + " --uri " + receivedtext

            if receivedtext_lower.startswith('command'):
                servicetype = "command"
                sonosinstruction = receivedtext[8:]

            if receivedtext_lower.startswith('room'):
                servicetype = "room"
                sonosroom_local = receivedtext[5:]
                print("Sonos room changed to " + sonosroom_local)
                return True

            if servicetype == "":
                print("Service type not recognised. Tag text should begin spotify, command, or room.")
                return True

            print("Detected " + servicetype + " service request")

            launch_spotify(usersettings.chromecast, usersettings.username, usersettings.password, receivedtext)


    else:
        print("")
        print(
            "NFC reader could not read tag. This can be because the reader didn't get a clear read of the card. If "
            "the issue persists then this is usually because (a) the tag is encoded (b) you are trying to use a "
            "mifare classic card, which is not supported or (c) you have tried to add data to the card which is not "
            "in text format. Please check the data on the card using NFC Tools on Windows or Mac.")
    return True


def launch_spotify(target, user, password, uri):

    chromecasts = pychromecast.get_listed_chromecasts(friendly_names=target)
    cast = None
    for _cast in chromecasts:
        if _cast.name == target:
            cast = _cast
            break

    if not cast:
        print('No chromecast with name "{}" discovered'.format(target))
        print("Discovered casts: {}".format(chromecasts))
        sys.exit(1)

    print("cast {}".format(cast))

    class ConnListener:
        def __init__(self, mz):
            self._mz = mz

        def new_connection_status(self, connection_status):
            """Handle reception of a new ConnectionStatus."""
            if connection_status.status == "CONNECTED":
                self._mz.update_members()

    class MzListener:
        def __init__(self):
            self.got_members = False

        def multizone_member_added(self, uuid):
            pass

        def multizone_member_removed(self, uuid):
            pass

        def multizone_status_received(self):
            self.got_members = True

    # Wait for connection to the chromecast
    cast.wait()

    spotify_device_id = None

    # Create a spotify token
    data = st.start_session(user, password)
    access_token = data[0]
    expires = data[1] - int(time.time())

    #Create spotify client
    client = spotipy.Spotify(auth=access_token)

    # Launch the spotify app on cast device
    sp = SpotifyController(access_token, expires)
    cast.register_handler(sp)
    sp.launch_app()

    if not sp.is_launched and not sp.credential_error:
        print("Failed to launch spotify controller due to timeout")
        sys.exit(1)
    if not sp.is_launched and sp.credential_error:
        print("Failed to launch spotify controller due to credential error")
        sys.exit(1)

    # Query spotify for active devices
    devices_available = client.devices()

    # Match active spotify devices with the spotify controller's device id
    for device in devices_available["devices"]:
        if device["id"] == sp.device:
            spotify_device_id = device["id"]
            break

    if not spotify_device_id:
        print('No device with id "{}" known by Spotify'.format(sp.device))
        print("Known devices: {}".format(devices_available["devices"]))
        sys.exit(1)

    # Start playback
    client.start_playback(device_id=spotify_device_id, context_uri=uri)

print("")
print("")
print("Loading and checking readnfc")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("")
print("SCRIPT")
print("You are running version " + appsettings.appversion + "...")

print("")
print("NFC READER")
print("Connecting to NFC reader...")
try:
    reader = nfc.ContactlessFrontend('usb')
except IOError as e:
    print("... could not connect to reader")
    print("")
    print("You should check that the reader is working by running the following command at the command line:")
    print(">  python -m nfcpy")
    print("")
    print(
        "If this reports that the reader is in use by readnfc or otherwise crashes out then make sure that you don't already have readnfc running in the background via pm2. You can do this by running:")
    print(">  pm2 status             (this will show you whether it is running)")
    print(">  pm2 stop readnfc       (this will allow you to stop it so you can run the script manually)")
    print("")
    print("If you want to remove readnfc from running at startup then you can do it with:")
    print(">  pm2 delete readnfc")
    print(">  pm2 save")
    print(">  sudo reboot")
    print("")
    sys.exit()

print("... and connected to " + str(reader))

print("")
print("CHROMECAST")
chromecast_local = usersettings.chromecast
print("Chromecast set to " + chromecast_local)

print("")
print("OK, all ready! Present an NFC tag.")
print("")

while True:
    reader.connect(rdwr={'on-connect': touched, 'beep-on-connect': False})
    time.sleep(0.1);
