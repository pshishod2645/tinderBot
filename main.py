from api import tinderAPI
ACCESS_TOKEN = "0c4a9280-8477-428e-88c1-0902b61872b5"

if __name__ == "__main__":
    api = tinderAPI(ACCESS_TOKEN)
    # api.whoLikesMe()
    api.autoSwipe()

    ## can access other api functions here. 
    ## like api.whoLikesMe() to find photos of people who like you 