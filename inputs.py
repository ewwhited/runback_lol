def get_name(gameName = None, tagLine = None): #get the summoner's name
    while gameName == None and tagLine == None:
        try:
            gameName, tagLine= input("Enter your Summoner Name (e.g. Summoner#NA1): ").split('#') #input must be realistic
        except ValueError:
            print(f'Please enter a real summoner name split by a pound sign.')
            get_name()
        return gameName, tagLine


