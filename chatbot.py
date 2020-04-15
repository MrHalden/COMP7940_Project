from __future__ import unicode_literals

import os
import sys
import redis
import requests

from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import (
    PostbackTemplateAction,MessageTemplateAction,URITemplateAction,CarouselTemplate,TemplateSendMessage,CarouselColumn, MessageAction,LocationAction, QuickReplyButton, QuickReply, MessageEvent, TextMessage, TextSendMessage, ImageMessage, VideoMessage, FileMessage, LocationMessage, StickerMessage, StickerSendMessage, LocationSendMessage
)
from linebot.utils import PY3
from geopy.distance import geodesic

######Another Service - Wikipedia######
def searchWiki(keyword):
    
    S = requests.Session()

    URL = "https://en.wikipedia.org/w/api.php"
    ######## Search API #######
    PARAMS = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": keyword 
    }

    R = S.get(url=URL, params=PARAMS)
    searchResult = R.json()
    isEmptyResult = (searchResult['query']['searchinfo']['totalhits'] == 0)
    if (isEmptyResult == True): # got empty search result
        return ("There were no results matching the query. Please try other keywords", "")
    titles = searchResult['query']['search'][0]['title']
    pageId = searchResult['query']['search'][0]['pageid']     # get page ID
    theUrl = "https://en.wikipedia.org/?curid=" + str(pageId) # construct the URL with page ID
    # using the first result (the most related one)
    ######## Search API #######

    ######## TextExtracts API #######
    PARAMS = {
        "action": "query",
        "prop": "extracts",
        "format": "json",
        "exintro": True,  # only the introduction part
        "titles": titles, # use the titles we got during the searching
        "explaintext": True,
        #exsentences": 1
        "exchars": 1200
    }
    
    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    D = list(DATA['query']['pages'].values())
    introductionPart = D[0]['extract']
    firstParagraph =introductionPart.split('\n')[0]
    ######## TextExtracts API #######
    
    return (firstParagraph, theUrl)
######Another Service - Wikipedia######

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
	
#### Using Redis Instead ####     

#store1 = Store(22.337998, 114.187433,20,2, "Lok Fu") 
#store2 = Store(22.319364, 114.169719,200,100, "Mong Kok")
#store3 = Store(22.341311, 114.194478,100,50, "Wong Tai Sin")
#storeList = []
#storeList.append(store1)
#storeList.append(store2)
#storeList.append(store3)

#### Using Redis Instead ####    

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
def findStoreByPrice(storeList):
    theStore = None
    minPrice = -1.0
    for s in storeList:
        if theStore is None:
            theStore = s
            minPrice = s.price
        else:
            if (int(s.price) < int(minPrice)):
                minPrice = s.price
                theStore = s
    return theStore
##################### ZHU Feng: END ######################
##################### Using Redis to Store Persistent Information######################
# My Redis Service:
HOST = os.getenv('REDIS_HOST', None)
PWD  = os.getenv('REDIS_PWD' , None)
PORT = os.getenv('REDIS_PORT', None)
r = redis.Redis(host = HOST, password = PWD, port = PORT)
r.flushall() # flush every time the service start

def saveToRedis_Store(lat, lon, price, limit, name):
    r.rpush("storeList", name)
    r.hset(name, "lat", lat)
    r.hset(name, "lon", lon)
    r.hset(name, "price", price)
    r.hset(name, "limit", limit)
    r.hset(name, "name", name)

def getFromRedis_Store():
    storeList = []
    storeList_redis = r.lrange("storeList", 0, -1)
    for store_redis in storeList_redis:
        tmpStore_redis = r.hgetall(store_redis.decode("utf-8"))
        #print(tmpStore_redis)
        tmpStore = Store(lat=tmpStore_redis[b'lat'].decode("utf-8"),lon=tmpStore_redis[b'lon'].decode("utf-8"), price=tmpStore_redis[b'price'].decode("utf-8"), limit=tmpStore_redis[b'limit'].decode("utf-8"), name=tmpStore_redis[b'name'].decode("utf-8"))
        storeList.append(tmpStore)
    #for store in storeList:
        #print(store.lat.decode("utf-8"))
    return storeList

saveToRedis_Store(22.337998, 114.187433,20,2, "Watsons (Lok Fu)")
saveToRedis_Store(22.319364, 114.169719,200,100, "Sasa (Mong Kok)")
saveToRedis_Store(22.341311, 114.194478,100,50, "Mannings (Wong Tai Sin)")

