import requests
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
        return "There were no results matching the query. Please try other keywords"
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
    }
    
    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    D = list(DATA['query']['pages'].values())
    introductionPart = D[0]['extract']
    ######## TextExtracts API #######
    
    return (introductionPart, theUrl)