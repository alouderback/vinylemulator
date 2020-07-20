import time
import nfc
import appsettings  # you shouldnt need to edit this file
import usersettings  # this is the file you might need to edit
import sys
import os


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

            os.system(castinstruction)


    else:
        print("")
        print(
            "NFC reader could not read tag. This can be because the reader didn't get a clear read of the card. If "
            "the issue persists then this is usually because (a) the tag is encoded (b) you are trying to use a "
            "mifare classic card, which is not supported or (c) you have tried to add data to the card which is not "
            "in text format. Please check the data on the card using NFC Tools on Windows or Mac.")
    return True


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