storeList = getFromRedis_Store()
r.set("sample", "This is sample content") # Sample code of saving string to Redis
r.hset(name = "infection", key = "shanghai", value = 153)
r.hset(name = "infection", key = "hubei", value = 244)
r.hset(name = "infection", key = "hongkong", value = 608)
r.hset(name = "infection", key = "beijing", value = 97)
r.hset(name = "infection", key = "guangdong", value = 92)
r.hset(name = "infection", key = "taiwan", value = 273)
r.set('tip1',"""How to wear mask correctly.
·The coloured side of the mask faces outwards, with the metallic strip uppermost.
·The strings or elastic bands are positioned properly to keep the mask firmly in place.
·The mask covers the nose, mouth and chin.
·The metallic strip moulds to the bridge of the nose.""")
r.set('tip2', """How to wash hands correctly.
·Wet your hands with clean, running water (warm or cold), turn off the tap, and apply soap....
·Lather your hands by rubbing them together with the soap. 
·Lather the backs of your hands, between your fingers, and under your nails.
·Scrub your hands for at least 20 seconds. Need a timer? Hum the “Happy Birthday” song from beginning to end twice.
·Rinse your hands well under clean, running water.Dry your hands using a clean towel or air dry them.""")
r.set('tip3',"May be staying at home is the best choice,although the situation in China is getting better and better.If you'd like to travel abroad(like US,France,etc),that's not a good idea.")
##################### Using Redis to Store Persistent Information######################
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
        if isinstance(event.message, LocationMessage):
            handle_LocationMessage(event) # ZHU Feng's part
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

    return 'OK'

# Handler function for Text Message

def handle_TextMessage(event):
    print(event.message.text)
