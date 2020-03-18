from __future__ import unicode_literals

import os
import sys
import redis

from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, VideoMessage, FileMessage, LocationMessage, StickerMessage, StickerSendMessage, LocationSendMessage
)
from linebot.utils import PY3
from geopy.distance import geodesic

##################### ZHU Feng: START ######################
class Store:
    lat   = 0
    lon   = 0
    price = 0
    limit = 0
    name  = ""
    def __init__(self, lat, lon, price, limit, name):
        self.lat   = lat   # the latitude of the store
        self.lon   = lon   # the longitude of the store
        self.price = price # price per mask
        self.limit = limit # purchase limit (max number of masks a consumer could buy each time)
        self.name  = name  # name of the store
        
    def distInKm(self, userLocation): # calculate the distance between the store and the given location from user (in KM)
            return geodesic( (self.lat, self.lon), userLocation).km
            
store1 = Store(22.337998, 114.187433,20,2, "Lok Fu")
store2 = Store(22.319364, 114.169719,200,100, "Mong Kok")
store3 = Store(22.341311, 114.194478,100,50, "Wong Tai Sin")
storeList = []
storeList.append(store1)
storeList.append(store2)
storeList.append(store3)
def findStoreByDist(storeList, userLocation):
    theStore = None
    minDist  = -1.0
    for s in storeList:
        if theStore is None:
            theStore = s
            minDist  = s.distInKm(userLocation)
        else:
            if (s.distInKm(userLocation) < minDist):
                minDist  = s.distInKm(userLocation)
                theStore = s
    return theStore
##################### ZHU Feng: END ######################

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

# obtain the port that heroku assigned to this app.
heroku_port = os.getenv('PORT', None)

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if isinstance(event.message, TextMessage):
            handle_TextMessage(event)
        if isinstance(event.message, ImageMessage):
            handle_ImageMessage(event)
        if isinstance(event.message, VideoMessage):
            handle_VideoMessage(event)
        if isinstance(event.message, FileMessage):
            handle_FileMessage(event)
        if isinstance(event.message, StickerMessage):
            handle_StickerMessage(event)

        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

    return 'OK'

# Handler function for Text Message
## WANG Yuhao ##
    if event.message.text=="measures to prevent new coronavirus":
        msg = """You ought to remember the following tips. 
        1.Wearing mask when go outside.
        2.Washing hands frequently.
        3.Do not go to the crowed places.
        If you want to know more details,just type in the serial number."""
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(msg)
        )
    elif event.message.text=="1":
        msg = """How to wear mask correctly.
        ·The coloured side of the mask faces outwards, with the metallic strip uppermost.
        ·The strings or elastic bands are positioned properly to keep the mask firmly in place.
        ·The mask covers the nose, mouth and chin.
        ·The metallic strip moulds to the bridge of the nose."""
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(msg)
        )
    elif event.message.text=="2":
        msg = """How to wash hands correctly.
        ·Wet your hands with clean, running water (warm or cold), turn off the tap, and apply soap.
        ·Lather your hands by rubbing them together with the soap. 
        ·Lather the backs of your hands, between your fingers, and under your nails.
        ·Scrub your hands for at least 20 seconds. Need a timer? Hum the “Happy Birthday” song from beginning to end twice.
        ·Rinse your hands well under clean, running water.Dry your hands using a clean towel or air dry them."""
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(msg)
        )
    elif event.message.text=="3":
        msg = "May be staying at home is the best choice,although the situation in China is getting better and better.If you'd like to travel abroad(like US,France,etc),that's not a good idea."
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(msg)
        )
    else:
        msg = "Sorry,I can't catch your point.You can type in 'measures to prevent new coronavirus' for some information about new coronavirus."
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(msg)
        )
    ## WANG Yuhao##

# Handler function for Sticker Message
def handle_StickerMessage(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
    )

# Handler function for Image Message
def handle_ImageMessage(event):
    line_bot_api.reply_message(
	event.reply_token,
	TextSendMessage(text="Nice image!")
    )

# Handler function for Video Message
def handle_VideoMessage(event):
    line_bot_api.reply_message(
	event.reply_token,
	TextSendMessage(text="Nice video!")
    )

# Handler function for File Message
def handle_FileMessage(event):
    line_bot_api.reply_message(
	event.reply_token,
	TextSendMessage(text="Nice file!")
    )

# Handler function for Location Message (ZHU Feng)
def handle_LocationMessage(event):
    userLocation = (event.message.latitude, event.message.longitude)
    theStore = findStoreByDist(storeList, userLocation)
    line_bot_api.reply_message(
	event.reply_token,
	LocationSendMessage(title = theStore.name, address = 'Price: $' + str(theStore.price) + '/Piece\nUp to ' + str(theStore.limit) +' piece(s) each customer', latitude = theStore.lat, longitude = theStore.lon)
    )

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(host='0.0.0.0', debug=options.debug, port=heroku_port)
