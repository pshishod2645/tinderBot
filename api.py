import requests
import json
from time import sleep
import datetime
from geopy.geocoders import Nominatim
from swipeLeft import swipeLeft
from PIL import Image
import urllib.request

TINDER_URL = "https://api.gotinder.com"
geolocator = Nominatim(user_agent="auto-tinder")
PROF_FILE = "./images/unclassified/profiles.txt"
ALL_PROFILES = './all_profiles.txt'
LIKED_PROFILES = './liked_profiles.txt'
DISLIKED_PROFILES = './disliked_profiles.txt'

liked_profiles_ptr = open(LIKED_PROFILES, 'a')
disliked_profiles_ptr = open(DISLIKED_PROFILES, 'a')
all_profiles_ptr = open(ALL_PROFILES, 'a+')
profiles_checked = {}

def saveProfile(file_ptr,  person) :
    global profiles_checked
    global all_profiles_ptr

    file_ptr.write(str(person) + '\n')
    all_profiles_ptr.write(person.id + '\n')
    profiles_checked[person.id] = True

def initalize() : 
    global all_profiles_ptr
    global profiles_checked

    all_profiles_ptr.seek(0)
    lines = all_profiles_ptr.readlines()
    for line in lines : 
        profiles_checked[line.replace('\n', '')] = True

def alreadyLiked(photoIdCheck, photoIds) :
    for photoId in photoIds : 
        if photoId in photoIdCheck : 
            return True
    return False

def appendToDict(mainDict, tempList) : 
    for photoId in tempList : 
        mainDict[photoId] = True

class tinderAPI():

    def __init__(self, token):
        self._token = token

    def profile(self):
        data = requests.get(TINDER_URL + "/v2/profile?include=account%2Cuser", headers={"X-Auth-Token": self._token}).json()
        return Profile(data["data"], self)

    def matches(self, limit=10):
        data = requests.get(TINDER_URL + f"/v2/matches?count={limit}", headers={"X-Auth-Token": self._token}).json()
        return list(map(lambda match: Person(match["person"], self), data["data"]["matches"]))

    def like(self, user_id):
        data = requests.get(TINDER_URL + f"/like/{user_id}", headers={"X-Auth-Token": self._token}).json()
        # return {
        #     "is_match": data["match"],
        #     "liked_remaining": data["likes_remaining"]
        # }
        return int(data["likes_remaining"])

    def dislike(self, user_id):
        requests.get(TINDER_URL + f"/pass/{user_id}", headers={"X-Auth-Token": self._token}).json()
        return True

    def recommendations(self):
        data = requests.get(TINDER_URL + "/v2/recs/core", headers={"X-Auth-Token": self._token}).json()
        # print(data)
        userList = []
        for entry in data['data']['results']: 
            if(entry['type'] == 'user') : 
                userList.append(entry['user'])

        return list(map(lambda user: Person(user, self), userList))

    def teaserPhotos(self) : 
        data = requests.get(TINDER_URL + f"/v2/fast-match/teasers", headers={"X-Auth-Token": self._token}).json()
        photos = list(map(lambda entry: entry['user']['photos'][0]['url'], data['data']['results']))
        ids = list(map(lambda entry : entry['user']['photos'][0]['id'], data['data']['results']))

        return {'photos' : photos, 'ids' : ids}

    def teaserCount(self) : 
        data = requests.get(TINDER_URL + f"/v2/fast-match/count", headers={"X-Auth-Token": self._token}).json()
        print(data)

    def whoLikesMe(self) : 
        photoUrls = self.teaserPhotos()['photos']
        print(json.dumps(photoUrls, indent = 4))
        for url in photoUrls : 
            image = Image.open(urllib.request.urlopen(url))
            image.show()
    def autoSwipe(self) : 
        initalize()

        photoIdCheck = {}
        TEASERS_ITER = 10
        for i in range(TEASERS_ITER) : 
            ids = self.teaserPhotos()['ids']
            appendToDict(photoIdCheck, ids)
            print(len(photoIdCheck))
            sleep(0.1)

        liked, disliked = 0, 1

        while True : 
            ids = self.teaserPhotos()['ids']
            appendToDict(photoIdCheck, ids)
            print(f'checkLen:  {len(photoIdCheck)}')


            persons = self.recommendations()

            for person in persons:
                if(alreadyLiked(photoIdCheck, person.images['ids'])) : 
                    remaining = person.like()
                    liked = liked + 1
                    print(f"matched {person}")
                    if(remaining == 0) : 
                        print(f"You're out of likes\n")
                        return

                elif (swipeLeft(person) or 7*disliked < 3*liked) : 
                    person.dislike()
                    disliked = disliked + 1
                    print(f"disliked {person}")

                else :  
                    remaining = person.like()
                    liked = liked + 1
                    print(f"liked {person}")
                    if(remaining == 0) : 
                        print(f"You're out of likes\n")
                        return
                sleep(0.01)

            print('numLiked, numDisliked : ', liked, disliked)
            sleep(0.5)


class Person(object):

    def __init__(self, data, api):
        self._api = api

        self.id = data["_id"]
        self.name = data.get("name", "Unknown")

        self.bio = data.get("bio", "")
        self.distance = data.get("distance_mi", 0) / 1.60934

        self.birth_date = datetime.datetime.strptime(data["birth_date"], '%Y-%m-%dT%H:%M:%S.%fZ') if data.get(
            "birth_date", False) else None
        self.gender = ["Male", "Female", "Unknown"][data.get("gender", 2)]

        self.images = {}
        self.images['photos'] = list(map(lambda photo: photo['url'], data.get("photos", [])))
        self.images['ids'] = list(map(lambda photo : photo['id'], data.get('photos', [])))

        # print(json.dumps(self.images, indent = 4))
        self.jobs = list(
            map(lambda job: {"title": job.get("title", {}).get("name"), "company": job.get("company", {}).get("name")}, data.get("jobs", [])))
        self.schools = list(map(lambda school: school["name"], data.get("schools", [])))

        if data.get("pos", False):
            self.location = geolocator.reverse(f'{data["pos"]["lat"]}, {data["pos"]["lon"]}')


    def __repr__(self):
        # schoolName = ""
        # if(len(self.schools) > 0) : 
        #     schoolName = self.schools[0]
        return f"{self.id}  -  {self.name}"


    def like(self):
        saveProfile(liked_profiles_ptr, self)
        return self._api.like(self.id)

    def dislike(self):
        saveProfile(disliked_profiles_ptr, self)
        return self._api.dislike(self.id)