#### Get If in Search Mode ####
    currentStatus = r.get(event.source.user_id+"search")
    #### IN Search Mode ####
    if currentStatus ==  b'1':
        if event.message.text.casefold() == "exit".casefold(): #### exit search mode
            r.set(event.source.user_id+"search", 0)
            msg = 'Successfully exit Search Mode. You could send "help" to learn how to use in the normal mode.' 
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(msg)
            )
            return
        ######Wikipedia#####
        searchResult = searchWiki(event.message.text)
        introText = ("From Wikipedia: \n" + searchResult[0])
        print(introText)
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(introText),
            TextSendMessage("For more information please visit " + searchResult[1])]
        )
        ######Wikipedia#####
    #### IN Search Mode ####
    #### Enter Search Mode ####
    if event.message.text.casefold() == "search mode".casefold():
        r.set(event.source.user_id+"search", 1)
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage('You are in Search Mode now. You could send any keywords to search. To exit Search Mode, please send "exit".')
        )   
    #### Enter Search Mode ####
    #### Exit Search Mode ####
    if event.message.text.casefold() == "exit".casefold():
        if currentStatus ==  b'1':
            r.set(event.source.user_id+"search", 0)
            msg = 'Successfully exit Search Mode. You could send "help" to learn how to use in the normal mode.'
        else:
            msg = 'You have already exited the Search Mode. You are in normal mode now. You could send "help" to learn how to use in the normal mode.'
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(msg)
        )   
    #### Exit Search Mode ####
    #### Help ####
    if event.message.text.casefold() == "help".casefold():
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage('You could send "coronavirus tips" to get some tips.\n\nYou could send some city name (e.g. HongKong, Beijing, Shanghai) to get the corresponding comfirmed coronavirus cases. You could also send "total" to get the total case number.\n\nYou could send "Find Mask" to find some face masks. You could also send "config" to choose find the nearest or the cheapest face mask.')
        )    
    #### Help ####
    #### Stateful ####
    if event.message.text.casefold() == "config/findMask/cheapest".casefold():
        r.set(event.source.user_id, "cheap") # rememeber every user's preference
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage( # quick reply for config
        text = 'OK, We will find the cheapest mask store for you',
        quick_reply = QuickReply(
            items = [
                QuickReplyButton(
                    action = MessageAction(label = "Find Mask NOW!", text = "Find Mask")
                )
            ]
        )))
    elif event.message.text.casefold() == "config/findMask/nearest".casefold():
        r.set(event.source.user_id, "nearby") # rememeber every user's preference
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage( # quick reply for config
        text = 'OK, We will find the nearest mask store for you',
        quick_reply = QuickReply(
            items = [
                QuickReplyButton(
                    action = MessageAction(label = "Find Mask NOW!", text = "Find Mask")
                )
            ]
        )))        
    #### Stateful ####
    QuickReply_text_message_config = TextSendMessage( # quick reply for config
        text = 'Here are the available configurations for finding masks',
        quick_reply = QuickReply(
            items = [
                QuickReplyButton(
                    action = MessageAction(label = "Cheap Mask First", text = "config/findMask/cheapest"),
                    image_url = "https://cdn1.iconfinder.com/data/icons/ios-11-glyphs/30/money_bag-512.png"
                ),
                QuickReplyButton(
                    action = MessageAction(label = "Nearby Mask First", text = "config/findMask/nearest"),
                    image_url = "https://lh3.googleusercontent.com/proxy/1a9k68551lJJFBDpXMENUSDxJC33VlTmir0Bj2LrZJ5QLOoHD6V8G-k3wpAfjdqN7oizSWerzL1nWwWbHKaYz3FCkOe5GpaV1OhRVJQQLrKHINKqMA"
                )
            ]
        )
    )

    if event.message.text.casefold() == "config".casefold() :# quick reply for config
        line_bot_api.reply_message(
        event.reply_token,
        QuickReply_text_message_config
        )
    ####ZHU Feng for quick reply location
    QuickReply_text_message = TextSendMessage(
        text = 'Please send your location so that we could help you find a neaby face mask store',
        quick_reply = QuickReply(
            items = [
                QuickReplyButton(
                    action = LocationAction(label = "Send Location"),
                )
            ]
        )
    )
    if event.message.text.casefold() == "Find Mask".casefold():
        line_bot_api.reply_message(
        event.reply_token,
        QuickReply_text_message
    )
    ####ZHU Feng for quick reply location
    ## Sample Code of getting string from Redis
    if event.message.text.casefold() == "sample".casefold():
        msg = r.get("sample").decode("utf-8")
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(msg)
        )
    ## WANG Yuhao ##

    print(event.message.text)
    if event.message.text=="coronavirus tips":
        message = TemplateSendMessage(
            alt_text='Carousel template',
            template=CarouselTemplate(
                columns=[
                    CarouselColumn(
                        thumbnail_image_url='https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcR5mlTGpxz5Ogie5g93siEvUcTy5dMxnOAJeiUwrTFSJtOEIi8u&usqp=CAU',
                        title='Measure 1',
                        text='Wear mask when go outside.',
                        actions=[
                            PostbackTemplateAction(
                                label='Some tips',
                                text='tip 1',
                                data='action=buy&itemid=1'
                            ),
#                             MessageTemplateAction(
#                                 label='message1',
#                                 text='message text1'
#                             ),
                            URITemplateAction(
                                label='More details',
                                uri='https://jingyan.baidu.com/article/f54ae2fc46c8061e93b84950.html'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcTruPXKu--ondWTUstQVMeqAc__4WMTB97rI6lSS-0gK2c7QPmE&usqp=CAU',
                        title='Measure 2',
                        text='Wash hands frequently.',
                        actions=[
                            PostbackTemplateAction(
                                label='Some tips',
                                text='tip 2',
                                data='action=buy&itemid=1'
                            ),
#                             MessageTemplateAction(
#                                 label='message1',
#                                 text='message text1'
#                             ),
                            URITemplateAction(
                                label='More details',
                                uri='https://jingyan.baidu.com/article/ff4116257cae5753e48237de.html'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcTIZzVtv-nGuPw-FebkzaIGI28s9PdBG3gTWtdDH5iHcK0mvvr5&usqp=CAU',
                        title='Measure 3',
                        text='Do not go to the crowed places.',
                        actions=[
                            PostbackTemplateAction(
                                label='Some tips',
                                text='tip 3',
                                data='action=buy&itemid=2'
                            ),
#                             MessageTemplateAction(
#                                 label='message2',
#                                 text='message text2'
#                             ),
                            URITemplateAction(
                                label='More details',
                                uri='https://voice.baidu.com/act/newpneumonia/newpneumonia/?from=osari_pc_3'
                            )
                        ]
                    )
                ]
            )
        )
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
#more buttons and images instead of only words,looks better

#         msg = """You ought to remember the following tips. 
#         1.Wearing mask when go outside.
#         2.Washing hands frequently.
#         3.Do not go to the crowed places.
#         If you want to know more details,just type in the serial number."""
#         line_bot_api.reply_message(
#             event.reply_token,
#             TextSendMessage(msg)
#         )
    elif event.message.text=="tip 1":
        msg=r.get('tip1').decode("utf-8")
###############using redis##################
#         msg = """How to wear mask correctly.
#         ·The coloured side of the mask faces outwards, with the metallic strip uppermost.
#         ·The strings or elastic bands are positioned properly to keep the mask firmly in place.
#         ·The mask covers the nose, mouth and chin.
#         ·The metallic strip moulds to the bridge of the nose."""
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(msg)
        )
    elif event.message.text=="tip 2":
        msg=r.get('tip2').decode("utf-8")
###############using redis##################
#         msg = """How to wash hands correctly.
#         ·Wet your hands with clean, running water (warm or cold), turn off the tap, and apply soap....
#         ·Lather your hands by rubbing them together with the soap. 
#         ·Lather the backs of your hands, between your fingers, and under your nails.
#         ·Scrub your hands for at least 20 seconds. Need a timer? Hum the “Happy Birthday” song from beginning to end twice.
#         ·Rinse your hands well under clean, running water.Dry your hands using a clean towel or air dry them."""
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(msg)
        )
    elif event.message.text=="tip 3":
        msg=r.get('tip3').decode("utf-8")
#############using redis##################
#         msg = "May be staying at home is the best choice,although the situation in China is getting better and better.If you'd like to travel abroad(like US,France,etc),that's not a good idea."
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(msg)
        )
#     else:
#         msg = "Sorry,I can't catch your point.You can type in 'measures to prevent new coronavirus' for some information about new coronavirus."
#         line_bot_api.reply_message(
#             event.reply_token,
#             TextSendMessage(msg)
#         )
    ## WANG Yuhao##
    
    ## ZHI Yiyao ##
       
    elif event.message.text.casefold() == "shanghai".casefold():
        msg = "current number: " + r.hget("infection", "shanghai").decode("utf-8")
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(msg)
        )

    elif event.message.text.casefold() == "hubei".casefold():
        msg = "current number: " + r.hget("infection", "hubei").decode("utf-8")
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(msg)
        )

    elif event.message.text.casefold() == "hongkong".casefold():
        msg = "current number: " + r.hget("infection", "hongkong").decode("utf-8")
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(msg)
        )

    elif event.message.text.casefold() == "guangdong".casefold():
        msg = "current number: " + r.hget("infection", "guangdong").decode("utf-8")
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(msg)
        )

    elif event.message.text.casefold() == "taiwan".casefold():
        msg = "current number: " + r.hget("infection", "taiwan").decode("utf-8")
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(msg)
        )    
    
    elif event.message.text.casefold() == "beijing".casefold():
        msg = "current number: " + r.hget("infection", "beijing").decode("utf-8")
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(msg)
        )    

    elif event.message.text.casefold() == "total".casefold():
        msg = "To view real-time situation please visit  " + "https://voice.baidu.com/act/newpneumonia/newpneumonia/?from=osari_pc_3"
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(msg)
        )          
    ## ZHI Yiyao ##   

    else:
        QuickReply_text_message_help = TextSendMessage( # quick reply for help
            text = 'Sorry, I cannot understand you. Send "help" to learn how to use this bot',
            quick_reply = QuickReply(
                items = [
                    QuickReplyButton(
                        action = MessageAction(label = "I need help NOW!", text = "help")
                    )
                ]
            )
        )
        line_bot_api.reply_message(
            event.reply_token,
            QuickReply_text_message_help
        )


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
    print(event.source.user_id)
    config = r.get(event.source.user_id)
    print(config)
    if (config == b'cheap'):
        theStore = findStoreByPrice(storeList)
        text_loc = "Here is the cheapest mask store:"
        print("find cheapest")
    else: # no config or nearby
        theStore = findStoreByDist(storeList, userLocation)
        text_loc = "Here is the closes mask store:"
        print("find nearest")
    line_bot_api.reply_message(
	event.reply_token,
    [TextSendMessage(text_loc),
	LocationSendMessage(title = theStore.name, address = 'Price: $' + str(theStore.price) + '/Piece\nUp to ' + str(theStore.limit) +' piece(s) each customer', latitude = theStore.lat, longitude = theStore.lon)
    ])

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(host='0.0.0.0', debug=options.debug, port=heroku_port)
