def swipeLeft(person) : 
    ## Return true if you definitely don't want to swipe right the person.
    ## you can access (name, distance, birthdate, bio) as person.field
    ## refer person class for more 
    if(len(person.bio) == 0) : 
        return True
    return False